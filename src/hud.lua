-- Top-left HP/LVL/XP stats; top-right depth indicator (one cell per slice).
local Assets = require("src.assets")

local Hud = {}

function Hud.draw(game)
  local p = game.player
  local w, h = love.graphics.getDimensions()

  -- HP bar
  local bx, by, bw, bh = 16, 16, 220, 18
  love.graphics.setColor(Assets.colors.hud_hp_bg)
  love.graphics.rectangle("fill", bx, by, bw, bh)
  local frac = (p.maxHp > 0) and math.max(0, p.hp / p.maxHp) or 0
  love.graphics.setColor(Assets.colors.hud_hp)
  love.graphics.rectangle("fill", bx, by, bw * frac, bh)
  love.graphics.setColor(Assets.colors.hud_text)
  love.graphics.rectangle("line", bx, by, bw, bh)
  love.graphics.setFont(Assets.fonts.normal)
  love.graphics.print(string.format("HP %d/%d", p.hp, p.maxHp), bx + 6, by + 2)

  -- LVL/XP/DMG/DEF line
  love.graphics.print(
    string.format("LVL %d   XP %d/%d   DMG %d   DEF %d",
                  p.lvl, p.xp, p.lvl * 30, p.dmg, p.def),
    bx, by + bh + 6
  )

  -- Depth indicator: one cell per layer, ordered far-to-near.
  local layers = game.map.layers
  local n = #layers
  local dw, dh, gap = 22, 40, 6
  local total = (n * dw) + ((n - 1) * gap)
  local dx0 = w - 16 - total
  local dy = 16
  love.graphics.setFont(Assets.fonts.small)
  for i, layer in ipairs(layers) do
    local x = dx0 + (i - 1) * (dw + gap)
    local active = (i == game.map.active)
    if active then
      love.graphics.setColor(0.95, 0.95, 1.0, 1)
    else
      love.graphics.setColor(0.30, 0.30, 0.40, 1)
    end
    love.graphics.rectangle("fill", x, dy, dw, dh)
    love.graphics.setColor(0.05, 0.05, 0.08, 1)
    love.graphics.rectangle("line", x, dy, dw, dh)
    love.graphics.setColor(active and {0.05,0.05,0.08} or {0.7,0.7,0.8})
    love.graphics.printf(layer.name or tostring(i), x, dy + dh + 3, dw, "center")
  end

  -- Blocked-shift red flash overlay on the depth indicator
  if game.flash.t > 0 then
    local a = math.min(1, game.flash.t / 0.4) * 0.45
    love.graphics.setColor(Assets.colors.flash[1], Assets.colors.flash[2], Assets.colors.flash[3], a)
    love.graphics.rectangle("fill", dx0 - 4, dy - 4, total + 8, dh + 22)
  end

  -- Controls hint
  love.graphics.setColor(0.7, 0.7, 0.75, 0.7)
  love.graphics.setFont(Assets.fonts.small)
  love.graphics.print(
    "A/D move   SPACE jump   J attack   W/S shift depth   1/2 maps   R reload   ESC quit",
    16, h - 20
  )

  love.graphics.setColor(1, 1, 1, 1)
end

return Hud
