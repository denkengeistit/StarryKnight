#!/usr/bin/env python3
"""Smoke-test the TMX converter output against the engine's expected Lua format."""
import sys

def check(path):
    with open(path) as f:
        text = f.read()

    errors = []
    def want(cond, msg):
        if not cond:
            errors.append(msg)

    want("tilesize = 32" in text,               "missing tilesize = 32")
    want("spawn_index = 2" in text,             "wrong spawn_index (expected midground=2)")
    want('name       = "background"' in text,   "missing background slice")
    want('name       = "midground"' in text,    "missing midground slice")
    want('name       = "foreground"' in text,   "missing foreground slice")
    want("0.25, 0.2, 0.35" in text,            "background tile_color wrong")
    want("0.45, 0.4, 0.55" in text,            "midground tile_color wrong")
    want("0.6, 0.55, 0.7" in text,             "foreground tile_color wrong")
    want("spawn      = { x = 64, y = 256 }" in text, "spawn coords wrong")
    want('type = "skeleton"' in text,          "skeleton entity missing")
    want('type = "heal"' in text,              "heal entity missing")
    want("lvl = 1" in text,                    "skeleton lvl missing")
    want(text.count("[[") == 3,               f"expected 3 tile blocks, got {text.count('[[')}")
    want("....###" in text,                   "foreground platform tiles missing (....###)")
    want(text.count("####################") >= 9, "not enough ground rows (3 slices x 3 rows)")

    if errors:
        for e in errors:
            print("FAIL:", e)
        sys.exit(1)
    else:
        lines = text.count("\n")
        print(f"OK: {path} ({lines} lines, {len(text)} bytes) - all checks passed")

check("assets/maps/test_basic.lua")
