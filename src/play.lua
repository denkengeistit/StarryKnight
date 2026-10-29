-- The actual gameplay state: ties Map / Player / Camera / Combat / HUD together
-- and handles draw ordering. Layers are drawn back-to-front (index 1 = farthest
-- from camera, index N = closest). Parallax and dim are computed dynamically
-- from each layer's signed distance to the active depth, so the same logic
-- works for any map with 2+ slices.
local Assets = require("src.assets")
local Map    = require("src.map")
local Player = require("src.player")
local Camera = require("src.camera")
local Combat = require("src.combat")
local Hud    = require("src.hud")

local Play = {}

-- Per-step falloff away from the active slice.
--   PARALLAX_STEP : horizontal scroll-rate change per layer of depth.
--   ALPHA_STEP    : how fast inactive layers dim out.
--   Y_OFFSET_STEP   : vertical screen-space shift per layer of depth.
--   X_OFFSET_STEP   : horizontal screen-space shift per layer of depth.
--                   Deeper layers (lower index than active) render slightly
--                   HIGHER and RIGHT on screen; closer layers (higher index) render
--                   slightly LOWER and LEFT. Gives a pseudo-3D "shifted horizon"
--                   feel, like a top-down ARPG world tilted toward the camera.
local PARALLAX_STEP = 0
local ALPHA_STEP    = 0.22
local X_OFFSET_STEP = -18
local Y_OFFSET_STEP = 18
local MIN_ALPHA     = 0.25
-- With many layers (iso-strip maps) only the active layer and this many
-- neighbours each side are drawn; the rest would be invisible or off-screen.
local DRAW_RADIUS   = 2

local function depth_factors(i, active)
  if i == active then return 1.0, 1.0, 0, 0 end
  local dist = i - active   -- negative = farther from camera; positive = closer
  local parallax = 1.0 + dist * PARALLAX_STEP
  local alpha    = math.max(MIN_ALPHA, 1.0 - math.abs(dist) * ALPHA_STEP)
  local x_offset = dist * X_OFFSET_STEP
  local y_offset = dist * Y_OFFSET_STEP
  return parallax, alpha, x_offset, y_offset
end

-- Map registry: which module path each hotkey loads.
local MAPS = {
  ["1"] = "assets.maps.cliffside_02", -- 4 slices
  ["3"] = "assets.maps.iso_demo",     -- 7 strips from an iso map
  ["9"] = "assets.maps.test_basic",
  ["4"] = "assets.maps.stress_two_layer",
  ["5"] = "assets.maps.stress_three_layer",
  ["6"] = "assets.maps.stress_five_layer",
  ["7"] = "assets.maps.stress_mixed_matching",
  ["8"] = "assets.maps.stress_large_map",
}

local game
local current_map_path = MAPS["3"]

local function load_map(path)
  -- Drop Lua's cached copy of the map module so hot-edited map files take
  -- effect immediately on reload (useful while iterating on tile layouts).
  package.loaded[path] = nil
  current_map_path = path

  game = {
    map    = Map.new(path),
    camera = Camera.new(),
    combat = Combat.new(),
    shake  = { t = 0 },
    flash  = { t = 0 },
  }

  local spawn_layer = game.map:active_layer()
  local sp = spawn_layer.spawn
  game.player = Player.new(spawn_layer, sp.x, sp.y)
  game.camera:snap(game.player.body:getX(), game.player.body:getY())
end

function Play.load()
  Assets.load()
  load_map(current_map_path)
end

function Play.update(dt)
  local active = game.map.active
  for i, layer in ipairs(game.map.layers) do
    if i == active then
      layer:update(dt, game)
    else
      layer:update_inactive(dt)
    end
  end

  game.player:update(dt, game)
  game.combat:update(dt)

  if game.player.body then
    game.camera:follow(game.player.body:getX(), game.player.body:getY())
  end
  game.camera:update(dt)

  if game.shake.t > 0 then
    game.shake.t = math.max(0, game.shake.t - dt)
  end
  if game.flash.t > 0 then
    game.flash.t = math.max(0, game.flash.t - dt)
  end
end

function Play.draw()
  love.graphics.clear(Assets.colors.sky)

  local sx, sy = 0, 0
  if game.shake.t > 0 then
    local mag = 6 * (game.shake.t / 0.15)
    sx = (math.random() - 0.5) * mag * 2
    sy = (math.random() - 0.5) * mag * 2
  end
  love.graphics.push()
  love.graphics.translate(sx, sy)

  local active = game.map.active
  for i, layer in ipairs(game.map.layers) do
    -- love.js runs PUC Lua 5.1 (no goto), so guard with if instead of goto continue.
    if math.abs(i - active) <= DRAW_RADIUS then
      local parallax, alpha, x_offset, y_offset = depth_factors(i, active)
      love.graphics.push()
      love.graphics.translate(
        -game.camera.x * parallax + x_offset,
        -game.camera.y * parallax + y_offset
      )
      layer:draw_tiles(alpha)
      layer:draw_entities(alpha)
      if i == active then
        game.player:draw()
        game.combat:draw_inworld()
      end
      love.graphics.pop()
    end
  end

  love.graphics.pop()

  Hud.draw(game)
end

function Play.keypressed(key)
  -- Map switching / reload hotkeys take precedence over player input.
  if MAPS[key] then
    load_map(MAPS[key])
    return
  elseif key == "r" then
    load_map(current_map_path)
    return
  end
  game.player:keypressed(key, game)
end

function Play.keyreleased(key)
  -- nothing for v0
end

return Play
