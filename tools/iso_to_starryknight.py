#!/usr/bin/env python3
"""Convert an isometric Tiled map (TMX) into StarryKnight side-scroller strips.

See docs/design/iso-strip-maps.md for the model. In short: the iso map is cut
into strips of `strip_width` tile columns (constant tile x), running along the
bottom-left -> top-right diagonal. Strip 1 (top-left of the screen) is the
farthest layer, strip N (bottom-right) the nearest. Scrolling runs along the
strip, and the middle strip is the spawn layer.

Authoring convention:
  - Map property `strip_width` (int, default 2); must divide the map width.
  - Tile layers carry an int property `elevation` (default 0, ground). A
    non-empty tile on a layer at elevation e is a solid block in height slot e.
  - Object layers: class/type spawn, skeleton/enemy, heal/potion, xp/coin.
    Objects use Tiled's iso object coordinates (x/tileheight, y/tileheight
    are tile coordinates). They land on the strip containing their tile x,
    standing on the highest solid block of that column.
"""
import argparse
import math
import os
import sys
import xml.etree.ElementTree as ET

from tmx_to_starryknight import fail, warn, get_properties, num

TS = 32            # engine tile size
SKY = 8            # empty rows above the highest elevation slot
DEFAULT_STRIP_WIDTH = 2
GID_MASK = 0x0FFFFFFF
FAR_COLOR = (0.25, 0.28, 0.45)
NEAR_COLOR = (0.65, 0.58, 0.48)

ENTITY_CLASSES = {
    'skeleton': 'skeleton', 'enemy': 'skeleton',
    'heal': 'heal', 'potion': 'heal',
    'xp': 'xp', 'coin': 'xp',
}


def read_gids(layer_el, w, h):
    data = layer_el.find('data')
    name = layer_el.get('name')
    if data is None or data.get('encoding') != 'csv':
        fail(f"Layer '{name}': save tile layer format as CSV.")
    raw = [v for v in data.text.replace('\n', ',').split(',') if v.strip()]
    if len(raw) != w * h:
        fail(f"Layer '{name}': expected {w * h} tiles, found {len(raw)}.")
    return [int(v) & GID_MASK for v in raw]


def parse(path, strip_width_override):
    root = ET.parse(path).getroot()
    if root.get('orientation') != 'isometric':
        fail(f"{path}: orientation is '{root.get('orientation')}', "
             "expected 'isometric'.")
    w, h = int(root.get('width')), int(root.get('height'))
    th = int(root.get('tileheight'))
    props = get_properties(root)
    sw = strip_width_override or int(props.get('strip_width', DEFAULT_STRIP_WIDTH))
    if sw < 1 or w % sw:
        fail(f"strip_width {sw} must be >= 1 and divide map width {w}.")
    n = w // sw
    if n < 2:
        fail(f"Map yields {n} strip(s); need at least 2 (lower strip_width).")

    # solid[(x, y)] = set of elevations
    solid = {}
    max_e = 0
    for layer in root.findall('layer'):
        e = int(get_properties(layer).get('elevation', 0))
        if e < 0:
            fail(f"Layer '{layer.get('name')}': negative elevation.")
        gids = read_gids(layer, w, h)
        for i, g in enumerate(gids):
            if g:
                solid.setdefault((i % w, i // w), set()).add(e)
                max_e = max(max_e, e)

    rows = SKY + max_e + 1
    cols = h  # side-scroll column c <-> iso tile y = h-1-c (bottom-left first)

    def row_of(e):
        return SKY + max_e - e

    strips = []
    for s in range(n):
        grid = [['.'] * cols for _ in range(rows)]
        top = [None] * cols  # highest solid elevation per column
        for x in range(s * sw, (s + 1) * sw):
            for y in range(h):
                c = h - 1 - y
                for e in solid.get((x, y), ()):
                    grid[row_of(e)][c] = '#'
                    if top[c] is None or e > top[c]:
                        top[c] = e
        if not any(t is not None for t in top):
            warn(f"strip {s + 1} has no solid tiles.")
        strips.append({'grid': grid, 'top': top, 'entities': []})

    spawn_col = None
    for og in root.findall('objectgroup'):
        for obj in og.findall('object'):
            cls = (obj.get('class') or obj.get('type') or '').lower()
            tx = float(obj.get('x', 0)) / th
            ty = float(obj.get('y', 0)) / th
            if not (0 <= tx < w and 0 <= ty <= h):
                warn(f"object '{cls}' at tile ({tx:.1f},{ty:.1f}) is off the map; skipped.")
                continue
            col = (h - ty) * TS  # px along the strip
            c = min(cols - 1, int(col // TS))
            if cls == 'spawn':
                spawn_col = c
                continue
            if cls not in ENTITY_CLASSES:
                warn(f"unknown object class '{cls}'; skipped.")
                continue
            st = strips[int(tx) // sw]
            t = st['top'][c]
            if t is None:
                warn(f"{cls} over a pit in strip {int(tx) // sw + 1}; skipped.")
                continue
            kind = ENTITY_CLASSES[cls]
            ent = {'type': kind, 'x': c * TS, 'y': (row_of(t) - 1) * TS}
            if kind == 'skeleton':
                ent['lvl'] = int(get_properties(obj).get('lvl', 1))
            else:
                ent['x'] += 8
                ent['y'] += 8
            st['entities'].append(ent)
    if spawn_col is None:
        warn("no spawn object; spawning at column 2.")
        spawn_col = 2

    for s, st in enumerate(strips):
        t = s / (n - 1)
        st['name'] = f"s{s + 1}"
        st['color'] = [round(a + (b - a) * t, 3) for a, b in zip(FAR_COLOR, NEAR_COLOR)]
        # nearest column to the spawn column that has floor
        cands = [c for c in range(cols) if st['top'][c] is not None]
        if cands:
            c = min(cands, key=lambda k: abs(k - spawn_col))
            st['spawn'] = {'x': c * TS, 'y': (row_of(st['top'][c]) - 1) * TS}
        else:
            st['spawn'] = {'x': spawn_col * TS, 'y': 0}
        st['tiles'] = '\n'.join(''.join(r) for r in st['grid'])
    return {'strips': strips, 'spawn_index': math.ceil(n / 2), 'sw': sw}


def write_lua(m, out, source):
    L = [f"-- Generated by tools/iso_to_starryknight.py from {source}.",
         "-- Do not hand-edit; edit the iso TMX and re-run the converter.",
         "return {", f"  tilesize = {TS},", f"  spawn_index = {m['spawn_index']},",
         "  layers = {"]
    for st in m['strips']:
        c = st['color']
        L += ["    {", f'      name       = "{st["name"]}",', "      tiles      = [[",
              st['tiles'], "]],",
              f"      tile_color = {{ {c[0]}, {c[1]}, {c[2]} }},",
              f"      spawn      = {{ x = {num(st['spawn']['x'])}, y = {num(st['spawn']['y'])} }},",
              "      entities = {"]
        for e in st['entities']:
            f = [f'type = "{e["type"]}"', f"x = {num(e['x'])}", f"y = {num(e['y'])}"]
            if 'lvl' in e:
                f.append(f"lvl = {e['lvl']}")
            L.append("        { " + ", ".join(f) + " },")
        L += ["      },", "    },"]
    L += ["  },", "}"]
    with open(out, 'w') as fh:
        fh.write('\n'.join(L) + '\n')


def main():
    ap = argparse.ArgumentParser(
        description="Slice an isometric Tiled map into StarryKnight "
                    "side-scroller strips (far = top-left, near = bottom-right).")
    ap.add_argument("input", help="Input isometric .tmx file")
    ap.add_argument("output", help="Output .lua file (put it in assets/maps/)")
    ap.add_argument("--strip-width", type=int, default=None,
                    help="tile columns per strip (overrides map property "
                         f"strip_width; default {DEFAULT_STRIP_WIDTH})")
    a = ap.parse_args()
    if not os.path.exists(a.input):
        fail(f"Input file {a.input} not found.")
    m = parse(a.input, a.strip_width)
    write_lua(m, a.output, os.path.basename(a.input))
    print(f"Wrote {a.output}: {len(m['strips'])} strips (width {m['sw']}), "
          f"spawn on strip {m['spawn_index']}.")


if __name__ == "__main__":
    main()
