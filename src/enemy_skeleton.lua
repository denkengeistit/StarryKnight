local P      = require("src.physics")
local Assets = require("src.assets")
local Combat = require("src.combat")

local Skel = {}
Skel.__index = Skel

local W, H = 18, 28
local SPEED = 70
local AGGRO_DIST = 220
local ATTACK_DIST = 26

function Skel.new(layer, x, y, lvl)
  local self = setmetatable({}, Skel)
  self.layer = layer
  self.w, self.h = W, H
  self.lvl  = lvl or 1
  self.maxHp = 10 * self.lvl
  self.hp   = self.maxHp
  self.dmg  = 2 + self.lvl
  self.def  = math.max(0, self.lvl - 1)
  self.xp_reward = 10
  self.dead = false
  self.facing = -1
  self.attack_cd = 0
  self.body, self.fixture = P.new_dynamic_box(
    layer.world, x, y, W, H, { kind = "enemy", ref = self }
  )
  self.body:setLinearDamping(6)
  -- Share the same negative group index as the player so they don't physically
  -- collide; combat is handled via AABB checks in update().
  self.fixture:setGroupIndex(-2)
  return self
end

function Skel:aabb()
  if not self.body then return 0, 0, 0, 0 end
  local cx, cy = self.body:getX(), self.body:getY()
  return cx - self.w * 0.5, cy - self.h * 0.5, self.w, self.h
end

function Skel:on_hit(facing)
  if self.dead or not self.body then return end
  self.body:applyLinearImpulse(120 * (facing or 1) * self.body:getMass(), -150)
  if self.hp <= 0 then self:die() end
end

function Skel:die()
  self.dead = true
  if self.body then
    self.body:destroy()
    self.body = nil
  end
end

function Skel:update_active(dt, game)
  if self.dead then return end
  local p = game.player
  if not p or not p.body then return end
  local px, py = p.body:getX(), p.body:getY()
  local mx, my = self.body:getX(), self.body:getY()
  local dx = px - mx
  local adx = math.abs(dx)
  if self.attack_cd > 0 then self.attack_cd = self.attack_cd - dt end
  local _, vy = self.body:getLinearVelocity()
  if adx < AGGRO_DIST and math.abs(py - my) < 80 then
    self.facing = (dx > 0) and 1 or -1
    if adx > ATTACK_DIST then
      self.body:setLinearVelocity(self.facing * SPEED, vy)
    else
      self.body:setLinearVelocity(0, vy)
      if self.attack_cd <= 0 then
        self.attack_cd = 0.9
        local dmg = Combat.damage(self, p)
        game.combat:add_number(px - 8, py - 24, dmg, { 1.0, 0.45, 0.45 })
        p:on_hit(self.facing)
        game.shake.t = 0.15
      end
    end
  else
    self.body:setLinearVelocity(0, vy)
  end
end

function Skel:update_inactive(dt)
  -- Body still ticks via Box2D (gravity). No AI / damage exchange.
end

-- Caller has already translated by -camera (with appropriate parallax).
function Skel:draw(alpha)
  if self.dead or not self.body then return end
  local x = self.body:getX() - self.w * 0.5
  local y = self.body:getY() - self.h * 0.5
  local c = Assets.colors.skeleton
  love.graphics.setColor(c[1], c[2], c[3], alpha)
  love.graphics.rectangle("fill", x, y, self.w, self.h)
  -- eyes (a little flavor)
  love.graphics.setColor(0.1, 0.1, 0.1, alpha)
  love.graphics.rectangle("fill", x + 4,  y + 8, 3, 3)
  love.graphics.rectangle("fill", x + 11, y + 8, 3, 3)
  -- hp bar
  local frac = (self.maxHp > 0) and math.max(0, self.hp / self.maxHp) or 0
  love.graphics.setColor(0, 0, 0, alpha * 0.6)
  love.graphics.rectangle("fill", x, y - 6, self.w, 3)
  love.graphics.setColor(0.9, 0.2, 0.2, alpha)
  love.graphics.rectangle("fill", x, y - 6, self.w * frac, 3)
  love.graphics.setColor(1, 1, 1, 1)
end

return Skel
