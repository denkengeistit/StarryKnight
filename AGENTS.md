# AGENTS.md — StarryKnight

## Running the game

```
./love.app/Contents/MacOS/love .
```

Long-running process. No build/lint/test commands — verification is in-game. Press `R` to hot-reload the current map module.

## Code search

Exclude `love.app/`: `grep -r "pattern" src assets tools --include="*.lua"`

## Code layout

- Entry: `main.lua` -> `src/state.lua` (thin state switcher) -> `src/play.lua` (game loop + input)
- `src/map.lua` — loads a map Lua file, validates it (2–5 layers), creates Layer objects
- `src/layer.lua` — one depth slice: tile string parsing, Box2D world, entity spawning
- `src/play.lua:~41` — `MAPS` table maps keyboard keys to map module paths; new maps must be registered here or they are unreachable in-game
- `assets/maps/` — live map files (`cliffside_02.lua`, `test_basic.lua`)
- `archive/assets/maps/` — retired maps, not loaded by the game

## Map format

Map files return a table validated by src/map.lua (2–5 layers, spawn_index in range). See src/layer.lua for tile parsing and entity spawning.

## Importing from Tiled (TMX)

```
python3 tools/tmx_to_starryknight.py path/to/map.tmx assets/maps/mymap.lua
```

The converter enforces engine constraints at import time. After converting, register the map in src/play.lua's MAPS table.

**Tiled authoring rules the converter enforces at convert time:**
- 2–5 tile layers (= depth slices). Fails loudly otherwise.
- Every tile layer must have at least one solid tile. Empty layers fail.
- Tile layer format must be **CSV** (Map > Map Properties > Tile Layer Format). Base64/zlib encoded layers fail with a clear message.
- One object with class `spawn` is required. Multiple or zero spawn objects fail.
- Object groups are matched to slices by name: an objectgroup `foo_objects` (or `foo`) attaches to the tile layer named `foo`. Alternatively, set a custom int property `slice` (1-based) on the group or on individual objects.
- `tile_color` can be set as a custom string property on a tile layer: `"r,g,b"` (0–1 floats) or Tiled's `#AARRGGBB` hex.
- Entity object classes: `spawn`, `skeleton`/`enemy`, `heal`/`potion`, `xp`/`coin`. Unknown classes are skipped with a warning.
- `lvl` custom int property on skeleton objects sets difficulty (default 1).

**After converting**, register the map in `src/play.lua`:

```lua
-- in the MAPS table (~line 41)
["2"] = "assets.maps.mymap",
```

## Converter tests

```bash
python3 tools/test_converter.py          # structural check on assets/maps/test_basic.lua
python3 tools/test_converter_errors.py   # error-handling: wrong layer count, empty layers, missing spawn, etc.
```

See BUILD_LOG.md for the full design history and bug-fix timeline.

## Lua version

The web build (love.js) runs PUC Lua 5.1, not LuaJIT: no `goto`/labels, no `//`, no bitwise operators, no `utf8` library. Write Lua 5.1-compatible code and check with `luac5.1 -p <file>`; `tools/build_web.sh` refuses to build if any file fails that check.
