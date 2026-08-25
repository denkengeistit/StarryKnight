-- Visual constants. No image loading in v0; placeholder colored rectangles.
local Assets = {}

Assets.colors = {
  sky        = {0.05, 0.06, 0.10},
  tile_far   = {0.32, 0.32, 0.45},
  tile_mid   = {0.55, 0.55, 0.55},
  tile_near  = {0.40, 0.58, 0.42},
  player     = {0.95, 0.82, 0.32},
  skeleton   = {0.85, 0.85, 0.80},
  pickup_hp  = {0.95, 0.25, 0.32},
  pickup_xp  = {0.32, 0.80, 0.95},
  hitbox     = {1, 1, 1, 0.30},
  hud_text   = {0.92, 0.92, 0.92},
  hud_hp     = {0.88, 0.16, 0.20},
  hud_hp_bg  = {0.20, 0.05, 0.05},
  hud_xp     = {0.32, 0.85, 0.95},
  flash      = {1, 0.20, 0.20},
}

Assets.fonts = {}

function Assets.load()
  Assets.fonts.small  = love.graphics.newFont(10)
  Assets.fonts.normal = love.graphics.newFont(12)
  Assets.fonts.big    = love.graphics.newFont(20)
end

return Assets
