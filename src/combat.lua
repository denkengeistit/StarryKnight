-- The entire RPG math fits on one screen.
local Assets = require("src.assets")

local Combat = {}
Combat.__index = Combat

function Combat.new()
  local self = setmetatable({}, Combat)
  self.numbers = {}
  return self
end

-- Damage application. Returns the actual damage dealt.
function Combat.damage(attacker, target)
  local d = math.max(1, (attacker.dmg or 1) - (target.def or 0))
  target.hp = (target.hp or 0) - d
  if target.hp < 0 then target.hp = 0 end
  return d
end

function Combat:add_number(world_x, world_y, text, color)
  table.insert(self.numbers, {
    x = world_x,
    y = world_y,
    text = tostring(text),
    t = 0.9,
    vy = -36,
    color = color or {1, 1, 1},
  })
end

function Combat:update(dt)
  for i = #self.numbers, 1, -1 do
    local fn = self.numbers[i]
    fn.t = fn.t - dt
    fn.y = fn.y + fn.vy * dt
    fn.vy = fn.vy + 28 * dt
    if fn.t <= 0 then
      table.remove(self.numbers, i)
    end
  end
end

-- Caller must have already translated by -camera.x, -camera.y
function Combat:draw_inworld()
  love.graphics.setFont(Assets.fonts.normal)
  for _, fn in ipairs(self.numbers) do
    local a = math.min(1, fn.t * 2)
    love.graphics.setColor(fn.color[1], fn.color[2], fn.color[3], a)
    love.graphics.print(fn.text, fn.x, fn.y)
  end
  love.graphics.setColor(1, 1, 1, 1)
end

return Combat
