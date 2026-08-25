# StarryKnight — Build Log
A summary of the design discussion and iterative build of a LÖVE 2D proof-of-concept that fuses Mario-style sidescrolling with Diablo-style hack-and-slash on a multi-plane depth-shifting map.
## The pitch
A 2D action-platformer where every zone is an isometric ARPG map "sliced" into **N parallel z-depth strips** (2–5 per zone). Each strip is a full sidescroller with its own internal verticality. The player can shift between adjacent strips anywhere the destination is clear of terrain, creating a navigation puzzle out of what would otherwise be flat traversal.
This is the inverse of the typical 2.5D depth-shift game: instead of being a single sidescroller with an occasional depth dimension, it's an entire top-down ARPG world unrolled into parallel sidescrollers.
## Design decisions locked in
1. **Engine**: LÖVE 2D 11.5, dropped into the project folder as `love.app/`.
2. **Physics**: built-in `love.physics` (Box2D wrapper). One world per layer. Player is a dynamic body with `setFixedRotation(true)`; horizontal velocity set directly each frame for tight platformer feel. Pickups are sensor fixtures.
3. **Slice geometry**: depth strips run far → near in z. *Not* high → low in y. Each slice has its own internal vertical platforming.
4. **Layer switching**: free-form. `W`/`S` anywhere; succeeds if the target layer's tiles don't overlap the player's AABB at the current x/y. Terrain in each slice is the gating mechanism — no shift-point entities.
5. **Player spawn**: middle slice (configurable per-map via `spawn_index`).
6. **Slice count**: variable per map. 2 to 5 slices. Different zones can have different counts to mimic varying isometric room widths.
7. **RPG layer**: deliberately minimal. Four stats: `lvl`, `hp`, `dmg`, `def`. Derivation `maxHp=10·lvl`, `dmg=2+lvl`, `def=lvl-1`. Damage = `max(1, atk.dmg − tgt.def)`.
8. **Art**: default LÖVE rendering, colored rectangles. PoC scope.
9. **Inactive-layer rendering**: dim + parallax only. Plus a pseudo-3D vertical offset (deeper layers nudged higher on screen, closer layers nudged lower).
10. **Pit design rule**: every pit must be jump-out-able. Width ≤ 5 tiles, depth = 1 tile.
11. **Archive policy**: superseded files move under `archive/` mirroring their original path; nothing is ever deleted.
## What got built
### Project layout
```
StarryKnight/
  love.app/                 -- LÖVE 11.5 (in-place)
  conf.lua, main.lua        -- LÖVE entry
  src/
    state.lua, play.lua     -- gamestate; map-switching hotkeys
    map.lua                 -- ordered 2-5 layer stack + active index
    layer.lua               -- per-slice tile grid + Box2D world
    tile.lua, physics.lua   -- tile defs; love.physics helpers
    camera.lua              -- smooth follow camera
    combat.lua              -- damage formula + floating numbers
    hud.lua                 -- HP/LVL/XP + per-slice depth indicator
    assets.lua              -- colors + fonts
    player.lua              -- movement, jump, attack, shift
    enemy_skeleton.lua      -- idle→chase→attack→dead AI
    pickup.lua              -- heal orb (+5 HP), xp shard (+10 XP)
  assets/maps/
    outskirts_01.lua        -- 3-slice demo (far / mid / near)
    cliffside_02.lua        -- 4-slice demo (cliff / ridge / road / creek)
  archive/                  -- superseded files preserved here
  BUILD_LOG.md              -- this file
  README.md
```
### Runtime controls
- `A` / `D` — move
- `Space` — jump
- `J` — melee swing
- `W` / `S` — shift one slice deeper / closer
- `1` / `2` — load map 1 / map 2
- `R` — reload current map (also picks up hot-edits to map files)
- `Esc` — quit
## Iteration history (bugs fixed during the build)
**1. Jump didn't work at all.**
Grounded check was inverted. Box2D contact normals point from fixture A to fixture B. With LÖVE's Y-down coordinates, when the player (A) is standing on a tile (B), the normal points **down** into B, so `ny > 0`. The original check used `< -0.5`. Fixed to `> 0.5`.
**2. Player walled off by skeletons.**
Skeletons were dynamic bodies whose AI clamped their velocity to 0 in melee range — they acted as immovable walls. Fixed by giving the player and enemy fixtures the same **negative Box2D group index** so they no longer physically collide. Combat is still resolved via AABB checks in `update()`, not contact events, so hit detection is unaffected.
**3. Movement snagged on floor tile seams.**
Classic "ghost edge" issue: every tile being its own static rectangle means the vertical face between two adjacent floor tiles can briefly register as a wall collision when the player slides across it, killing horizontal velocity for a tick. Fix: in `Layer:_build_tiles`, collapse each row's contiguous run of solid tiles into a single long static body so the internal seams cease to exist. (Drawing still happens per-tile so visuals are unchanged.)
**4. Pits were unrecoverable.**
Original pits extended below the bottom of the map; falling in triggered respawn. Reworked all pits into 1-tile-deep trenches with a solid floor immediately below, and narrowed any pit wider than 5 tiles. The player can now always jump out, though pits are now "soft" obstacles (slow detour) rather than hard ones — walls remain the hard gating mechanism.
## Architecture decisions worth remembering
**Per-layer Box2D worlds.** Each `Layer` instance owns its own `love.physics.newWorld(0, 1500)`. Only the active world ticks AI / damage; inactive worlds tick for gravity continuity only. On a shift, the player body is destroyed in the old world and recreated at the same x/y in the target world.
**Layers as ordered array, active as integer index.** Originally `Map.layers = { far=..., mid=..., near=... }` with `Map.active` a string. Refactored to `Map.layers = { layer1, layer2, ..., layerN }` (ordered 1..N where 1 is farthest) with `Map.active` being the integer index. This is what enabled variable slice counts.
**Dynamic parallax / dim / vertical offset.** Originally each map declared `parallax = 0.7` etc. per layer. Now computed in `play.lua` from each layer's signed distance to the active slice (constants `PARALLAX_STEP = 0.22`, `ALPHA_STEP = 0.22`, `Y_OFFSET_STEP = 18`, `MIN_ALPHA = 0.25`). Same code works for any layer count.
**Layer shift = AABB tile-grid query.** No shift-point entities. `request_shift(dir)` computes the target index, calls `target_layer:tile_blocks_aabb(player_x, player_y, w, h)`, and either swaps the player's body into the target world or shows blocked-shift feedback (red HUD flash + tiny shake).
**Map format.**
```lua
return {
  tilesize    = 32,
  spawn_index = 2,
  layers = {                  -- 2 to 5 entries, ordered far → near
    { name=..., tiles=[[...]], tile_color=..., spawn=..., entities=... },
    ...
  },
}
```
`tiles` is a multi-line string where `#` is solid and any other character is empty. The map module is `package.loaded`-cleared on reload, so editing a map file and pressing `R` in-game refreshes it.
**Authoring rules locked in.**
- Each layer must be a uniform-width rectangle (all rows same length). An `awk` one-liner used during the build can verify this.
- Pits ≤ 5 tiles wide, exactly 1 tile deep.
- Walls (vertical solid columns above the floor) are the *hard* obstacles that force shifts.
## Out of scope (for this prototype)
- Tiled / LDtk integration (Lua-tables are sufficient for v0).
- Procedural map generation (rooms are hand-authored).
- Multiplayer, save system, full skill tree, audio mixing.
- Final art — placeholder colored rectangles are intentional.
- Cross-zone progression (currently `1`/`2` just hot-swap).
## Where it stands
Playable proof-of-concept. Both demo maps (`outskirts_01` 3-slice and `cliffside_02` 4-slice) boot cleanly, the Triplane/Multi-plane shift mechanic works, combat and pickups function, and pits are recoverable. The core invariant — that the runtime is slice-count-agnostic — is what makes the design feel like a real navigation system rather than a one-off gimmick.
