# StarryKnight

A LÖVE 2D proof-of-concept that fuses Mario-style sidescrolling with Diablo-style hack-and-slash on a **Multi-plane** depth-shifting map: every zone is sliced into **2–5 parallel z-depth strips** that the player shifts between to navigate. Different zones use different slice counts, mimicking how a real isometric ARPG world has rooms of varying width.

## Run

The LÖVE app bundle is already in this directory (`love.app/`, version 11.5).

```sh
./love.app/Contents/MacOS/love .
```

The first launch may show a macOS Gatekeeper prompt; allow it.

## Controls

- `A` / `D` — move left / right
- `Space` — jump
- `J` — melee swing
- `W` — shift one slice deeper (away from camera)
- `S` — shift one slice closer (toward camera)
- `1` / `2` — load demo map 1 (`outskirts_01`, 3 slices) / map 2 (`cliffside_02`, 4 slices)
- `R` — reload current map (also picks up hot edits to the map file)
- `Esc` — quit

If a shift is **blocked** by terrain in the target layer, you'll see a red flash on the depth indicator (top-right HUD). The depth indicator has one cell per slice, so you can see at a glance how many depth lanes the current zone has and which one you're on.

## What's where

- `conf.lua`, `main.lua` — LÖVE entry.
- `src/state.lua`, `src/play.lua` — gamestate machine; v0 has a single `play` state, plus map-switching hotkeys.
- `src/map.lua`, `src/layer.lua`, `src/tile.lua` — the Multi-plane mapping system: a `Map` owns an ordered array of 2–5 `Layer`s, each with its own Box2D world and tile grid. Index 1 is farthest from camera, index N is closest.
- `src/player.lua`, `src/enemy_skeleton.lua`, `src/pickup.lua` — entities.
- `src/combat.lua`, `src/hud.lua`, `src/camera.lua` — feel/feedback.
- `src/physics.lua` — thin `love.physics` helpers (Box2D wrappers).
- `src/assets.lua` — color palette + fonts.
- `assets/maps/outskirts_01.lua` — 3-slice demo (`far` / `mid` / `near`).
- `assets/maps/cliffside_02.lua` — 4-slice demo (`cliff` / `ridge` / `road` / `creek`).
- `archive/` — previous versions of files moved here when superseded.

## Authoring a new map

A map file returns a Lua table with this shape:

```lua path=null start=null
return {
  tilesize    = 32,
  spawn_index = 2,   -- which layer index the player spawns on
  layers = {         -- 2 to 5 entries, ordered far → near
    { name = "...", tiles = [[...]], tile_color = {r,g,b},
      spawn = { x=..., y=... }, entities = { ... } },
    ...
  },
}
```

`tiles` is a multi-line string where `#` is a solid tile and any other character is empty. Parallax and dim values are derived automatically from each layer's distance to the active slice, so you only need to set `tile_color` for visual distinction.

## Design notes

- **Physics**: `love.physics` (Box2D). One world per layer. Player is a dynamic body with fixed rotation and zero friction; horizontal velocity is set directly each frame for tight platformer feel. Pickups are sensor fixtures. Player and enemies share a negative Box2D group index so they don't physically collide — combat is resolved by AABB overlap in update().
- **Layer shift**: free-form. Pressing W/S anywhere triggers an AABB tile check against the target layer at the player's current x/y. Clear → swap; blocked → red flash + tiny shake. Shifts step exactly one slice; from index 1 you can't jump directly to index 3.
- **Parallax / dim**: computed dynamically from each layer's signed distance to the active slice (steps of 0.22), so the same draw code handles maps with 2, 3, 4, or 5 slices without any per-map tuning.
- **Floor seams**: each row's contiguous run of solid tiles is collapsed into a single static rectangle body so the player can't snag on "ghost edges" between adjacent floor tiles.
- **RPG**: each actor has `lvl`, `hp`, `dmg`, `def`. `maxHp = 10*lvl`, `dmg = 2+lvl`, `def = lvl-1`. Damage = `max(1, atk.dmg - tgt.def)`.

## Play in the browser (love.js)

A WebAssembly build is served from iris, **Tailscale-only** (dev use, never public). URL: `http://<iris-tailnet-name>:8088/` (set by the Caddy route; see `tools/web/Caddyfile.snippet`). Keyboard controls are the same as above; touch is not supported yet.

- **Rebuild by hand:** `tools/build_web.sh` (needs node, npm, zip; installs love.js 11.4.1 into `.web-tools/` on first run). Output goes to `web/` (git-ignored).
- **Automatic rebuild:** `tools/web/starryknight-web.timer` runs `tools/web/update_web.sh` every 2 minutes: `git pull --ff-only origin main`, then rebuilds only if HEAD changed. Install the units from `tools/web/` into systemd and adjust `User=` and the paths.
- Note: love.js runs LÖVE 11.4 while `conf.lua` says 11.5; this has not been checked in a real browser from the build host.
