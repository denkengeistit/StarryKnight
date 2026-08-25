-- Thin wrappers around love.physics (Box2D) so callers don't repeat boilerplate.
-- All `x, y` arguments here are TOP-LEFT of the box; we offset to center for Box2D.
local P = {}

function P.new_world(gx, gy)
  return love.physics.newWorld(gx or 0, gy or 1500, true)
end

function P.new_static_box(world, x, y, w, h, userdata)
  local body = love.physics.newBody(world, x + w * 0.5, y + h * 0.5, "static")
  local shape = love.physics.newRectangleShape(w, h)
  local fixture = love.physics.newFixture(body, shape)
  fixture:setFriction(0)
  if userdata then fixture:setUserData(userdata) end
  return body, fixture
end

function P.new_dynamic_box(world, x, y, w, h, userdata)
  local body = love.physics.newBody(world, x + w * 0.5, y + h * 0.5, "dynamic")
  body:setFixedRotation(true)
  local shape = love.physics.newRectangleShape(w, h)
  local fixture = love.physics.newFixture(body, shape, 1)
  fixture:setFriction(0)
  if userdata then fixture:setUserData(userdata) end
  return body, fixture
end

function P.new_sensor(world, x, y, w, h, userdata)
  local body = love.physics.newBody(world, x + w * 0.5, y + h * 0.5, "static")
  local shape = love.physics.newRectangleShape(w, h)
  local fixture = love.physics.newFixture(body, shape)
  fixture:setSensor(true)
  if userdata then fixture:setUserData(userdata) end
  return body, fixture
end

return P
