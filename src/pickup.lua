local P      = require("src.physics")
local Assets = require("src.assets")

local Pickup = {}
Pickup.__index = Pickup

local W, H = 16, 16

-- kind: "heal" | "xp"
function Pickup.new(layer, x, y, kind)
  local self = setmetatable({}, Pickup)
  self.kind = kind
  self.layer = layer
  self.w, self.h = W, H
  self.consumed = false
  self.t = 0
  self.body, self.fixture = P.new_sensor(
    layer.world, x, y, W, H, { kind = "pickup", ref = self }
  )
  return self
end

function Pickup:aabb()
  if not self.body then return 0, 0, 0, 0 end
  local cx, cy = self.body:getX(), self.body:getY()
  return cx - self.w * 0.5, cy - self.h * 0.5, self.w, self.h
end

local function aabb_overlap(ax, ay, aw, ah, bx, by, bw, bh)
  return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by
end

function Pickup:update_active(dt, game)
  if self.consumed then return end
  self.t = self.t + dt
  local p = game.player
  if not p or not p.body then return end
  -- player AABB in world coords (top-left)
  local px = p.body:getX() - p.w * 0.5
  local py = p.body:getY() - p.h * 0.5
  local ax, ay, aw, ah = self:aabb()
  if aabb_overlap(ax, ay, aw, ah, px, py, p.w, p.h) then
    if self.kind == "heal" then
      p:heal(5)
      game.combat:add_number(ax, ay, "+5 HP", { 0.3, 1.0, 0.4 })
    elseif self.kind == "xp" then
      p:gain_xp(10)
      game.combat:add_number(ax, ay, "+10 XP", { 0.4, 0.75, 1.0 })
    end
    self.consumed = true
    if self.body then
      self.body:destroy()
      self.body = nil
    end
  end
end

function Pickup:update_inactive(dt)
  if not self.consumed then self.t = self.t + dt end
end

-- Caller has already translated by -camera (with the appropriate parallax).
function Pickup:draw(alpha)
  if self.consumed or not self.body then return end
  local x, y = self.body:getX(), self.body:getY()
  local bob = math.sin(self.t * 4) * 3
  local c = (self.kind == "heal") and Assets.colors.pickup_hp or Assets.colors.pickup_xp
  love.graphics.setColor(c[1], c[2], c[3], alpha)
  love.graphics.circle("fill", x, y + bob, 7)
  love.graphics.setColor(1, 1, 1, alpha * 0.7)
  love.graphics.circle("line", x, y + bob, 7)
end

return Pickup
