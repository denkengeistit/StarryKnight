-- Tile types. v0 keeps it minimal: empty / solid.
local Tile = {}

Tile.EMPTY  = 0
Tile.SOLID  = 1
Tile.HAZARD = 3

function Tile.is_solid(t)
  return t == Tile.SOLID
end

function Tile.is_blocking(t)
  -- For shift-AABB checks: anything that would crush the player.
  return t == Tile.SOLID
end

return Tile
