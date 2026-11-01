# Stellar core: shared contract for the first build

> Written by Hark on 2026-11-01 so that four parallel cards can build against one interface. The rules come from progression-system.md section 10 (Andy's answers). The model details below are Hark's first-build interpretation, and playtesting can change them.

## Model
- Units: mass in **solar masses (M☉)**. Real thresholds stay real. Only **time** is scaled (`TIME_SCALE`, game seconds per simulated year) so a run lasts minutes.
- Player state: `H` (hydrogen fuel mass) and `He` (helium ash). Total mass `M = H + He`.
- **Burn (real relationship):** luminosity `L = L☉ · M^3.5` (main-sequence mass-luminosity). Fusing H→He releases 0.7% of the rest mass, so the hydrogen burn rate is `dH/dt_burn = -L / (0.007 c²)`. Of the hydrogen burned, 99.3% becomes He and 0.7% leaves as energy. Bigger stars burn disproportionately faster, which is real and is the strategy.
- **The two displayed stats:** `H` (current hydrogen mass) and `dH/dt` (intake minus burn, smoothed over ~2 s).
- **No HP.** Enemy hits and antimatter annihilation remove hydrogen directly. When `H` reaches 0 the core is out of fuel and the run ends.
- **Derived stats** (pure functions of M, H and dH/dt, in src/stellar.lua): radius ∝ M^0.8 (main sequence), which sets body size and melee reach; damage ∝ L; gravity-pull radius from `GM`; and speed. Keep each formula one line, with a comment naming the physics.
- **Gravity absorb:** stand within pull radius of a defeated enemy's corpse for ~1 s and its mass streams in (`stellar:addMass(corpse.mass)`, animated).
- **Run end and fate** (real thresholds on total mass M at fuel exhaustion): `M < 8` → red giant, then white dwarf: fate `"dwarf"` (shown as giant → dwarf), payout **gravity**. `M ≥ 8` → core-collapse supernova: fate `"nova"`, payout **iron**.
- **Meta currencies** (persisted with love.filesystem in `meta.lua` in the save dir): `iron` (spendable) and `gravity` (sum of the final masses of all stable-star runs, never decreases). First-build effects: gravity sets starting hydrogen (more gravity, bigger start); iron buys one-run boosts on the title screen.

## Module API (src/stellar.lua, card "Stellar core")
```lua
local Stellar = require("src.stellar")
local s = Stellar.new(H0)        -- starting hydrogen, M☉
s:update(dt)                     -- burn, smoothing
s:addMass(m)                     -- intake (absorb); m > 0
s:removeMass(m, cause)           -- damage / annihilation; returns actual removed
s.H, s.He, s:M(), s:dHdt(), s:L()
s:radius(), s:damage(), s:pullRadius(), s:speed()
s:isDepleted()                   -- H <= 0
s:fate()                         -- "nova" | "dwarf"  (by real thresholds)
```
Physics constants and the game-scaling knobs live in **src/physics.lua** (`G, c, Msun, Lsun, MS_EXP=3.5, EFF=0.007, TIME_SCALE, NOVA_MIN=8, ...`), each with a source comment. The research card writes docs/design/physics-reference.md; Hark folds its values into physics.lua.

## Enemy contract (card "Cosmic enemies")
Each enemy has `x, y, layer, alive, mass` (hydrogen it yields), `touchDamage` (M☉ removed per hit), `update(dt, player)`, `draw()` and `hit(dmg)`. On death it leaves a corpse entity `{x, y, layer, mass, absorbed=false}` in `layer.entities.corpses`. The player (stellar core card) absorbs corpses.

## Run contract (card "Run endings and meta")
src/run.lua and src/meta.lua. `Run.finish(stellar)` reads `stellar:fate()` and `stellar:M()`, pays out (nova: iron = f(M); dwarf: gravity += M), saves, and shows the run-end screen with a short real-physics explanation of the fate (educational). `Meta.load()/save()`, `Meta.startingH()`.
