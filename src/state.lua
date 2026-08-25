-- Minimal state machine. v0 has only 'play'.
local State = {}

local Play = require("src.play")

State.current = Play

function State.load()
  Play.load()
end

function State.update(dt)
  if State.current and State.current.update then
    State.current.update(dt)
  end
end

function State.draw()
  if State.current and State.current.draw then
    State.current.draw()
  end
end

function State.keypressed(key)
  if State.current and State.current.keypressed then
    State.current.keypressed(key)
  end
end

function State.keyreleased(key)
  if State.current and State.current.keyreleased then
    State.current.keyreleased(key)
  end
end

return State
