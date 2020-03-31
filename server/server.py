import ssl
import json
import time
import random
import asyncio
import websockets
from datetime import datetime

from . import utilities

users = []
groups = []
games = []

DATALESS = ['GAME_START']

class Round:
	def __init__(self, game, team):
		"""
		Round object that stores information about a round,
		such as teams, words, and score

		:param game: game the round is part of
		:param team: the team that is playing together
		"""
		self.team = team
		self.game = game
		self.words = []
		self.finished = False
		self.questioner = None
		self.answerer = None
		self.score = 0

	@property
	def is_finished(self):
		count = 0
		for word in self.words:
			if word.scored:
				count += 1
		return count == 5

	async def answer(self, word):
		for index, round_word in enumerate(self.words):
			word_string = round_word.word
			if round_word.word != word:
				continue

			round_word.scored = True
			await self.game.group.send(utilities.message(1, 'CORRECT_WORD', {
				'word': word,
				'index': index
			}))

		if self.is_finished:
			await self.end()

		return False
		

	async def start(self):
		"""
		Start the round
		"""

		# Generate the questioner/answerer depending on how
		# many rounds the team has done before
		self.questioner, self.answerer = tuple(self.team)

		# Generate a random list of words
		self.words = [utilities.get_random_word() for _ in range(5)]

		await self.game.group.send(utilities.message(1, 'ROUND_START', {
			'questioner': self.questioner.as_safe_dict(),
			'answerer': self.answerer.as_safe_dict(),
			'round': len(self.game.rounds)
		}))

		# Send the words to the questioner
		await self.questioner.send(utilities.message(1, 'QUESTIONER_START', {
			'words': [x.word for x in self.words]
		}))

	async def end(self):
		"""
		End the round
		"""
		self.finished = True
		self.game.next_action = int(time.time()) + 10

		# Score is calculated client side, on the server side each word
		# is marked with a bool, whether or not it was correctly guessed
		# or not
		word_score = []
		for word in self.words:
			word_score.append([word.word, word.scored])

		await self.game.group.send(utilities.message(1, 'ROUND_END', {
			'words': word_score,
			'cooldown': 10
		}))

class Game:
	def __init__(self, group):
		"""
		Game object that stores information about the game, such
		as whether or not it is in progress, the group it belongs to,
		the round history, and when the next action will be

		:param group: the group that the game belongs to
		"""
		self.in_game = False
		self.group = group
		self.teams = []
		self.rounds = []
		self.next_action = 0

	def construct_teams(self):
		"""
		Randomly generate the teams
		"""

		# Copy before shuffling, as shuffle() is byref
		members = self.group.members.copy()
		random.shuffle(members)

		teams = []
		
		# Make teams of two
		for i in range(0, int(len(members) / 2)):
			teams.append([members[(i * 2)], members[(i * 2) + 1]])

		return teams

	@property
	def is_finished(self):
		"""
		Whether or not the game is finished
		:return bool:
		"""
		for score in self.scores:
			if score >= 25:
				return True

		return False

	def get_current_team(self):
		"""
		Get the currently playing team
		"""
		return self.teams[len(self.rounds) % len(self.teams)]

	async def start(self):
		"""
		Start the game
		"""
		self.group.game = self
		self.in_game = True

		self.teams = self.construct_teams()

		await self.group.send(utilities.message(1, 'GAME_START', {
			'teams': [[x.as_safe_dict(), y.as_safe_dict()] for x, y in self.teams],
			'cooldown': 10
		}))

		self.next_action = int(time.time()) + 10

	async def end(self):
		"""
		End the game
		"""
		self.in_game = False

class Group:
	def __init__(self, gid, members):
		"""
		Group object which holds information about all of the users in the group
		alongside information on games

		:param gid 		: the ID of the group
		:param members 	: array of all members
		"""

		# Don't create if it already exists
		for group in groups:
			if group.gid == gid:
				raise Exception('GROUP_EXISTS')

		self.gid = gid
		self.members = []

		self.in_game = False
		self.game = Game(self)

		games.append(self.game)
		groups.append(self)

	@classmethod
	def get(cls, gid):
		"""
		Function to create a new group

		:param gid 	: the ID of the group
		"""
		if not utilities.validate_string(gid):
			return False

		# If group already exists, return it
		for group in groups:
			if group.gid == gid:
				return group

		# Otherwise, make a new one
		return cls(gid, [])

	async def add(self, member):
		"""
		Add a new member to the group

		:param member : member to add
		"""
		if not isinstance(member, User):
			raise Exception('INVALID_TYPE')

		# Only allow a certain amount of people per group
		if len(self.members) == 12:
			raise Exception('MAX_MEMBERS')

		valid_name = False
		addition = ''
		skip = False

		# Add a random string to the new user's name if there is already a
		# member of the group with the new user's name
		while not valid_name:
			for p_member in self.members:
				if p_member.name == (member.name + addition):
					addition = '-' + utilities.random_string(4)
					skip = True
					break
				skip = False

			valid_name = (True if not skip else False)

		member.name += addition

		member.group = self
		self.members.append(member)
		await self.alert('GROUP_JOIN', member)

	async def remove(self, member):
		"""
		Remove a member from the group

		:param member : member to remove
		"""
		if not isinstance(member, User):
			raise Exception('INVALID_TYPE')

		self.members.remove(member)
		await self.alert('GROUP_LEAVE', member)

		# Clean up, remove group from the list if there are no longer
		# any members
		if len(self.members) == 0:
			groups.remove(self)

	async def alert(self, change, member):
		"""
		Alert all users in the group about a change in users

		:param change: action name
		:param member: the member in question
		"""
		await self.send(utilities.message(1, change, {
			'member': member.as_safe_dict(),
			'members': [m.as_safe_dict() for m in self.members],
			'count': len(self.members),
			'name': self.gid
		}))

	async def update_user(self, member):
		"""
		Send updated user info to all group members

		:param member: the updated member
		"""
		await self.alert('USER_UPDATE', member)

	async def start_game(self):
		"""
		Start a game for the group
		"""

		# Must be more than 2 teams, each with 2 people in them
		if len(self.members) < 4 or len(self.members) % 2 != 0:
			raise Exception('CANT_START')

		if self.in_game:
			raise Exception('CANT_START')

		self.in_game = True

		await self.game.start()

	async def send(self, data):
		"""
		Send data to all members of the group

		:param data: the data to send
		"""
		for member in self.members:
			await member.websocket.send(data)

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
		users.append(self)

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

		users.remove(self)

	async def join_group(self, gid):
		"""
		Try to join a group

		:param gid 	: the ID of the group to join
		"""

		# Don't join if user is already in the group
		if self.group != None:
			if self.group.gid == gid:
				return False

		if not utilities.validate_string(gid):
			return False

		group = Group.get(gid)

		await group.add(self)

	async def leave_group(self):
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

		# Skip if user already has the name
		if name == self.name:
			raise Exception('INVALID_NAME')

		# Skip if the new name has invalid letters
		if not utilities.validate_string(name):
			raise Exception('INVALID_NAME')

		self.name = name

		# Make sure that other people in the user's group don't
		# share the name
		if self.group != None:
			for member in self.group.members:
				if member.name == name and member.uid != self.uid:
					raise Exception('TAKEN_NAME')

			await self.group.update_user(self)

	async def send_message(self, message):
		"""
		Send a message to the user's group

		:param message 	: message to send
		"""

		# Skip if we have no group to send to
		if not self.group:
			raise Exception('NO_GROUP')

		# Limit messages to less than 100 characters
		if len(message) > 100:
			raise Exception('INVALID_MESSAGE')

		# Limit the user to 1 message per 0.1 seconds
		if self.last_message > int(time.time()) - 0.1:
			raise Exception('RATE_LIMIT')

		# Send the message to everyone in the group
		await self.group.send(utilities.message(1, 'CHAT_MESSAGE', {
			'user': self.as_safe_dict(),
			'message': message
		}))

		# Check if the user is an answerer in a current game, then check if the word
		# is one of the answers for the round
		if self.group.game.in_game:
			current_round = self.group.game.rounds[-1]
			if current_round.answerer == self and not current_round.finished:
				for index, word in enumerate(current_round.words):
					if word.word.lower().strip() != message.lower().strip():
						continue

					await current_round.answer(word.word)

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
		if not data and action not in DATALESS:
			raise Exception('NO_DATA')

		# Do the action the user wants to do
		if action == 'JOIN_GROUP':
			await self.join_group(data.get('group'))
		elif action == 'LEAVE_GROUP':
			await self.leave_group()
		elif action == 'EDIT_USER':
			await self.edit(name=data.get('name'))
		elif action == 'GAME_START':
			await self.group.start_game()
		elif action == 'CHAT_MESSAGE':
			await self.send_message(data.get('message'))
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
			#try:
			await self.process_data(await self.websocket.recv())
			#except Exception as e:
			#	await self.websocket.send(utilities.message(0, str(e)))

async def server(websocket, path):
	log('New connection', websocket)
	user = await User.register(websocket)
	if not user:
		return await websocket.send(utilities.message(0, 'INVALID_JSON'))

	await websocket.send(utilities.message(1, 'HELLO', user.as_safe_dict()))

	try:
		await user.loop()
	except websockets.ConnectionClosed:
		log('Connection closed unexpectedly', websocket)
	finally:
		await user.unregister()
		log('Unregistered a user', websocket)

async def game_controller():
	log('Started the controller')
	while 1:
		for game in games:
			# Skip if game is finished/hasn't started
			if not game.in_game:
				continue

			# Skip if the next action is still coming up
			if game.next_action > int(time.time()):
				continue

			if len(game.rounds) == 0 or game.rounds[-1].finished == True:
				# Make a new round if the last round is finished, or there are no
				# other rounds
				new_team = game.get_current_team()
				new_round = Round(game, new_team)
				game.rounds.append(new_round)
				game.next_action = int(time.time()) + 30

				await new_round.start()

				log('Started round ' + str(len(game.rounds)), game.group)
			else:
				# Otherwise, end the round
				await game.rounds[-1].end()

				log('Ended round ' + str(len(game.rounds)), game.group)

		# Sleep for a small amount of time so as to not overload the server
		await asyncio.sleep(0.1)

def log(message, data=None):
	# Logging format:
	# [dd/mm/yyyy hh:mm] [group-id]: <message>
	if data is None:
		extra_data = 'server'
	elif isinstance(data, websockets.server.WebSocketServerProtocol):
		extra_data = str(data.remote_address[0]) + ':' + str(data.remote_address[1])
	elif isinstance(data, Group):
		extra_data = data.gid
	else:
		extra_data = type(data)

	print(f"[{datetime.now().strftime('%d/%m/%y %H:%M:%S')}] [{extra_data}]: {message}")