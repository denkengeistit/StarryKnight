-- StarryKnight: Diablo x Mario sidescroller with a Triplane mapping system.
-- Entry point.

local State = require("src.state")

function love.load()
  math.randomseed(os.time())
  State.load()
end

function love.update(dt)
  State.update(dt)
end

function love.draw()
  State.draw()
end

function love.keypressed(key)
  if key == "escape" then
    love.event.quit()
    return
  end
  State.keypressed(key)
end

function love.keyreleased(key)
  State.keyreleased(key)
end
