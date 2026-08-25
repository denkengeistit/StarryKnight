-- Map: wraps an ordered stack of parallel z-depth layers and tracks the active
-- one. Index 1 is the farthest from camera, index N is closest. Maps can have
-- between MIN_LAYERS and MAX_LAYERS slices, giving zone widths some variety
-- (like a real isometric ARPG world where some rooms are narrow and others
-- broad).
local Layer = require("src.layer")

local Map = {}
Map.__index = Map

Map.MIN_LAYERS = 2
Map.MAX_LAYERS = 5

function Map.new(path)
  local def = require(path)
  local self = setmetatable({}, Map)

  local list = def.layers
  assert(type(list) == "table",
    "Map " .. path .. " must define a 'layers' array")
  local n = #list
  assert(n >= Map.MIN_LAYERS and n <= Map.MAX_LAYERS,
    string.format("Map %s defines %d layers; must be between %d and %d",
                  path, n, Map.MIN_LAYERS, Map.MAX_LAYERS))

  local shared_ts = def.tilesize or 32
  self.layers = {}
  for i, ldef in ipairs(list) do
    ldef.tilesize = ldef.tilesize or shared_ts
    local name = ldef.name or ("layer" .. i)
    self.layers[i] = Layer.new(name, ldef)
  end

  -- Player starts on this index (defaults to the middle slice).
  self.spawn_index = def.spawn_index or math.ceil(n / 2)
  assert(self.spawn_index >= 1 and self.spawn_index <= n,
    "Map " .. path .. " spawn_index out of range")
  self.active = self.spawn_index
  return self
end

function Map:layer_count()
  return #self.layers
end

function Map:active_layer()
  return self.layers[self.active]
end

return Map
