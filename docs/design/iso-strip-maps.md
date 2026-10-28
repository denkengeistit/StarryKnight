# Iso-strip maps

Starry Knight plays like a Diablo-style ARPG split into side-scroller layers.
Authors draw **one isometric map**; `tools/iso_to_starryknight.py` slices it
into strips, each of which becomes one side-scroller plane in the existing Lua
map format. (`tools/tmx_to_starryknight.py`, where each Tiled layer is a
hand-drawn side view, is legacy.)

## Slicing math

Tiled isometric: tile `(x, y)` (0-based) draws at screen
`((x - y) * tw/2, (x + y) * th/2)`. Increasing `x` goes down-right (toward the
viewer); decreasing `y` goes up-right. So the bottom-left → top-right diagonal
is the direction of **constant x, decreasing y**.

- `strip_width` `sw` (map property, default 2, `--strip-width` overrides) must
  divide map width `W`.
- Strip `s` (1-based) holds tiles with `x` in `[(s-1)*sw, s*sw)`.
- Layer count `N = W / sw`, no cap. Strip 1 (top-left, farthest) = layer 1;
  strip N (bottom-right, nearest) = layer N. Engine convention: index 1 is
  farthest.
- Spawn layer = `ceil(N/2)` (the middle strip).
- Scroll axis: side-view column `c = H - 1 - y`, so walking right moves
  up-right along the diagonal, starting from the bottom-left end.
  Width of each layer = `H` columns. The `sw` tiles across a strip are
  collapsed into one lane (depth within a strip is not modelled).

## Terrain: elevation

Side-view terrain comes from **tile layers with an `elevation` property**
(int, default 0 = ground). A non-empty tile on a layer of elevation `e` at
`(x, y)` makes slot `e` solid in column `c` of strip `x / sw`. Any tile in the
strip's `sw` lanes counts (union).

- Ground = elevation 0; gaps in it are pits. Walls/steps = tiles on layers
  with elevation 1, 2, … Stack layers to build taller walls and stairs.
- Side view rows = `SKY(8) + maxElevation + 1`; slot `e` is row
  `SKY + maxE - e`, so ground is the bottom row.
- Tile identity (gid) is ignored; only presence matters, as in the old
  converter. Each strip gets a colour interpolated far (cool blue) → near
  (warm tan).

## Entities and spawns

Use Tiled object layers. Object `x, y` in iso maps are in Tiled's iso pixel
space: tile coordinate = `x / tileheight`, `y / tileheight`.

- Strip = `floor(tx) / sw`; column = `H - ty`.
- Height: the object stands on the highest solid block of that column in its
  strip (pits: entity skipped with a warning).
- `spawn`: only its column matters. Every strip gets a spawn at the nearest
  column with floor (so W/S shifts and respawns always land on ground); the
  player starts on the middle strip.
- Classes: `skeleton`/`enemy` (property `lvl`), `heal`/`potion`, `xp`/`coin`.

## Engine changes (done)

- `src/map.lua`: removed the 5-layer cap (min 2 kept).
- `src/play.lua`: each non-active layer is offset 18px per step of distance,
  which runs off screen with many layers, so only the active layer ±2
  (`DRAW_RADIUS`) are drawn. Alpha already clamps at 0.25. All layers still
  simulate (cheap Box2D worlds; `update_inactive`).
- HUD depth indicator is one cell per layer (short names `s1…sN`); 7 cells fit
  fine, roughly 40 cells fit a 1280 px screen.
- Hotkey `3` loads `assets/maps/iso_demo` (old `test_basic` moved to `9`).

## Not covered (KISS)

Depth within a strip, diagonal slopes, per-tile art, overhangs (an elevated
block over a hole is just a floating block), non-integer elevations.
