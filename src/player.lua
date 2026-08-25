local P      = require("src.physics")
local Assets = require("src.assets")
local Combat = require("src.combat")

local Player = {}
Player.__index = Player

local W, H = 18, 28
local MOVE_SPEED   = 220
local JUMP_VEL     = -380  -- y-velocity injected on jump (negative = up)
local SWING_W, SWING_H = 26, 28

-- Layer ordering is just an integer index into Map.layers:
--   index 1     = farthest from camera ("far" direction)
--   index N     = closest to camera   ("near" direction)
-- request_shift uses dir = -1 to step toward 1, dir = +1 to step toward N.

function Player.new(layer, world_x, world_y)
  local self = setmetatable({}, Player)
  self.w, self.h = W, H

  self.lvl = 1
  self.xp  = 0
  self:derive_stats()
  self.hp  = self.maxHp

  self.facing       = 1
  self.grounded     = false
  self.attack_timer = 0   -- visual swing duration
  self.attack_cd    = 0
  self.hit_cd       = 0

  self:spawn_in_layer(layer, world_x, world_y)
  return self
end

function Player:derive_stats()
  self.maxHp = 10 * self.lvl
  self.dmg   = 2 + self.lvl
  self.def   = math.max(0, self.lvl - 1)
end

-- world_x, world_y = top-left of the desired body
function Player:spawn_in_layer(layer, world_x, world_y)
  self.layer = layer
  self.body, self.fixture = P.new_dynamic_box(
    layer.world, world_x, world_y, W, H, { kind = "player", ref = self }
  )
  self.body:setLinearDamping(0)  -- we set velocity directly, damping unused
  -- Negative group index = never physically collide with same-group fixtures.
  -- Combat hit detection uses AABB checks in update(), not contacts, so this
  -- lets the player walk through enemies without being walled off by them.
  self.fixture:setGroupIndex(-2)
end

function Player:destroy_body()
  if self.body then
    self.body:destroy()
    self.body = nil
    self.fixture = nil
  end
end

function Player:aabb()
  if not self.body then return 0, 0, 0, 0 end
  local cx, cy = self.body:getX(), self.body:getY()
  return cx - self.w * 0.5, cy - self.h * 0.5, self.w, self.h
end

function Player:update(dt, game)
  if not self.body then return end
  local k = love.keyboard
  local j = love.joystick

  local move = 0
  -- Keyboard movement
  if k.isDown("a") or k.isDown("left")  then move = move - 1 end
  if k.isDown("d") or k.isDown("right") then move = move + 1 end

  -- Joystick movement
  if j.getJoysticks()[1] then
    local axis_x = j.getGamepadAxis(j.getJoysticks()[1], "leftx")
    if math.abs(axis_x) > 0.3 then -- deadzone
      move = axis_x
    end
  end

  if move ~= 0 then self.facing = (move > 0 and 1 or -1) end

  local _, vy = self.body:getLinearVelocity()
  self.body:setLinearVelocity(move * MOVE_SPEED, vy)

  self:update_grounded()

  if self.attack_timer > 0 then self.attack_timer = self.attack_timer - dt end
  if self.attack_cd    > 0 then self.attack_cd    = self.attack_cd    - dt end
  if self.hit_cd       > 0 then self.hit_cd       = self.hit_cd       - dt end

  -- Pit / off-world recovery
  if self.body:getY() > 2000 then
    self:respawn()
  end

  -- Death respawn
  if self.hp <= 0 then
    self:respawn()
  end
end

function Player:update_grounded()
  self.grounded = false
  if not self.body then return end
  for _, c in ipairs(self.body:getContacts()) do
    if c:isTouching() then
      local f1, _ = c:getFixtures()
      local _, ny = c:getNormal()
      -- Box2D contact normal points from fixture A to fixture B.
      -- LÖVE has +Y pointing DOWN, so when we (A) are standing on a tile (B),
      -- the normal points down into B, i.e. ny > 0. If we are B instead, the
      -- normal points up out of us toward A, i.e. ny < 0 → flip sign.
      local self_is_a = (f1 == self.fixture)
      local sy = self_is_a and ny or -ny
      if sy > 0.5 then
        self.grounded = true
        break
      end
    end
  end
end

function Player:respawn()
  local sp = self.layer.spawn or { x = 64, y = 64 }
  self:destroy_body()
  self:spawn_in_layer(self.layer, sp.x, sp.y)
  self.hp = self.maxHp
end

function Player:keypressed(key, game)
  if key == "space" or (love.joystick.getJoysticks()[1] and love.joystick.getGamepadButton(love.joystick.getJoysticks()[1], "a")) then
    if self.grounded and self.body then
      local vx, _ = self.body:getLinearVelocity()
      self.body:setLinearVelocity(vx, JUMP_VEL)
    end
  elseif key == "j" or (love.joystick.getJoysticks()[1] and love.joystick.getGamepadButton(love.joystick.getJoysticks()[1], "x")) then
    if self.attack_cd <= 0 then
      self.attack_timer = 0.18
      self.attack_cd    = 0.32
      self:do_attack(game)
    end
  elseif key == "w" or (love.joystick.getJoysticks()[1] and love.joystick.getGamepadButton(love.joystick.getJoysticks()[1], "left")) then
    self:request_shift(game, -1)
  elseif key == "s" or (love.joystick.getJoysticks()[1] and love.joystick.getGamepadButton(love.joystick.getJoysticks()[1], "right")) then
    self:request_shift(game,  1)
  end
end

function Player:do_attack(game)
  if not self.body then return end
  local px, py = self.body:getX(), self.body:getY()
  local sx
  if self.facing > 0 then
    sx = px + self.w * 0.5
  else
    sx = px - self.w * 0.5 - SWING_W
  end
  local sy = py - self.h * 0.5

  for _, e in ipairs(self.layer.entities.enemies) do
    if not e.dead and e.body then
      local ex, ey, ew, eh = e:aabb()
      if ex < sx + SWING_W and ex + ew > sx and ey < sy + SWING_H and ey + eh > sy then
        local d = Combat.damage(self, e)
        game.combat:add_number(ex + ew * 0.5 - 6, ey - 4, d, { 1, 0.85, 0.30 })
        e:on_hit(self.facing)
        game.shake.t = 0.12
        if e.dead then
          self:gain_xp(e.xp_reward or 10)
          game.combat:add_number(ex, ey - 18, "+" .. (e.xp_reward or 10) .. " XP",
                                 { 0.4, 0.75, 1.0 })
        end
      end
    end
  end
end

function Player:on_hit(facing_of_attacker)
  if self.hit_cd > 0 or not self.body then return end
  self.hit_cd = 0.55
  self.body:applyLinearImpulse(150 * (facing_of_attacker or 1) * self.body:getMass(), -120)
end

function Player:heal(n)
  self.hp = math.min(self.maxHp, self.hp + n)
end

function Player:gain_xp(n)
  self.xp = self.xp + n
  local need = self.lvl * 30
  while self.xp >= need do
    self.xp = self.xp - need
    self.lvl = self.lvl + 1
    self:derive_stats()
    self.hp = self.maxHp
    need = self.lvl * 30
  end
end

-- dir = -1 toward index 1 (farther from camera), +1 toward index N (closer).
function Player:request_shift(game, dir)
  local cur_idx = game.map.active
  local tgt_idx = cur_idx + dir
  if tgt_idx < 1 or tgt_idx > game.map:layer_count() then
    -- Already at the edge of the stack.
    game.flash.t = 0.4
    return
  end
  local tgt = game.map.layers[tgt_idx]
  if not self.body then return end
  local px = self.body:getX() - self.w * 0.5
  local py = self.body:getY() - self.h * 0.5
  if tgt:tile_blocks_aabb(px, py, self.w, self.h) then
    game.flash.t = 0.4
    game.shake.t = 0.08
    return
  end
  local vx, vy = self.body:getLinearVelocity()
  self:destroy_body()
  self:spawn_in_layer(tgt, px, py)
  self.body:setLinearVelocity(vx, vy)
  game.map.active = tgt_idx
end

-- Caller has already translated by -camera (full alpha when active).
function Player:draw()
  if not self.body then return end
  local x = self.body:getX() - self.w * 0.5
  local y = self.body:getY() - self.h * 0.5
  -- i-frame blink
  local alpha = 1
  if self.hit_cd > 0 then
    alpha = (math.floor(self.hit_cd * 20) % 2 == 0) and 1 or 0.4
  end
  local c = Assets.colors.player
  love.graphics.setColor(c[1], c[2], c[3], alpha)
  love.graphics.rectangle("fill", x, y, self.w, self.h)
  -- eyes
  love.graphics.setColor(0.10, 0.08, 0.05, alpha)
  local ex = (self.facing > 0) and (x + 9) or (x + 4)
  love.graphics.rectangle("fill", ex, y + 8, 4, 3)
  -- attack hitbox flash
  if self.attack_timer > 0 then
    local sw, sh = SWING_W, SWING_H
    local sx
    if self.facing > 0 then sx = x + self.w else sx = x - sw end
    love.graphics.setColor(Assets.colors.hitbox)
    love.graphics.rectangle("fill", sx, y, sw, sh)
  end
  love.graphics.setColor(1, 1, 1, 1)
end

return Player
