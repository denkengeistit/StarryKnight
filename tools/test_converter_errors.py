#!/usr/bin/env python3
"""Test that the converter catches invalid TMX inputs at convert time."""
import subprocess, sys, os, shutil

TOOL = "tools/tmx_to_starryknight.py"
TMP  = "/tmp/sk_test_out.lua"

def run(tmx_content):
    path = "/tmp/sk_test_input.tmx"
    with open(path, "w") as f:
        f.write(tmx_content)
    r = subprocess.run([sys.executable, TOOL, path, TMP],
                      capture_output=True, text=True)
    if os.path.exists(TMP):
        os.remove(TMP)
    return r.returncode, r.stderr

MAP_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" width="5" height="4"
     tilewidth="32" tileheight="32" infinite="0">
 <tileset firstgid="1" name="t" tilewidth="32" tileheight="32" tilecount="1" columns="1">
  <tile id="0"/>
 </tileset>
'''

SOLID_DATA = '''<data encoding="csv">
0,0,0,0,0,
0,0,0,0,0,
1,1,1,1,1,
1,1,1,1,1
</data>'''

SPAWN_GROUP = '''<objectgroup name="slice1_objects">
 <object id="1" class="spawn" x="32" y="64"/>
</objectgroup>'''

failures = []

def expect_fail(label, xml, expected_fragment):
    code, stderr = run(xml)
    if code == 0:
        failures.append(f"{label}: expected failure but converter succeeded")
    elif expected_fragment not in stderr:
        failures.append(f"{label}: expected '{expected_fragment}' in stderr, got: {stderr.strip()}")
    else:
        print(f"ok (correctly rejected): {label}")

def expect_ok(label, xml):
    code, stderr = run(xml)
    if code != 0:
        failures.append(f"{label}: expected success but got exit {code}: {stderr.strip()}")
    else:
        print(f"ok (accepted):           {label}")

# --- Too few layers (1) ---
exact_1_layer = MAP_HEADER + f'''
<layer id="1" name="slice1" width="5" height="4">{SOLID_DATA}</layer>
{SPAWN_GROUP}
</map>'''
expect_fail("too few layers (1)", exact_1_layer, "2-5")

# --- Too many layers (6) ---
layer_block = lambda i: f'<layer id="{i}" name="slice{i}" width="5" height="4">{SOLID_DATA}</layer>\n'
spawn_for_1 = '''<objectgroup name="slice1_objects">
 <object id="1" class="spawn" x="32" y="64"/>
</objectgroup>'''
six_layers = MAP_HEADER + ''.join(layer_block(i) for i in range(1, 7)) + spawn_for_1 + "</map>"
expect_fail("too many layers (6)", six_layers, "2-5")

# --- Empty tile layer (no solid tiles) ---
empty_layer = MAP_HEADER + f'''
<layer id="1" name="slice1" width="5" height="4">{SOLID_DATA}</layer>
<layer id="2" name="slice2" width="5" height="4">
 <data encoding="csv">
0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0
</data>
</layer>
{SPAWN_GROUP}
</map>'''
expect_fail("empty tile layer", empty_layer, "no solid tiles")

# --- No spawn object ---
no_spawn = MAP_HEADER + f'''
<layer id="1" name="slice1" width="5" height="4">{SOLID_DATA}</layer>
<layer id="2" name="slice2" width="5" height="4">{SOLID_DATA}</layer>
</map>'''
expect_fail("no spawn object", no_spawn, "No spawn object")

# --- Unmatched objectgroup ---
bad_group = MAP_HEADER + f'''
<layer id="1" name="slice1" width="5" height="4">{SOLID_DATA}</layer>
<layer id="2" name="slice2" width="5" height="4">{SOLID_DATA}</layer>
<objectgroup name="typo_objects">
 <object id="1" class="spawn" x="32" y="64"/>
</objectgroup>
</map>'''
expect_fail("unmatched objectgroup", bad_group, "doesn't match any tile layer")

# --- Wrong tilesize warns but still succeeds ---
big_tiles = MAP_HEADER.replace('tilewidth="32" tileheight="32"', 'tilewidth="16" tileheight="16"') + f'''
<layer id="1" name="slice1" width="5" height="4">{SOLID_DATA}</layer>
<layer id="2" name="slice2" width="5" height="4">{SOLID_DATA}</layer>
{SPAWN_GROUP}
</map>'''
expect_ok("wrong tilesize (warns, not fatal)", big_tiles)

# --- Valid 2-layer map with per-object slice property ---
per_obj_slice = MAP_HEADER + f'''
<layer id="1" name="slice1" width="5" height="4">{SOLID_DATA}</layer>
<layer id="2" name="slice2" width="5" height="4">{SOLID_DATA}</layer>
<objectgroup name="misc">
 <object id="1" class="spawn" x="32" y="64">
  <properties><property name="slice" value="1"/></properties>
 </object>
</objectgroup>
</map>'''
expect_ok("per-object slice property", per_obj_slice)

if failures:
    print()
    for f in failures:
        print("FAIL:", f)
    sys.exit(1)
else:
    print("\nAll error-handling tests passed.")
