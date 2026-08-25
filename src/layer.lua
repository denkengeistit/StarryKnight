-- A single z-depth strip: tiles, entities, its own Box2D world.
local P      = require("src.physics")
local Tile   = require("src.tile")
local Skel   = require("src.enemy_skeleton")
local Pickup = require("src.pickup")

local Layer = {}
Layer.__index = Layer

-- Convert a multi-line string description to a 2D tile array.
-- '#' = SOLID, anything else = EMPTY.
local function parse_tile_string(str)
  local rows = {}
  for line in str:gmatch("[^\r\n]+") do
    local row = {}
    for i = 1, #line do
      local c = line:sub(i, i)
      row[i] = (c == "#") and Tile.SOLID or Tile.EMPTY
    end
    table.insert(rows, row)
  end
  return rows
end

function Layer.new(name, data)
  local self = setmetatable({}, Layer)
  self.name      = name
  self.tilesize  = data.tilesize or 32

  if type(data.tiles) == "string" then
    self.tiles = parse_tile_string(data.tiles)
  else
    self.tiles = data.tiles or {}
  end
  self.height = #self.tiles
  self.width  = 0
  for _, row in ipairs(self.tiles) do
    if #row > self.width then self.width = #row end
  end

  self.tile_color = data.tile_color or { 0.5, 0.5, 0.5 }
  self.bg_color   = data.bg_color   or { 0.07, 0.07, 0.10 }
  self.spawn      = data.spawn      or { x = 64, y = 64 }
  -- NOTE: parallax/dim are no longer stored here; Play.draw derives them from
  -- each layer's distance to the active slice so the same code handles 2-5
  -- layers without per-map tuning.

  self.world = P.new_world(0, 1500)
  self.entities = { enemies = {}, pickups = {} }

  self:_build_tiles()
  self:_spawn_entities(data.entities or {})
  return self
end

-- Per-tile static bodies create vertical "ghost edges" between adjacent floor
-- tiles that Box2D occasionally registers as wall collisions, killing
-- horizontal velocity for a tick (the player snags on a flat floor and has to
-- jump to unstick). Merging each row's contiguous run of solid tiles into one
-- long static body removes those internal seams entirely.
function Layer:_build_tiles()
  local ts = self.tilesize
  for y, row in ipairs(self.tiles) do
    local run_start = nil
    for x = 1, #row + 1 do
      local solid = (x <= #row) and Tile.is_solid(row[x])
      if solid then
        if not run_start then run_start = x end
      elseif run_start then
        local px = (run_start - 1) * ts
        local py = (y - 1) * ts
        local pw = (x - run_start) * ts
        P.new_static_box(self.world, px, py, pw, ts,
                         { kind = "tile", x0 = run_start, x1 = x - 1, y = y })
        run_start = nil
      end
    end
  end
end

function Layer:_spawn_entities(list)
  for _, e in ipairs(list) do
    if e.type == "skeleton" then
      table.insert(self.entities.enemies, Skel.new(self, e.x, e.y, e.lvl or 1))
    elseif e.type == "heal" or e.type == "xp" then
      table.insert(self.entities.pickups, Pickup.new(self, e.x, e.y, e.type))
    end
  end
end

function Layer:tile_at(tx, ty)
  local row = self.tiles[ty]
  if not row then return Tile.EMPTY end
  return row[tx] or Tile.EMPTY
end

-- AABB overlap (top-left world coords) against this layer's solid tiles.
function Layer:tile_blocks_aabb(x, y, w, h)
  local ts = self.tilesize
  local x0 = math.floor(x / ts) + 1
  local y0 = math.floor(y / ts) + 1
  local x1 = math.floor((x + w - 1) / ts) + 1
  local y1 = math.floor((y + h - 1) / ts) + 1
  for ty = y0, y1 do
    for tx = x0, x1 do
      if Tile.is_blocking(self:tile_at(tx, ty)) then
        return true
      end
    end
  end
  return false
end

function Layer:update(dt, game)
  self.world:update(dt)
  for _, e in ipairs(self.entities.enemies) do
    e:update_active(dt, game)
  end
  for _, p in ipairs(self.entities.pickups) do
    p:update_active(dt, game)
  end
end

function Layer:update_inactive(dt)
  -- Still tick world for consistent state (gravity, settling).
  self.world:update(dt)
  for _, e in ipairs(self.entities.enemies) do e:update_inactive(dt) end
  for _, p in ipairs(self.entities.pickups) do p:update_inactive(dt) end
end

-- Caller has already pushed the right camera transform with this layer's parallax.
function Layer:draw_tiles(alpha)
  local ts = self.tilesize
  local c  = self.tile_color
  love.graphics.setColor(c[1], c[2], c[3], alpha)
  for y, row in ipairs(self.tiles) do
    for x = 1, #row do
      if Tile.is_solid(row[x]) then
        love.graphics.rectangle("fill", (x - 1) * ts, (y - 1) * ts, ts, ts)
      end
    end
  end
end

function Layer:draw_entities(alpha)
  for _, e in ipairs(self.entities.enemies) do e:draw(alpha) end
  for _, p in ipairs(self.entities.pickups) do p:draw(alpha) end
end

return Layer
