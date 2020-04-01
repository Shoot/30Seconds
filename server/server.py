import websockets
from . import utilities
from .user import User

async def server(websocket, path):
	utilities.log('New connection', websocket)
	user = await User.register(websocket)
	if not user:
		return await websocket.send(utilities.message(0, 'INVALID_JSON'))

	await websocket.send(utilities.message(1, 'HELLO', user.as_safe_dict()))

	try:
		await user.loop()
	except websockets.ConnectionClosed:
		utilities.log('Connection closed unexpectedly', websocket)
	finally:
		await user.unregister()
		utilities.log('Unregistered a user', websocket)