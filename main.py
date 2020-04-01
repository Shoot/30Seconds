import asyncio
import websockets

from server.server import server
from server.game_controller import game_controller

loop = asyncio.get_event_loop()

tasks = asyncio.gather(
	websockets.serve(server, 'localhost', 5000),
	game_controller()
)

try:
	loop.run_until_complete(tasks)
	loop.run_forever()
finally:
	loop.close()