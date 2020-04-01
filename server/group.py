from . import utilities, shared, user, game

class Group:
	def __init__(self, gid, members):
		"""
		Group object which holds information about all of the users in the group
		alongside information on games

		:param gid 		: the ID of the group
		:param members 	: array of all members
		"""

		# Don't create if it already exists
		for group in shared.groups:
			if group.gid == gid:
				raise Exception('GROUP_EXISTS')

		self.gid = gid
		self.members = []

		self.in_game = False
		self.game = game.Game(self)

		shared.games.append(self.game)
		shared.groups.append(self)

	@classmethod
	def register(cls, gid):
		"""
		Function to create a new group

		:param gid 	: the ID of the group
		"""
		if not utilities.validate_string(gid):
			raise Exception('INVALID_STRING')

		# If group already exists, return it
		for group in shared.groups:
			if group.gid == gid:
				return group

		# Otherwise, make a new one
		return cls(gid, [])

	async def unregister(self):
		await self.send(utilities.message(1, 'DELETE_GROUP'))
		groups.remove(self)

		if self.in_game:
			games.remove(self.game)

	async def add(self, member):
		"""
		Add a new member to the group

		:param member : member to add
		"""
		if not isinstance(member, user.User):
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
		if not isinstance(member, user.User):
			raise Exception('INVALID_TYPE')

		self.members.remove(member)
		await self.alert('GROUP_LEAVE', member)

		# Clean up, remove group from the list if there are no longer
		# any members
		if len(self.members) == 0:
			await self.unregister()

	async def send(self, data):
		"""
		Send data to all members of the group

		:param data: the data to send
		"""
		for member in self.members:
			await member.websocket.send(data)

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