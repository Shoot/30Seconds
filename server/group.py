from . import exceptions
from . import game
from . import shared
from . import utilities

class Group:
	def __init__(self, gid):
		""" Group object which holds information about all of the users in the 
		group alongside information on games

		:param gid 		: the ID of the group
		:param members 	: array of all members
		"""
		for group in shared.groups:
			if group.gid == gid:
				raise exceptions.ClientError('GROUP_EXISTS')

		self.gid = gid
		self.members = []

		self.in_game = False
		self.game = game.Game(self)

		shared.groups.append(self)

	@classmethod
	def register(cls, gid):
		""" Function to create a new group

		:param gid 	: the ID of the group
		"""
		if not utilities.validate_string(gid):
			raise exceptions.ClientError('INVALID_STRING')

		for group in shared.groups:
			if group.gid == gid:
				return group

		return cls(gid)

	async def unregister(self):
		""" Delete a group and alert its members """
		await self.send(1, 'DELETE_GROUP')
		shared.groups.remove(self)

		if self.in_game:
			shared.games.remove(self.game)

	async def add(self, member):
		""" Add a new member to the group

		:param member : member to add
		"""
		if len(self.members) == 12:
			raise exceptions.ClientError('MAX_MEMBERS')

		valid_name = False
		addition = ''
		skip = False

		while not valid_name:
			for p_member in self.members:
				if p_member.name == (member.name + addition):
					addition = '-' + utilities.random_string(4)
					skip = True
					break
				skip = False

			valid_name = True if not skip else False

		member.name += addition

		member.group = self
		self.members.append(member)
		await self.alert('GROUP_JOIN', member)

	async def remove(self, member):
		""" Remove a member from the group

		:param member : member to remove
		"""
		self.members.remove(member)
		await self.alert('GROUP_LEAVE', member)

		if len(self.members) == 0:
			await self.unregister()

	async def send(self, success, code, data=None):
		""" Send data to all members of the group

		:param data: the data to send
		"""
		for member in self.members:
			await member.send(success, code, data)

	async def alert(self, change, member):
		""" Alert all users in the group about a change in users

		:param change: action name
		:param member: the member in question
		"""
		await self.send(1, change, {
			'member': member.as_safe_dict(),
			'members': [m.as_safe_dict() for m in self.members],
			'count': len(self.members),
			'name': self.gid
		})

	async def update_user(self, member):
		""" Send updated user info to all group members

		:param member: the updated member
		"""
		await self.alert('USER_UPDATE', member)

	async def start_game(self):
		""" Start a game for the group """
		if len(self.members) < 4 or len(self.members) % 2 != 0:
			raise exceptions.ClientError('CANT_START')

		if self.in_game:
			raise exceptions.ClientError('CANT_START')

		await self.game.start()