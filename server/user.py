import json
import logging

from . import constants
from . import exceptions
from . import shared
from . import utilities
from .group import Group

log = logging.getLogger(__name__)

class User:
	def __init__(self, websocket, name, group=None):
		""" Basic user object which stores information on them, including their
		websocket, UIDs, and group/game information.

		:param websocket: websocket connection for the user
		:param name 	: the user's name
		:param group 	: group to join
		"""
		self.websocket = websocket
		self.name = name
		self.group = group
		self.session = utilities.random_string(32)
		self.uid = utilities.random_string(32)
		self.active = 1

		shared.users.append(self)

	def as_safe_dict(self):
		""" Returns safe information about the user that can be given to anyone """
		return {
			'group': (self.group.gid if self.group else None),
			'name': self.name,
			'uid': self.uid
		}

	@classmethod
	async def register(cls, websocket):
		""" Registers the websocket to a user

		:param websocket: websocket connection
		:return User 	: the user's information
		""" 
		await websocket.send(json.dumps({
			's': 1, 
			'c': 'CONNECT_START'
		}))

		user = utilities.is_json(await websocket.recv())
		if not user:
			raise exceptions.ClientError('INVALID_JSON')

		if user.get('d'):
			username = user['d'].get('name')
			if not utilities.validate_string(username):
				username = utilities.random_string(16)
		else:
			username = utilities.random_string(16)

		return cls(websocket, group=None, name=username)

	async def unregister(self):
		""" Unregister the user's object """
		if self.group != None:
			if self.group.in_game:
				for team in self.group.game.teams:
					if self in team:
						self.group.game.teams.remove(team)
						break

			await self.group.remove(self)

		shared.users.remove(self)

	async def join(self, gid):
		""" Try to join a group

		:param gid: the ID of the group to join
		"""
		if self.group != None:
			if self.group.gid == gid:
				raise exceptions.ClientError('IN_GROUP')

		if gid and not utilities.validate_string(gid):
			raise exceptions.ClientError('INVALID_STRING')

		if gid:
			group = Group.register(gid)
		else:
			tries = 0
			while 1:
				if tries >= 5:
					raise exceptions.ClientError('INVALID_GROUP')
				gid = utilities.random_string(16)
				group = Group.register(gid)
				if len(group.members) == 0:
					break
				tries += 1

		if group.in_game:
			raise exceptions.ClientError('IN_GAME')

		await group.add(self)

	async def leave(self):
		""" Try to leave a group """
		if self.group == None:
			raise exceptions.ClientError('NO_GROUP')

		await self.group.remove(self)

		self.group = None

	async def edit(self, name=None):
		""" Edit a user's information, just name for now

		:param name : new name for the user
		"""
		sanitized_name = utilities.sanitize_string(str(name))

		if sanitized_name in {'', None}:
			raise exceptions.ClientError('INVALID_NAME')

		if sanitized_name == self.name:
			raise exceptions.ClientError('INVALID_NAME')

		if not 0 < len(sanitized_name) < 32:
			raise exceptions.ClientError('INVALID_NAME')

		self.name = sanitized_name

		if self.group != None:
			for member in self.group.members:
				if member.name == sanitized_name and member.uid != self.uid:
					raise exceptions.ClientError('TAKEN_NAME')

			await self.group.update_user(self)

	async def message(self, message):
		""" Send a chat message to the user's group

		:param message: message to send
		"""
		if not self.group:
			raise exceptions.ClientError('NO_GROUP')

		sanitized_message = utilities.sanitize_string(message)

		if not (0 < len(sanitized_message) < 100):
			raise exceptions.ClientError('INVALID_MESSAGE')

		if self.group.game.in_progress and len(self.group.game.rounds) > 0:
			current_round = self.group.game.rounds[-1]
			if current_round.answerer == self and not current_round.finished:
				for index, word in enumerate(current_round.words):
					if word.lower().strip() == sanitized_message.lower().strip():
						await current_round.answer(word)
			elif current_round.questioner == self:
				raise exceptions.ClientError('CANT_MESSAGE')

		await self.group.send(1, 'CHAT_MESSAGE', {
			'user': self.as_safe_dict(),
			'message': sanitized_message
		})

	async def process_data(self, received):
		""" Process the data received from the websocket

		:param received: data received
		"""
		received_json = utilities.is_json(received)

		if not received_json:
			raise exceptions.ClientError('INVALID_JSON')

		action = received_json.get('c').upper()
		data = received_json.get('d')

		if not data and action not in constants.DATALESS:
			raise exceptions.ClientError('NO_DATA')

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

		log.info('%s@%s: %s' % (
			self.name,
			self.group.gid if self.group else '',
			action
		))

	async def send(self, success, code, data=None):
		""" Send data to the websocket formatted

		:param success	: whether or not the request succeeded
		:param code		: action/error code
		:param data 	: data to send
		"""
		await self.websocket.send(json.dumps({
			's': success,
			'c': code,
			'd': data
		}))

	async def loop(self):
		""" Continually receive information from the user and process it """
		while self.active:
			try:
				await self.process_data(await self.websocket.recv())
			except exceptions.ClientError as e:
				await self.send(0, str(e))