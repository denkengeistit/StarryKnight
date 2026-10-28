#!/usr/bin/env python3
"""LEGACY: for isometric maps use tools/iso_to_starryknight.py instead.

Convert a Tiled TMX map to the StarryKnight Lua map format.

Mapping model (matches the game's multi-plane depth system):
  - Each TMX *tile layer* becomes one depth slice, in TMX document order
    (first layer = farthest from camera, last = closest).
  - Each TMX *object group* attaches entities to a slice. The group is matched
    to a tile layer by name: an objectgroup named "foo_objects" (or exactly
    "foo") attaches to the tile layer named "foo". Alternatively any object or
    objectgroup may carry a custom property `slice` (1-based index).
  - An object with class/type "spawn" sets that slice's player spawn point and
    makes that slice the map's spawn_index.

Entity classes recognized (Tiled object class/type, case-insensitive):
  spawn, skeleton/enemy, heal/potion, xp/coin

Engine constraints enforced here so bad maps fail at convert time, not in-game
(see src/map.lua and src/layer.lua):
  - 2 to 5 tile layers (legacy limit; the engine itself no longer caps layers)
  - every slice must have non-empty tile data
  - tilesize should be 32 (the physics tuning assumes it); other sizes warn
"""
import xml.etree.ElementTree as ET
import sys
import os
import argparse

MIN_LAYERS = 2
MAX_LAYERS = 5
EXPECTED_TILESIZE = 32


def fail(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print(f"Warning: {msg}", file=sys.stderr)


def get_properties(el):
    """Read a Tiled <properties> block into a dict."""
    props = {}
    props_el = el.find('properties')
    if props_el is not None:
        for p in props_el.findall('property'):
            props[p.get('name')] = p.get('value')
    return props


def layer_to_tile_string(layer_el):
    """Convert one TMX tile layer to the '#'/'.' multi-line string format."""
    width = int(layer_el.get('width', 0))
    height = int(layer_el.get('height', 0))
    data_el = layer_el.find('data')
    if data_el is None or not (data_el.text or '').strip():
        return None

    encoding = data_el.get('encoding')
    if encoding == 'csv':
        raw = data_el.text.strip().replace('\n', ',').split(',')
        raw = [v for v in raw if v.strip() != '']
    elif encoding is None:
        # XML tile elements
        raw = [t.get('gid', '0') for t in data_el.findall('tile')]
    else:
        fail(f"Layer '{layer_el.get('name')}' uses encoding '{encoding}'. "
             "Re-save the map with tile layer format CSV "
             "(Map > Map Properties > Tile Layer Format).")

    if len(raw) != width * height:
        fail(f"Layer '{layer_el.get('name')}': expected {width * height} "
             f"tiles, found {len(raw)}.")

    rows = []
    for y in range(height):
        row = ''.join(
            '#' if int(raw[y * width + x]) > 0 else '.'
            for x in range(width)
        )
        rows.append(row)
    return '\n'.join(rows)


def classify_object(obj):
    """Map a Tiled object class/type/name to a game entity type."""
    label = (obj.get('class') or obj.get('type') or obj.get('name') or '').lower()
    if 'spawn' in label or 'player' in label:
        return 'spawn'
    if 'heal' in label or 'potion' in label:
        return 'heal'
    if 'xp' in label or 'coin' in label:
        return 'xp'
    if 'skeleton' in label or 'enemy' in label:
        return 'skeleton'
    return None


def match_group_to_slice(group_el, slice_names):
    """Resolve which slice an objectgroup belongs to. Returns 0-based index or None."""
    props = get_properties(group_el)
    if 'slice' in props:
        idx = int(props['slice']) - 1
        if not (0 <= idx < len(slice_names)):
            fail(f"Objectgroup '{group_el.get('name')}' has slice={props['slice']} "
                 f"but the map has {len(slice_names)} tile layers.")
        return idx

    name = (group_el.get('name') or '').lower()
    for i, sname in enumerate(slice_names):
        s = sname.lower()
        if name == s or name == s + '_objects' or name == s + '_obj':
            return i
    return None


def parse_color(value):
    """Parse 'r,g,b' (0-1 floats) or '#rrggbb' / '#aarrggbb' into [r, g, b]."""
    if not value:
        return None
    value = value.strip()
    if value.startswith('#'):
        h = value.lstrip('#')
        if len(h) == 8:  # Tiled emits #AARRGGBB
            h = h[2:]
        return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]
    parts = [float(p) for p in value.split(',')]
    if len(parts) != 3:
        fail(f"Bad tile_color property: '{value}'")
    return parts


def parse_tmx(tmx_path):
    tree = ET.parse(tmx_path)
    root = tree.getroot()

    tile_w = int(root.get('tilewidth', 32))
    tile_h = int(root.get('tileheight', 32))
    if tile_w != tile_h:
        fail(f"Non-square tiles ({tile_w}x{tile_h}) are not supported.")
    if tile_w != EXPECTED_TILESIZE:
        warn(f"tilesize is {tile_w}, but the game's physics/jump tuning assumes "
             f"{EXPECTED_TILESIZE}px tiles. The map will load but may play badly.")

    # --- Tile layers -> depth slices (document order: first = farthest) ---
    tile_layers = root.findall('layer')
    if not (MIN_LAYERS <= len(tile_layers) <= MAX_LAYERS):
        fail(f"Map has {len(tile_layers)} tile layers; the engine requires "
             f"{MIN_LAYERS}-{MAX_LAYERS} (one per depth slice, first = farthest "
             "from camera).")

    slices = []
    for el in tile_layers:
        name = el.get('name') or f"slice_{len(slices) + 1}"
        tiles = layer_to_tile_string(el)
        if tiles is None or '#' not in tiles:
            fail(f"Tile layer '{name}' has no solid tiles. Every depth slice "
                 "needs terrain; delete the layer or paint it.")
        props = get_properties(el)
        slices.append({
            'name': name,
            'tiles': tiles,
            'tile_color': parse_color(props.get('tile_color')) or [0.5, 0.5, 0.5],
            'spawn': None,
            'entities': [],
        })

    # --- Object groups -> entities + spawn ---
    slice_names = [s['name'] for s in slices]
    spawn_index = None
    for group_el in root.findall('objectgroup'):
        group_idx = match_group_to_slice(group_el, slice_names)
        for obj in group_el.findall('object'):
            obj_props = get_properties(obj)
            if 'slice' in obj_props:
                idx = int(obj_props['slice']) - 1
                if not (0 <= idx < len(slices)):
                    fail(f"Object at ({obj.get('x')},{obj.get('y')}) has "
                         f"slice={obj_props['slice']}; map has {len(slices)} slices.")
            elif group_idx is not None:
                idx = group_idx
            else:
                fail(f"Objectgroup '{group_el.get('name')}' doesn't match any tile "
                     "layer name. Name it '<tilelayer>_objects', or set a 'slice' "
                     "custom property (1-based) on the group or its objects.")

            kind = classify_object(obj)
            if kind is None:
                warn(f"Skipping object '{obj.get('name')}' (class "
                     f"'{obj.get('class') or obj.get('type')}') -- not one of: "
                     "spawn, skeleton/enemy, heal/potion, xp/coin.")
                continue

            x = float(obj.get('x', 0))
            y = float(obj.get('y', 0))
            if kind == 'spawn':
                if spawn_index is not None:
                    fail("Multiple spawn objects found; a map needs exactly one.")
                slices[idx]['spawn'] = {'x': x, 'y': y}
                spawn_index = idx + 1
            else:
                ent = {'type': kind, 'x': x, 'y': y}
                if kind == 'skeleton':
                    ent['lvl'] = int(obj_props.get('lvl', 1))
                slices[idx]['entities'].append(ent)

    if spawn_index is None:
        fail("No spawn object found. Add an object with class 'spawn' to an "
             "object layer (otherwise the player drops at a default point that "
             "may be inside terrain).")

    return {
        'tilesize': tile_w,
        'spawn_index': spawn_index,
        'layers': slices,
    }


def num(v):
    """Format numbers without trailing .0 noise."""
    return str(int(v)) if float(v) == int(v) else str(v)


def write_lua(map_data, output_path, source_name):
    lines = []
    lines.append(f"-- Generated by tools/tmx_to_starryknight.py from {source_name}.")
    lines.append("-- Do not hand-edit; re-export from Tiled and re-run the converter.")
    lines.append("return {")
    lines.append(f"  tilesize = {map_data['tilesize']},")
    lines.append(f"  spawn_index = {map_data['spawn_index']},")
    lines.append("  layers = {")
    for layer in map_data['layers']:
        lines.append("    {")
        lines.append(f'      name       = "{layer["name"]}",')
        lines.append("      tiles      = [[")
        lines.append(layer['tiles'])
        lines.append("]],")
        c = layer['tile_color']
        lines.append(f"      tile_color = {{ {c[0]}, {c[1]}, {c[2]} }},")
        if layer['spawn']:
            s = layer['spawn']
            lines.append(f"      spawn      = {{ x = {num(s['x'])}, y = {num(s['y'])} }},")
        lines.append("      entities = {")
        for ent in layer['entities']:
            fields = [f'type = "{ent["type"]}"', f"x = {num(ent['x'])}", f"y = {num(ent['y'])}"]
            if 'lvl' in ent:
                fields.append(f"lvl = {ent['lvl']}")
            lines.append("        { " + ", ".join(fields) + " },")
        lines.append("      },")
        lines.append("    },")
    lines.append("  },")
    lines.append("}")
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Tiled TMX map to a StarryKnight Lua map. "
                    "Each TMX tile layer becomes one depth slice "
                    "(first layer = farthest from camera).")
    parser.add_argument("input", help="Input .tmx file")
    parser.add_argument("output", help="Output .lua file (put it in assets/maps/)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        fail(f"Input file {args.input} not found.")

    map_data = parse_tmx(args.input)
    write_lua(map_data, args.output, os.path.basename(args.input))

    n = len(map_data['layers'])
    print(f"Wrote {args.output}: {n} slices, spawn on slice {map_data['spawn_index']}.")
    module = os.path.splitext(args.output)[0].replace('/', '.').replace(os.sep, '.')
    print("Remember to register it in the MAPS table in src/play.lua, e.g.:")
    print(f'  ["2"] = "{module}",')


if __name__ == "__main__":
    main()
