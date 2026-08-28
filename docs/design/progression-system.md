# StarryKnight — Progression System Design

> **Status:** Draft for review
> **Author:** Design team
> **Audience:** Andy (creator) + implementation team
> **Last updated:** 2026-08-28

---

## 1. Overview

This document specifies the core RPG progression system for **StarryKnight**, a
depth-shifting 2D platformer built in LÖVE 2D (Lua). The progression system is
the thematic and mechanical heart of the game: **the player IS a star**, and
advancement follows the real physics of **stellar nucleosynthesis** — the chain
of nuclear fusion reactions that stars use to produce energy and synthesize
heavier elements over their lifetimes.

The current codebase has a minimal RPG layer (four stats — `lvl`, `hp`, `dmg`,
`def` — with linear scaling and a simple XP-from-pickups loop). This document
describes how that layer is expanded into a thematically rich, multi-tier
progression system that culminates in an endgame branch, while remaining
compatible with the existing depth-shifting platformer mechanics and the TMX
map import pipeline.

The goal of this document is to **align with Andy's vision before coding
begins**. Open questions are collected in [Section 9](#9-questions-for-andy).

---

## 2. The Star-as-Knight Metaphor

**"Starry Knight" is a play on words — the knight is literally a star.**

The central conceit is that the player character is not a person wearing star
motifs; it is a star, and the RPG progression is the star's life cycle. Every
gameplay system is an allegory for a real astrophysical process:

| Astrophysical concept | Game concept |
|---|---|
| A star | The player character (the "knight") |
| Gravity (inward force) | Threats, enemies, the pressure to advance or die |
| Nuclear fusion (outward force) | The player's active power — combat, abilities, energy output |
| Hydrostatic equilibrium | The "knight" state — a star that is stable because fusion pushes back against gravity |
| Stellar fuel (hydrogen, helium, …) | Collectible elements, the progression currency |
| Running out of fuel / fusion going energy-negative | Loss of equilibrium → game pressure, collapse risk |
| Supernova / white dwarf / neutron star / black hole | Endgame branching paths |

**The knight is the stable form.** A star exists in equilibrium: gravity wants
to crush it, fusion pushes outward, and as long as the two are balanced the star
endures. That equilibrium *is* what the knight represents. The player's job is
to maintain it — to keep fusing, keep producing energy, keep pushing back — for
as long as possible. When the fuel runs out and fusion can no longer hold
gravity at bay, the star (and the player) faces its endgame: collapse and
explosion, or a quiet fade into a dense remnant.

This metaphor is not decorative. It drives every design decision below: what the
player collects, why leveling matters, what "death" means, and what the endgame
choice represents.

---

## 3. Progression Tiers

Progression is organized into **tiers**, each corresponding to a real stage of
stellar nucleosynthesis. Within each tier the player collects a specific element
and, upon accumulating enough, begins **fusing** it into the next heavier
element — which unlocks the next tier and a new ability or stat upgrade.

The tiers below follow the actual fusion chain of massive stars, in order of
increasing temperature (which in-game maps to increasing player level / tier).

### Tier 0 — Ignition (Hydrogen Collection)

- **Element collected:** Hydrogen (H)
- **Fusion reaction:** Proton-proton chain (H → He)
- **Astrophysical analog:** A protostar igniting hydrogen fusion; entering the main sequence
- **Level range:** Levels 1–10
- **XP / collection requirement:** ~30 XP per level (current baseline), ~300 H atoms to complete the tier
- **Player ability / upgrade:** Basic fusion ignition. The player gains the melee swing (already exists) and the ability to sustain HP. This is the "main sequence" entry — the star has "turned on."
- **Thematic note:** This is where the player *becomes* a knight — equilibrium is first achieved.

### Tier 1 — Main Sequence (Hydrogen → Helium)

- **Element collected:** Hydrogen → fused into Helium (He)
- **Fusion reaction:** pp-chain / CNO cycle (H → He)
- **Astrophysical analog:** Main sequence star (like our Sun) steadily burning hydrogen
- **Level range:** Levels 11–25
- **XP / collection requirement:** Scaling XP curve (e.g. `lvl * 30`, increasing per tier), ~600 H to fuse into a He reserve
- **Player ability / upgrade:** **Helium Reserve.** HP pool increases (the star grows), damage scales up. The player can now stockpile Helium as the "spent fuel" that will fuel the next tier.
- **Mechanic introduced:** Fusion rate must exceed decay rate (see [Section 7](#7-energy--stability-system)). Mild pressure begins.

### Tier 2 — Red Giant (Helium → Carbon / Oxygen)

- **Element collected:** Helium → fused into Carbon (C) / Oxygen (O)
- **Fusion reaction:** Triple-alpha process (3 He → C; C + He → O)
- **Astrophysical analog:** Red giant — the star has exhausted core hydrogen and ignites helium fusion
- **Level range:** Levels 26–45
- **XP / collection requirement:** Steeper curve, ~900 He to complete
- **Player ability / upgrade:** **Shell Burning.** The player gains a ranged or area energy attack (fusion "flare"). The star has swelled — represented by a larger effective hitbox *or* a damage aura. Depth-shifting becomes strategically important: heavier elements may concentrate on specific z-layers.
- **Mechanic introduced:** Multi-element inventory. The player must manage both Helium intake (fuel) and Carbon/Oxygen output (progress).

### Tier 3 — Carbon Burning (Carbon → Neon / Sodium / Magnesium)

- **Element collected:** Carbon → fused into Neon (Ne), Sodium (Na), Magnesium (Mg)
- **Fusion reaction:** Carbon fusion
- **Astrophysical analog:** Massive star (≥8 solar masses) igniting carbon fusion
- **Level range:** Levels 46–65
- **XP / collection requirement:** High requirement; fusion is "expensive"
- **Player ability / upgrade:** **Elemental Affinity.** The byproducts (Ne, Na, Mg) grant passive buffs or selectable mods — e.g. Neon = speed/illumination, Magnesium = defense (bright flare), Sodium = reactive damage. The player chooses which byproduct to emphasize, introducing light build variety.
- **Mechanic introduced:** Byproduct branching — minor player choice within a tier.

### Tier 4 — Neon Burning (Neon → Oxygen / Silicon)

- **Element collected:** Neon → Oxygen (O), Silicon (Si)
- **Fusion reaction:** Neon fusion
- **Astrophysical analog:** Late-stage massive star
- **Level range:** Levels 66–80
- **XP / collection requirement:** Very high; the star is burning hot and fast
- **Player ability / upgrade:** **Core Compression.** Defense scales sharply (gravity is winning — the core is dense). The player can "compress" to briefly increase fusion output at the cost of stability (a risk/reward burst mechanic).

### Tier 5 — Oxygen Burning (Oxygen → Silicon / Sulfur)

- **Element collected:** Oxygen → Silicon (Si), Sulfur (S)
- **Fusion reaction:** Oxygen fusion
- **Astrophysical analog:** Final fusion stages of a massive star
- **Level range:** Levels 81–90
- **XP / collection requirement:** Extreme; fuel is scarce
- **Player ability / upgrade:** **Layered Fusion.** The player can fuse across depth layers — collecting fuel on one z-slice to power reactions observed on another. Ties the progression system tightly to the depth-shifting core mechanic.

### Tier 6 — Silicon Burning (Silicon → Iron)

- **Element collected:** Silicon → Iron (Fe)
- **Fusion reaction:** Silicon burning (alpha process ladder → Iron)
- **Astrophysical analog:** The last exothermic fusion stage. Iron is the end of the road.
- **Level range:** Levels 91–99
- **XP / collection requirement:** The hardest tier. Iron accumulates as dead weight — it cannot be fused further for energy.
- **Player ability / upgrade:** **Iron Core.** Maximum defense, but energy output is declining. The player feels gravity winning. Iron accumulation is a ticking clock toward the endgame.
- **Thematic note:** Iron is the heaviest element fusion can produce. Beyond iron, fusion *consumes* energy. The player is now living on borrowed time.

### Endgame Trigger — Collapse

- **Condition:** The player reaches the Iron Core and fusion can no longer sustain equilibrium (see [Section 7](#7-energy--stability-system)). This is not a level threshold — it is a **stability failure**.
- **Astrophysical analog:** Core collapse. The star can no longer support itself.
- **Outcome:** The endgame branch opens (see [Section 5](#5-endgame-branching)).

### Summary Table

| Tier | Name | Collect | Fuse Into | Levels | Key Ability |
|------|------|---------|-----------|--------|-------------|
| 0 | Ignition | Hydrogen | Helium | 1–10 | Fusion ignition (melee) |
| 1 | Main Sequence | Hydrogen | Helium | 11–25 | Helium Reserve (HP up) |
| 2 | Red Giant | Helium | Carbon/Oxygen | 26–45 | Shell Burning (ranged/aura) |
| 3 | Carbon Burning | Carbon | Ne/Na/Mg | 46–65 | Elemental Affinity (byproduct mods) |
| 4 | Neon Burning | Neon | O/Silicon | 66–80 | Core Compression (burst mechanic) |
| 5 | Oxygen Burning | Oxygen | Si/Sulfur | 81–90 | Layered Fusion (cross-depth) |
| 6 | Silicon Burning | Silicon | Iron | 91–99 | Iron Core (max def, declining energy) |
| — | Collapse | — | — | trigger | Endgame branch opens |

---

## 4. The Equilibrium Mechanic

Andy's key insight: **"the knight is the stable form"** — the star maintaining
equilibrium. Fusion pushes outward; gravity pushes inward; the star endures as
long as the two balance. This is not flavor text — it is the core pressure
mechanic.

### How equilibrium works in gameplay

- **Fusion output (outward force):** Driven by the player's current collection
  rate and tier. While the player is actively collecting fuel and fusing, output
  is high and the star is stable.
- **Gravity (inward force):** A constant (or tier-scaling) pressure that always
  acts against the player. Represented by enemies, environmental hazards, and a
  background "collapse pressure" that grows as fuel runs low.
- **Equilibrium:** When fusion output ≥ gravity pressure, the player is stable.
  HP regenerates slowly (or holds steady), abilities are at full strength, and
  the "knight" form is intact.

### Losing equilibrium

When the player's fuel intake drops — because they stop collecting, because the
current tier's element is scarce, or because they've reached Iron and fusion is
going energy-negative — **fusion output falls below gravity pressure**. Consequences:

1. **HP drain:** The star begins to collapse. Slow, steady HP loss representing
   gravity crushing the core. Not instant death — a mounting pressure.
2. **Ability weakening:** Attack damage and defense decay as fusion output drops.
   The player literally loses power.
3. **Visual feedback:** The star dims, shrinks, or flickers. The equilibrium
   indicator (in the HUD) tilts toward "collapse."
4. **Collapse risk meter:** A dedicated meter shows the balance. If it fully
   tips toward collapse and HP reaches zero, the endgame trigger fires (see
   [Section 5](#5-endgame-branching)) — this is *not* a normal respawn.

### Design intent

This creates a **rhythm of pressure and release**: the player must keep moving,
keep collecting, keep fusing. Standing still is dangerous. The deeper the tier,
the faster fuel burns and the harder gravity pushes. The equilibrium mechanic
turns the entire game into a sustained balancing act — which is exactly what a
star does.

> **Open question:** Should HP drain from collapse be survivable (heal orbs
> counteract it) or is it a one-way ratchet once it starts? See
> [Section 9](#9-questions-for-andy).

---

## 5. Endgame Branching

When equilibrium fails at the Iron Core stage, the player reaches the **collapse
event** — the astrophysical moment when a star can no longer support itself.
This is the game's climax and offers a **permanent, mutually exclusive choice**
between two (or more) endgame paths.

### Path A — Supernova

- **Astrophysical analog:** A massive star's core collapses and the outer layers
  explode in a supernova, briefly outshining a galaxy and forging elements
  heavier than iron.
- **What it means for the player:** The player *intentionally collapses* and
  explodes. This is a high-risk, high-reward offensive transformation.
- **Gameplay mode unlocked — Supernova Mode:**
  - The player becomes an expanding blast wave — a time-limited mode of extreme
    power that clears enemies and forges heavy elements (gold, uranium, etc.)
    as rare drops.
  - The explosion has a duration; when it ends, the player reforms at reduced
    mass (a remnant) and must survive the aftermath.
  - Thematically: the player has "won" by going out gloriously, but the game
    continues in a transformed state.
- **Tone:** Aggressive, spectacular, finite. The knight goes out in a blaze.

### Path B — White Dwarf / Dense Remnant

- **Astrophysical analog:** A lower-mass star (or the core remnant of certain
  collapses) sheds its outer layers (planetary nebula) and settles into a white
  dwarf — extremely dense, slowly cooling, stable for eons.
- **What it means for the player:** The player *compresses* rather than
  explodes. This is a defensive, endurance-oriented transformation.
- **Gameplay mode unlocked — Dwarf Mode:**
  - The player becomes small, dense, and nearly invulnerable — a tank form with
    immense defense but reduced mobility and no ranged attacks.
  - The game shifts to an endurance/survival mode: how long can the remnant
    persist? The challenge is environmental — gravity wells, collisions,
    slow energy bleed.
  - For the most massive players (highest tier / most fuel accumulated), this
    path may further branch into **Neutron Star** (extreme density, unique
    physics-based abilities like gravitational pull) or **Black Hole** (the
    ultimate "win" state — consume everything).
- **Tone:** Patient, defensive, infinite. The knight endures.

### Is the choice permanent?

**Yes.** The collapse event is a point of no return. Once the player chooses
Supernova or Dwarf, the other path is locked for that playthrough. This mirrors
real stellar evolution — a star's mass at collapse determines its fate, and the
outcome is irreversible.

> **Open question:** Should the path be determined by player choice at the
> moment of collapse, or by the player's accumulated "mass" (total elements
> collected / tier reached) — i.e. a massive player is *forced* into supernova?
> A hybrid (mass determines *available* choices, player picks among them) may
> be best. See [Section 9](#9-questions-for-andy).

---

## 6. Collection Mechanics

### What the player collects

Elements are the progression currency. Each tier has a **primary fuel element**
(the thing being fused) and produces **byproduct elements** (the result of
fusion, which may be fuel for the next tier or grant bonuses).

### How elements are obtained

**Both enemy drops and environmental pickups**, scaling by tier:

1. **Enemy drops (primary source):**
   - Defeated enemies drop element shards corresponding to the *current tier's
     fuel*. A skeleton in Tier 0 drops Hydrogen shards; enemies in Tier 2 drop
     Helium shards, etc.
   - Drop type is determined by the **zone/map** (which tier it belongs to) and
     the **active z-layer** (deeper layers may yield rarer/denser elements).
   - This directly extends the existing `pickup.lua` sensor-fixture system
     (currently heal orbs + XP shards).

2. **Environmental pickups (secondary source):**
   - Scattered element nodes in the environment — "gas clouds," "deposits," or
     element-themed crystals that the player collects by passing through them.
   - These reward exploration and depth-shifting: rare elements may only appear
     on specific z-layers, incentivizing layer switching.

3. **Fusion byproducts (internal):**
   - When the player fuses (auto-triggered upon reaching a threshold), the
     *output* element is added to inventory. E.g. fusing Hydrogen produces
     Helium, which is banked toward the next tier.

### Collection rate scaling

- **Early tiers (0–1):** Generous drops. Hydrogen is everywhere — the universe
  is mostly hydrogen. The player ramp is fast and forgiving.
- **Mid tiers (2–4):** Moderate scarcity. Fuel elements become less common;
  the player must explore more and fight tougher enemies. Collection rate is the
  primary difficulty driver.
- **Late tiers (5–6):** Scarce. Oxygen and Silicon are rare; Iron accumulates
  but is dead weight. The player feels the fuel running out — this is the
  intended pressure toward endgame.
- **Numeric scaling:** Drop chance and shard value scale inversely with tier.
  E.g. Tier 0: 80% drop rate, +10 H per shard. Tier 6: 30% drop rate, +5 Si
  per shard. Exact numbers to be tuned.

### Integration with existing pickups

The current system has two pickup types (heal orb +5 HP, XP shard +10 XP). The
progression system generalizes this:

- **XP shards → Element shards** (typed by element; the existing `+10 XP` becomes
  `+10 [Element]` toward the current tier's fusion threshold).
- **Heal orbs → remain as HP restoration**, but thematically become "energy
  injection" — a burst of fuel that stabilizes equilibrium without advancing
  the tier.
- A new pickup type: **Byproduct shards** (Ne, Na, Mg, etc.) that grant
  tier-specific buffs rather than fusion progress.

---

## 7. Energy / Stability System

If leveling = energy output, the player must **maintain** that output. This is
the mechanical realization of equilibrium (see [Section 4](#4-the-equilibrium-mechanic)).

### The Stability Meter

A new HUD element (alongside the existing HP bar and depth indicator) showing
the balance between **fusion output** and **gravity pressure**:

```
   FUSION ◄══════════════════════════► GRAVITY
        [████████████████░░░░░░░░░░░░]
   stable                            collapsing
```

- **Fusion output** = function of (current fuel reserves × tier fusion rate).
  High when the player has been collecting; decays when intake stops.
- **Gravity pressure** = function of tier (higher tiers = more pressure) and
  Iron accumulation (Iron adds dead weight, increasing pressure without adding
  output).
- **Stable zone:** Output ≥ Pressure. HP holds or slowly regenerates. Abilities
  at full strength.
- **Unstable zone:** Output < Pressure. HP drains, abilities weaken, collapse
  risk increases.

### Decay mechanic

**Yes, there is decay.** Fusion output is not a permanent stat — it is a rate
that reflects *current* fuel burn:

- **Fuel burn rate:** Each tier consumes fuel at a rate proportional to its
  temperature. Tier 0 (hydrogen) burns slowly; Tier 6 (silicon) burns fast.
  The player's collected element reserves deplete over time as they are "fused."
- **Output decay:** When reserves drop below a threshold, output decays. The
  player must keep collecting to maintain output.
- **Iron penalty:** Once Iron accumulates (Tier 6+), it contributes to gravity
  pressure without contributing to output. It is a one-way ratchet — Iron does
  not decay, it only builds. This is the ticking clock toward endgame.

### What "running out of fuel" means

If the player's reserves hit zero and output falls below pressure:

1. The stability meter enters the red (collapse zone).
2. HP begins draining at a rate proportional to the deficit.
3. If HP reaches zero **while in the collapse zone**, the endgame trigger fires
   (collapse event → branching choice). This is distinct from normal death
   (being killed by an enemy while stable), which triggers the existing
   respawn mechanic.

### Design intent

The stability system ensures the player can never fully "camp" or grind to
safety. Even a high-level player must keep moving and collecting. The deeper
the tier, the more demanding the upkeep. This creates escalating tension that
naturally drives toward the endgame — exactly as a star's life escalates toward
its death.

> **Open question:** Should the player be able to "vent" Iron or shed mass to
  temporarily restore stability (at a cost), or is Iron accumulation strictly
  irreversible? See [Section 9](#9-questions-for-andy).

---

## 8. Integration with Existing Systems

This section maps the progression design onto the current codebase. No rewrite
of the core engine is needed — the progression system is an **expansion** of
the existing RPG layer.

### 8.1 Stats System (`player.lua`, `combat.lua`)

**Current:**
```lua
lvl, hp, dmg, def
maxHp = 10 * lvl
dmg = 2 + lvl
def = max(0, lvl - 1)
damage = max(1, attacker.dmg - target.def)
xpThreshold = lvl * 30
```

**Proposed expansion:**

- `lvl` → retained as the universal level (1–99). Determines tier
  (`tier = floor((lvl - 1) / 14.14)` → roughly 7 tiers of ~14 levels each, or
  use explicit tier boundaries from [Section 3](#3-progression-tiers)).
- `hp` / `maxHp` → retained. `maxHp` now scales with tier *and* fuel reserves
  (a well-fueled star is "bigger"). Base: `maxHp = 10 * lvl` (keep current
  formula); bonus: `+ fuelBonus` where fuelBonus scales with current element
  reserves.
- `dmg` → retained. Scales with tier and **fusion output** (stable star hits
  harder). When unstable, `dmg` decays. Base: `dmg = 2 + lvl` (keep); effective:
  `effDmg = dmg * stabilityMultiplier` where `stabilityMultiplier` ranges
  ~0.5 (collapsing) to 1.0 (stable).
- `def` → retained. Scales with tier and **Iron accumulation** (dense core =
  more defense). Base: `def = max(0, lvl - 1)` (keep); bonus: `+ ironBonus`.
- **New stat:** `stability` (0.0–1.0) — the equilibrium ratio. Drives HP
  regen/drain and ability effectiveness.
- **New inventory:** `elements` table mapping element name → count.
  e.g. `{ H = 340, He = 120, C = 0, ... }`.
- **New stat:** `tier` (0–6) — derived from level, determines active fuel
  element and fusion reaction.

**Damage formula** (`combat.lua`) stays the same structure but uses effective
stats:
```lua
damage = max(1, attacker.effDmg - target.def)
```

### 8.2 XP / Leveling (`player.lua`)

**Current:** XP shards add to `xp`; when `xp >= lvl * 30`, level up.

**Proposed:** XP shards become **element shards**. The `xp` value is replaced
(or aliased) by the current tier's element count. Level-up occurs when the
element count reaches the tier's fusion threshold:

```lua
-- Pseudocode
function Player:addElement(elem, amount)
    self.elements[elem] = (self.elements[elem] or 0) + amount
    if elem == self.currentFuel then
        self:checkFusion()
    end
end

function Player:checkFusion()
    local threshold = FUSION_THRESHOLDS[self.tier]
    if self.elements[self.currentFuel] >= threshold then
        self:fuse()
    end
end

function Player:fuse()
    -- Consume fuel, produce byproduct, advance progress
    self.elements[self.currentFuel] = self.elements[self.currentFuel] - threshold
    local byproduct = FUSION_BYPRODUCTS[self.tier]
    self.elements[byproduct] = (self.elements[byproduct] or 0) + byproductAmount
    self.lvl = self.lvl + 1
    self:updateTier()
    self:recalcStats()
end
```

The existing `lvl * 30` threshold becomes a tier-scaled curve
(e.g. `base * tierMultiplier`).

### 8.3 Pickups (`pickup.lua`)

**Current:** Two types — heal orb (+5 HP, sensor fixture) and XP shard (+10 XP,
sensor fixture).

**Proposed:** Generalize the pickup system to carry an `element` field:

- XP shards → `element`-typed shards (`H`, `He`, `C`, …). The `+10` becomes
  `+amount` of the specified element.
- Heal orbs → unchanged mechanically; thematically "energy injection."
- New: Byproduct shards (grant buffs, not fusion progress).
- The sensor-fixture collision system in `pickup.lua` needs no structural
  change — only the `onCollect` callback branches on element type.

### 8.4 Depth-Shifting Platformer (`map.lua`, `layer.lua`, `player.lua`)

The progression system **enriches** the depth-shifting mechanic rather than
replacing it:

- **Layer-specific elements:** Different z-layers within a zone can yield
  different elements. A far layer might have diffuse Hydrogen (easy, low
  reward); a near layer might have dense Carbon deposits (hard, high reward).
  This gives the player a *progression reason* to shift layers, beyond
  navigation.
- **Tier-gated layers:** Some layers may require a minimum tier to survive
  (environmental heat/pressure scales with depth). This creates gated content
  that unlocks naturally as the player advances.
- **Layered Fusion (Tier 5 ability):** Explicitly ties fusion to layer
  mechanics — collect fuel on one layer, deliver to a reaction site on another.
- The existing W/S shift mechanic, AABB clearance check, and red-flash blocked
  indicator are all retained as-is.

### 8.5 Enemies (`enemy_skeleton.lua`)

- Skeletons remain the baseline enemy. Their drops scale with the zone's tier.
- **New enemy types** (future): element-themed enemies that are stronger but
  drop more/rarer elements. The skeleton AI (idle→chase→attack→dead, aggro
  220px) is a solid template — new enemies can subclass it.
- Enemy stats scale with tier (more HP, more damage) to match the player's
  growth, keeping combat challenging across all tiers.

### 8.6 HUD (`hud.lua`)

**Current:** HP bar, stats display, depth indicator, blocked-shift flash.

**Proposed additions:**
- **Stability meter** — the equilibrium bar (fusion ↔ gravity). Most important
  new HUD element.
- **Element inventory** — small display of current fuel element + count, and
  progress toward next fusion.
- **Tier indicator** — shows current tier name (e.g. "Red Giant") and element.
- **Iron clock** — once Iron accumulates (Tier 6), a visible indicator that
  the endgame is approaching.

### 8.7 Maps / TMX Import (`play.lua`, `tools/tmx_to_starryknight.py`)

- **MAPS table** (`play.lua`) — extend map entries with a `tier` field so the
  game knows which element tier a zone belongs to. This determines enemy drops
  and environmental pickups.
- **TMX converter** — the Python converter (`tmx_to_starryknight.py`) can use
  TMX custom properties to tag layers/maps with tier and element type. No
  structural change to the converter is needed; it's a metadata addition.
- **Zone progression:** Maps are ordered by tier. The player progresses through
  zones (hotkeys 1–8 currently switch maps for testing; in the full game, this
  becomes a progression sequence).

### 8.8 Assets (`assets.lua`)

- No images needed (placeholder rectangles, as current). Element shards can be
  color-coded using the existing palette (H = white/cyan, He = yellow, C =
  gray, O = blue, Si = brown, Fe = dark gray/red).
- The stability meter and tier indicator are drawn with `love.graphics`
  primitives, consistent with the current HUD style.

---

## 9. Questions for Andy

These are the open design questions that need Andy's input before
implementation begins. They are flagged throughout the document above.

### Q1 — Collapse drain: survivable or one-way?

When the player enters the collapse zone (fusion output < gravity pressure),
should the HP drain be **counteractable** (heal orbs / collecting fuel restores
stability and reverses the drain), or is it a **one-way ratchet** (once
collapse begins, it can only be slowed, not stopped)?

- *Survivable* = more forgiving, lets players recover from mistakes.
- *One-way* = more thematic (real stars don't un-collapse), higher stakes.

### Q2 — Endgame path: choice or consequence?

Should the Supernova vs. Dwarf endgame branch be:

- **Pure player choice** at the moment of collapse (player picks regardless of
  stats)?
- **Determined by accumulated mass** (total elements / tier reached forces the
  outcome — a "massive" player must go supernova)?
- **Hybrid** (mass determines which options are *available*; player chooses
  among them)?

### Q3 — Iron: reversible or permanent?

Can the player shed Iron or vent mass to temporarily restore stability (at a
cost — e.g. losing levels or stats), or is Iron accumulation strictly
irreversible (the clock only ticks forward)?

### Q4 — Tier boundaries and level ranges

The tier/level ranges in [Section 3](#3-progression-tiers) are proposed
roughly. Are these the right boundaries, or does Andy have a specific vision
for how many levels each tier should span? Should the total level cap be 99,
or open-ended?

### Q5 — Endgame as "end" or "new game+"?

After the player goes Supernova or becomes a Dwarf, is that the **end of the
game** (a finale), or does it unlock a **new game mode / loop** that continues
indefinitely? E.g.:

- Supernova → replay as a remnant with forged heavy elements?
- Dwarf → endless survival mode?
- Neutron Star / Black Hole → a true "win" state or an endless power fantasy?

### Q6 — Byproduct depth

In Tier 3 (Carbon Burning), byproducts (Ne, Na, Mg) grant buffs. How deep
should this go? Are byproducts just minor stat mods, or should they be a full
build-customization system (selectable loadouts, synergies, etc.)?

### Q7 — Layer-element mapping

Should element types be **strictly tied to z-layers** (far = light elements,
near = heavy), or should it be **zone/map-dependent** with layers as a
secondary factor? This affects how much the progression system drives
depth-shifting vs. zone progression.

### Q8 — Death vs. collapse

The document distinguishes "normal death" (killed by enemy while stable →
respawn) from "collapse" (stability failure → endgame trigger). Is this the
right distinction, or should *all* death funnel through the stability system?
Does the player have lives / a respawn limit, or is it a roguelike
one-death-and-done?

### Q9 — Tone and narrative

Is there a narrative wrapper around this (why is the star a knight? is there a
quest?), or is the progression purely mechanical with the metaphor speaking for
itself? This affects how much UI/text scaffolding the system needs.

### Q10 — Scope for first implementation

For a first playable version of the progression system, which of these is the
priority?

1. Tier 0–1 only (Hydrogen → Helium, basic equilibrium)?
2. Full tier chain but without endgame branching?
3. Full chain + endgame branching (complete vertical slice)?

---

## Appendix A — Element Reference

For implementation, the fusion chain and its game mappings:

| # | Element | Symbol | Tier | Role | Fusion Product |
|---|---------|--------|------|------|----------------|
| 1 | Hydrogen | H | 0–1 | Fuel (main sequence) | Helium |
| 2 | Helium | He | 2 | Fuel (red giant) | Carbon, Oxygen |
| 3 | Carbon | C | 3 | Fuel (carbon burning) | Neon, Sodium, Magnesium |
| 4 | Neon | Ne | 4 | Fuel (neon burning) | Oxygen, Silicon |
| 5 | Oxygen | O | 5 | Fuel (oxygen burning) | Silicon, Sulfur |
| 6 | Silicon | Si | 6 | Fuel (silicon burning) | Iron |
| 7 | Iron | Fe | 6+ | Dead weight (endgame trigger) | — (fusion energy-negative) |
| — | Gold, Uranium, etc. | various | endgame | Supernova forged drops | — |

## Appendix B — Proposed Stat Scaling (Draft)

```
Tier 0 (L1–10):   maxHp = 10*lvl,      dmg = 2+lvl,     def = max(0,lvl-1),  stab ~1.0
Tier 1 (L11–25):  maxHp = 10*lvl+fuel,  dmg = 2+lvl,     def = max(0,lvl-1),  stab decays if idle
Tier 2 (L26–45):  maxHp += tier bonus,  dmg += aura,     def += tier,         ranged attack unlocked
Tier 3 (L46–65):  byproduct mods apply (speed/defense/reactive dmg)
Tier 4 (L66–80):  burst mechanic (compress → +dmg, -stab), def scales sharply
Tier 5 (L81–90):  cross-layer fusion, dmg scales with layer synergy
Tier 6 (L91–99):  def = max, dmg declining, iron accumulation → collapse clock
Endgame:          Supernova (burst mode) OR Dwarf (tank mode) — permanent
```

---

*This document is a living design spec. Once Andy answers the questions in
[Section 9](#9-questions-for-andy), it will be updated and frozen for
implementation.*
