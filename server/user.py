import time

from . import constants
from . import group
from . import shared
from . import utilities

class User:
	def __init__(self, websocket, **kwargs):
		"""
		Basic user object which stores information on them,
		including their websocket, UIDs, and group/game information.

		:param websocket: websocket connection for the user
		:param kwargs	: 	name 	-> the user's name
							group 	-> group to join
		"""
		self.websocket = websocket
		self.name = kwargs.get('name')
		self.group = kwargs.get('group')
		self.session = utilities.random_string(32)
		self.uid = utilities.random_string(32)

		# Whether or not the websocket is active
		self.active = 1

		# The user's last sent message, used for rate limiting
		self.last_message = 0

		# Add user to the global users array, useful for tracking
		shared.users.append(self)

	def as_safe_dict(self):
		"""
		Returns safe information about the user that can be
		given to any user publicly
		"""
		return {
			'group': (self.group.gid if self.group else None),
			'name': self.name,
			'uid': self.uid
		}

	@classmethod
	async def register(cls, websocket):
		"""
		Registers the websocket to a user

		:param websocket: websocket connection
		:return User 	: the user's information
		""" 
		await websocket.send(utilities.message(1, 'CONNECT_START'))

		user = utilities.is_json(await websocket.recv())
		if not user:
			return False

		if user.get('d'):
			username = user['d'].get('name')
			if not utilities.validate_string(username):
				username = utilities.random_string(16)
		else:
			username = utilities.random_string(16)

		return cls(websocket, group=None, name=username)

	async def unregister(self):
		"""
		Unregister the user's object
		"""
		if self.group != None:
			await self.group.remove(self)

		shared.users.remove(self)

	async def join(self, gid):
		"""
		Try to join a group

		:param gid 	: the ID of the group to join
		"""

		# Don't join if user is already in the group
		if self.group != None:
			if self.group.gid == gid:
				return False

		if gid and not utilities.validate_string(gid):
			return False

		# If no group is provided, create a new random one
		if gid:
			target_group = group.Group.register(gid)
		else:
			tries = 0
			while 1:
				if tries >= 5:
					raise Exception('INVALID_GROUP')
				gid = utilities.random_string(16)
				target_group = Group.register(gid)
				if len(target_group.members) == 0:
					break
				tries += 1

		await target_group.add(self)

	async def leave(self):
		"""
		Try to leave a group
		"""
		if self.group == None:
			return False

		await self.group.remove(self)
		self.group = None

		return True

	async def edit(self, name=None):
		"""
		Edit a user's information, just name for now

		:param name : new name for the user
		"""

		sanitized_name = utilities.sanitize_string(name)

		if sanitized_name in {'', None}:
			raise Exception('INVALID_NAME')

		if sanitized_name == self.name:
			raise Exception('INVALID_NAME')

		self.name = sanitized_name

		# Make sure that other people in the user's group don't
		# share the name
		if self.group != None:
			for member in self.group.members:
				if member.name == sanitized_name and member.uid != self.uid:
					raise Exception('TAKEN_NAME')

			await self.group.update_user(self)

	async def message(self, message):
		"""
		Send a message to the user's group

		:param message 	: message to send
		"""

		# Skip if we have no group to send to
		if not self.group:
			raise Exception('NO_GROUP')

		# Limit messages to less than 100 characters
		if not (0 < len(message) < 100):
			raise Exception('INVALID_MESSAGE')

		# Limit the user to 1 message per 0.1 seconds
		if self.last_message > int(time.time()) - 0.1:
			raise Exception('RATE_LIMIT')

		# Sanitize the user's input
		sanitized_message = utilities.sanitize_string(message)

		# Send the message to everyone in the group
		await self.group.send(utilities.message(1, 'CHAT_MESSAGE', {
			'user': self.as_safe_dict(),
			'message': sanitized_message
		}))

		# Check if the user is an answerer in a current game, then check if the word
		# is one of the answers for the round
		if self.group.game.in_progress and len(self.group.game.rounds) > 0:
			current_round = self.group.game.rounds[-1]
			if current_round.answerer == self and not current_round.finished:
				for index, word in enumerate(current_round.words):
					if str(word).lower().strip() != sanitized_message.lower().strip():
						continue

					await current_round.answer(str(word))

		# Save when we last sent a message for rate limiting
		self.last_message = int(time.time())

	async def process_data(self, received):
		"""
		Process the data received from the websocket

		:param received : data received from the websocket
		"""

		# Validate that the received data is JSON,, then return it
		# as JSON
		received_json = utilities.is_json(received)

		if not received_json:
			raise Exception('INVALID_JSON')

		action = received_json.get('c')
		data = received_json.get('d')

		# If data is not provided when we need it, throw an error
		if not data and action not in constants.DATALESS:
			raise Exception('NO_DATA')

		# Do the action the user wants to do
		if action == 'JOIN_GROUP':
			await self.join(data.get('group'))
		elif action == 'LEAVE_GROUP':
			await self.leave()
		elif action == 'EDIT_USER':
			await self.edit(name=data.get('name'))
		elif action == 'GAME_START':
			await self.group.start_game()
		elif action == 'CHAT_MESSAGE':
			await self.message(data.get('message'))
		elif action == 'CLOSE_CONNECTION':
			self.active = 0

		return True

	async def send(self, data):
		"""
		Send data to the websocket
		* Unnecessary but done for neatness, maybe remove?

		:param data : data to send
		"""
		await self.websocket.send(data)

	async def loop(self):
		"""
		Continually receive information from the user and process it
		"""
		while self.active:
			try:
				await self.process_data(await self.websocket.recv())
			except Exception as e:
				await self.send(utilities.message(0, str(e)))