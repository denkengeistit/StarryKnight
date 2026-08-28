#!/usr/bin/env python3
"""Generate stress-test TMX maps for the StarryKnight converter."""
import xml.etree.ElementTree as ET
import os

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

def make_map(width, height, tilewidth=32, tileheight=32, orientation="orthogonal"):
    """Create a base TMX map element."""
    map_el = ET.Element('map', {
        'version': '1.10',
        'orientation': orientation,
        'renderorder': 'right-down',
        'width': str(width),
        'height': str(height),
        'tilewidth': str(tilewidth),
        'tileheight': str(tileheight),
        'infinite': '0',
    })
    ts = ET.SubElement(map_el, 'tileset', {
        'firstgid': '1',
        'name': 'tiles',
        'tilewidth': str(tilewidth),
        'tileheight': str(tileheight),
        'tilecount': '1',
        'columns': '1',
    })
    ET.SubElement(ts, 'tile', {'id': '0'})
    return map_el

def make_csv_data(width, height, pattern='solid'):
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            if pattern == 'solid':
                row.append('1')
            elif pattern == 'platforms':
                if y >= height - 2:
                    row.append('1')
                elif y == height // 2 and 3 <= x <= width - 4:
                    row.append('1')
                else:
                    row.append('0')
            elif pattern == 'checker':
                row.append('1' if (x + y) % 2 == 0 else '0')
            elif pattern == 'border':
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    row.append('1')
                else:
                    row.append('0')
        rows.append(','.join(row))
    return '\n'.join(rows) + '\n'

def add_tile_layer(map_el, name, width, height, csv_data, encoding='csv', tile_color=None, color_format='float'):
    layer = ET.SubElement(map_el, 'layer', {
        'id': str(len(map_el.findall('layer')) + 1),
        'name': name,
        'width': str(width),
        'height': str(height),
    })
    data = ET.SubElement(layer, 'data', {'encoding': encoding})
    data.text = '\n' + csv_data
    if tile_color:
        props = ET.SubElement(layer, 'properties')
        ET.SubElement(props, 'property', {'name': 'tile_color', 'value': tile_color})
    return layer

def add_xml_tile_layer(map_el, name, width, height, pattern='solid', tile_color=None):
    layer = ET.SubElement(map_el, 'layer', {
        'id': str(len(map_el.findall('layer')) + 1),
        'name': name,
        'width': str(width),
        'height': str(height),
    })
    data = ET.SubElement(layer, 'data')
    for y in range(height):
        for x in range(width):
            gid = '1'
            if pattern == 'platforms':
                if y < height - 2 and not (y == height // 2 and 3 <= x <= width - 4):
                    gid = '0'
            tile = ET.SubElement(data, 'tile', {'gid': gid})
    if tile_color:
        props = ET.SubElement(layer, 'properties')
        ET.SubElement(props, 'property', {'name': 'tile_color', 'value': tile_color})
    return layer

def add_object_group(map_el, name, objects, slice_prop=None):
    group = ET.SubElement(map_el, 'objectgroup', {
        'id': str(len(map_el.findall('objectgroup')) + 1),
        'name': name,
    })
    if slice_prop is not None:
        props = ET.SubElement(group, 'properties')
        ET.SubElement(props, 'property', {'name': 'slice', 'value': str(slice_prop)})
    for obj in objects:
        obj_attrs = {
            'id': str(obj.get('id', 1)),
            'x': str(obj['x']),
            'y': str(obj['y']),
        }
        if obj.get('class'):
            obj_attrs['class'] = obj['class']
        if obj.get('type'):
            obj_attrs['type'] = obj['type']
        obj_el = ET.SubElement(group, 'object', obj_attrs)
        if obj.get('props'):
            props = ET.SubElement(obj_el, 'properties')
            for pname, pval in obj['props'].items():
                ET.SubElement(props, 'property', {'name': pname, 'value': str(pval)})
    return group

def write_tmx(map_el, filename):
    ET.indent(map_el, space=' ')
    tree = ET.ElementTree(map_el)
    path = os.path.join(TOOLS_DIR, filename)
    tree.write(path, encoding='UTF-8', xml_declaration=True)
    print(f"  Wrote {filename}")
    return path

W, H = 10, 8

print("Creating stress test maps...")

# 1. Two-layer minimal map with spawn
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'platforms'), tile_color="0.2,0.3,0.4")
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'platforms'), tile_color="0.5,0.6,0.7")
add_object_group(m, "front_objects", [{'id': 1, 'class': 'spawn', 'x': 64, 'y': 128}])
write_tmx(m, "stress_two_layer.tmx")

# 2. Three-layer map with spawn + skeleton + heal + xp
m = make_map(W, H)
add_tile_layer(m, "background", W, H, make_csv_data(W, H, 'platforms'), tile_color="0.15,0.1,0.2")
add_tile_layer(m, "midground", W, H, make_csv_data(W, H, 'solid'), tile_color="0.4,0.35,0.5")
add_tile_layer(m, "foreground", W, H, make_csv_data(W, H, 'platforms'), tile_color="0.6,0.5,0.4")
add_object_group(m, "midground_objects", [
    {'id': 1, 'class': 'spawn', 'x': 64, 'y': 192},
    {'id': 2, 'class': 'skeleton', 'x': 256, 'y': 192, 'props': {'lvl': 3}},
])
add_object_group(m, "foreground_objects", [
    {'id': 3, 'class': 'heal', 'x': 128, 'y': 192},
    {'id': 4, 'class': 'xp', 'x': 192, 'y': 192},
])
write_tmx(m, "stress_three_layer.tmx")

# 3. Five-layer map (maximum layers)
m = make_map(W, H)
for name, color in [("far","0.1,0.1,0.15"),("far2","0.2,0.15,0.25"),("mid","0.35,0.3,0.4"),("near2","0.5,0.45,0.55"),("near","0.7,0.65,0.75")]:
    add_tile_layer(m, name, W, H, make_csv_data(W, H, 'solid'), tile_color=color)
add_object_group(m, "mid_objects", [
    {'id': 1, 'class': 'spawn', 'x': 32, 'y': 128},
    {'id': 2, 'class': 'enemy', 'x': 160, 'y': 128},
    {'id': 3, 'class': 'coin', 'x': 96, 'y': 128},
])
write_tmx(m, "stress_five_layer.tmx")

# 4. XML tile format (no encoding attribute)
m = make_map(W, H)
add_xml_tile_layer(m, "layer1", W, H, 'platforms', tile_color="0.3,0.3,0.3")
add_xml_tile_layer(m, "layer2", W, H, 'platforms', tile_color="0.6,0.6,0.6")
add_object_group(m, "layer2_objects", [{'id': 1, 'class': 'spawn', 'x': 64, 'y': 128}])
write_tmx(m, "stress_xml_format.tmx")

# 5. Hex color tile_color
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'), tile_color="#336699")
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'), tile_color="#AABBCCDD")
add_object_group(m, "front_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 96}])
write_tmx(m, "stress_hexcolor.tmx")

# 6. Per-object slice property
m = make_map(W, H)
add_tile_layer(m, "layer1", W, H, make_csv_data(W, H, 'solid'), tile_color="0.2,0.2,0.2")
add_tile_layer(m, "layer2", W, H, make_csv_data(W, H, 'solid'), tile_color="0.5,0.5,0.5")
add_object_group(m, "misc_objects", [
    {'id': 1, 'class': 'spawn', 'x': 32, 'y': 96, 'props': {'slice': 1}},
    {'id': 2, 'class': 'skeleton', 'x': 160, 'y': 96, 'props': {'slice': 2, 'lvl': 2}},
])
write_tmx(m, "stress_slice_prop.tmx")

# 7. Group-level slice property
m = make_map(W, H)
add_tile_layer(m, "slice_a", W, H, make_csv_data(W, H, 'solid'), tile_color="0.2,0.2,0.3")
add_tile_layer(m, "slice_b", W, H, make_csv_data(W, H, 'solid'), tile_color="0.4,0.4,0.5")
add_object_group(m, "entities", [
    {'id': 1, 'class': 'spawn', 'x': 32, 'y': 96},
    {'id': 2, 'class': 'potion', 'x': 128, 'y': 96},
], slice_prop=2)
write_tmx(m, "stress_group_slice.tmx")

# 8. Five-layer with mixed matching
m = make_map(W, H)
for name, color in [("L1","0.1,0.1,0.2"),("L2","0.25,0.2,0.35"),("L3","0.4,0.35,0.45"),("L4","0.55,0.5,0.55"),("L5","0.7,0.65,0.65")]:
    add_tile_layer(m, name, W, H, make_csv_data(W, H, 'solid'), tile_color=color)
add_object_group(m, "L2_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 128}])
add_object_group(m, "L4_objects", [
    {'id': 2, 'class': 'skeleton', 'x': 160, 'y': 128, 'props': {'lvl': 5}},
    {'id': 3, 'class': 'enemy', 'x': 224, 'y': 128},
])
add_object_group(m, "misc", [{'id': 4, 'class': 'xp', 'x': 96, 'y': 128, 'props': {'slice': 5}}])
write_tmx(m, "stress_mixed_matching.tmx")

# 9. Base64 encoding (should fail)
m = make_map(W, H)
l1 = ET.SubElement(m, 'layer', {'id': '1', 'name': 'back', 'width': str(W), 'height': str(H)})
d1 = ET.SubElement(l1, 'data', {'encoding': 'base64'})
d1.text = '\neJztwQEBAAAAgJD+r+5QEdVoVQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABVQw==\n'
l2 = ET.SubElement(m, 'layer', {'id': '2', 'name': 'front', 'width': str(W), 'height': str(H)})
d2 = ET.SubElement(l2, 'data', {'encoding': 'base64'})
d2.text = '\neJztwQEBAAAAgJD+r+5QEdVoVQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABVQw==\n'
add_object_group(m, "front_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_base64.tmx")

# 10. One layer only
m = make_map(W, H)
add_tile_layer(m, "only", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "only_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_one_layer.tmx")

# 11. Six layers
m = make_map(W, H)
for i in range(6):
    add_tile_layer(m, f"layer{i+1}", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "layer1_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_six_layers.tmx")

# 12. No spawn object
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "front_objects", [{'id': 1, 'class': 'skeleton', 'x': 32, 'y': 64}])
write_tmx(m, "stress_no_spawn.tmx")

# 13. Multiple spawn objects
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "back_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
add_object_group(m, "front_objects", [{'id': 2, 'class': 'spawn', 'x': 128, 'y': 64}])
write_tmx(m, "stress_multi_spawn.tmx")

# 14. Empty tile layer (all zeros)
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
l2 = ET.SubElement(m, 'layer', {'id': '2', 'name': 'empty', 'width': str(W), 'height': str(H)})
d2 = ET.SubElement(l2, 'data', {'encoding': 'csv'})
d2.text = '\n' + ','.join(['0'] * (W * H)) + '\n'
add_object_group(m, "back_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_empty_layer.tmx")

# 15. Unmatched objectgroup
m = make_map(W, H)
add_tile_layer(m, "layer1", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "layer2", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "wrong_name_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_unmatched_group.tmx")

# 16. Small tiles (should warn but succeed)
m = make_map(W, H, tilewidth=16, tileheight=16)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "front_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_small_tiles.tmx")

# 17. Non-orthogonal (staggered) orientation
m = make_map(W, H, orientation="staggered")
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "front_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_staggered.tmx")

# 18. Unknown object classes (should warn + skip)
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "front_objects", [
    {'id': 1, 'class': 'spawn', 'x': 32, 'y': 64},
    {'id': 2, 'class': 'treasure_chest', 'x': 128, 'y': 64},
    {'id': 3, 'class': 'npc', 'x': 192, 'y': 64},
])
write_tmx(m, "stress_unknown_classes.tmx")

# 19. Per-object slice in same group targeting different slices
m = make_map(W, H)
add_tile_layer(m, "a", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "b", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "mixed", [
    {'id': 1, 'class': 'spawn', 'x': 32, 'y': 64, 'props': {'slice': 1}},
    {'id': 2, 'class': 'skeleton', 'x': 160, 'y': 64, 'props': {'slice': 2}},
    {'id': 3, 'class': 'heal', 'x': 96, 'y': 64, 'props': {'slice': 2}},
])
write_tmx(m, "stress_per_obj_slice_mixed.tmx")

# 20. zlib compressed (should fail)
m = make_map(W, H)
l1 = ET.SubElement(m, 'layer', {'id': '1', 'name': 'back', 'width': str(W), 'height': str(H)})
d1 = ET.SubElement(l1, 'data', {'encoding': 'base64', 'compression': 'zlib'})
d1.text = '\neJxrYK4BaQEKAAArAQ4=\n'
l2 = ET.SubElement(m, 'layer', {'id': '2', 'name': 'front', 'width': str(W), 'height': str(H)})
d2 = ET.SubElement(l2, 'data', {'encoding': 'base64', 'compression': 'zlib'})
d2.text = '\neJxrYK4BaQEKAAArAQ4=\n'
add_object_group(m, "front_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_zlib.tmx")

# 21. Tile count mismatch (data has wrong number of tiles)
m = make_map(W, H)
l1 = ET.SubElement(m, 'layer', {'id': '1', 'name': 'back', 'width': str(W), 'height': str(H)})
d1 = ET.SubElement(l1, 'data', {'encoding': 'csv'})
d1.text = '\n1,1,1,1,1,1,1,1,1,1\n'  # only 10 tiles, should be 80
l2 = ET.SubElement(m, 'layer', {'id': '2', 'name': 'front', 'width': str(W), 'height': str(H)})
d2 = ET.SubElement(l2, 'data', {'encoding': 'csv'})
d2.text = '\n' + make_csv_data(W, H, 'solid')
add_object_group(m, "front_objects", [{'id': 1, 'class': 'spawn', 'x': 32, 'y': 64}])
write_tmx(m, "stress_tile_count_mismatch.tmx")

# 22. Float coordinates in objects
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'), tile_color="0.2,0.2,0.3")
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'), tile_color="0.5,0.5,0.6")
add_object_group(m, "front_objects", [
    {'id': 1, 'class': 'spawn', 'x': 32.5, 'y': 64.7},
    {'id': 2, 'class': 'skeleton', 'x': 160.123, 'y': 64.456, 'props': {'lvl': 2}},
])
write_tmx(m, "stress_float_coords.tmx")

# 23. Object using 'type' attribute instead of 'class' (Tiled < 1.9 compatibility)
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'))
add_object_group(m, "front_objects", [
    {'id': 1, 'type': 'spawn', 'x': 32, 'y': 64},
    {'id': 2, 'type': 'skeleton', 'x': 160, 'y': 64, 'props': {'lvl': 1}},
])
write_tmx(m, "stress_type_attr.tmx")

# 24. Object using name for classification (no class or type attribute)
m = make_map(W, H)
add_tile_layer(m, "back", W, H, make_csv_data(W, H, 'solid'))
add_tile_layer(m, "front", W, H, make_csv_data(W, H, 'solid'))
# We need to add objects with just a name - use raw ET
group = ET.SubElement(m, 'objectgroup', {'id': '1', 'name': 'front_objects'})
obj1 = ET.SubElement(group, 'object', {'id': '1', 'name': 'spawn_point', 'x': '32', 'y': '64'})
obj2 = ET.SubElement(group, 'object', {'id': '2', 'name': 'skeleton_warrior', 'x': '160', 'y': '64'})
write_tmx(m, "stress_name_only.tmx")

# 25. Very large map (50x30)
m = make_map(50, 30)
add_tile_layer(m, "back", 50, 30, make_csv_data(50, 30, 'platforms'), tile_color="0.2,0.2,0.3")
add_tile_layer(m, "front", 50, 30, make_csv_data(50, 30, 'solid'), tile_color="0.5,0.5,0.6")
add_object_group(m, "front_objects", [
    {'id': 1, 'class': 'spawn', 'x': 64, 'y': 800},
    {'id': 2, 'class': 'skeleton', 'x': 800, 'y': 800, 'props': {'lvl': 10}},
    {'id': 3, 'class': 'heal', 'x': 400, 'y': 800},
])
write_tmx(m, "stress_large_map.tmx")

print(f"\nAll stress test maps created! Total: 25 maps")
