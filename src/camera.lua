-- Simple follow-camera in world space. Parallax is applied at draw time by Layer,
-- so this module only tracks one "true" camera position.
local Camera = {}
Camera.__index = Camera

function Camera.new()
  local self = setmetatable({}, Camera)
  self.x, self.y   = 0, 0
  self.tx, self.ty = 0, 0
  self.lerp = 10
  self.vw, self.vh = love.graphics.getDimensions()
  return self
end

function Camera:follow(world_x, world_y)
  self.tx = world_x - self.vw * 0.5
  self.ty = world_y - self.vh * 0.6
end

function Camera:update(dt)
  local a = 1 - math.exp(-self.lerp * dt)
  self.x = self.x + (self.tx - self.x) * a
  self.y = self.y + (self.ty - self.y) * a
end

function Camera:snap(world_x, world_y)
  self.tx = world_x - self.vw * 0.5
  self.ty = world_y - self.vh * 0.6
  self.x, self.y = self.tx, self.ty
end

return Camera
