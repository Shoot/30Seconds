import time
import random

from . import shared
from . import utilities

class Game:
	def __init__(self, group):
		"""
		Game object that stores information about the game, such
		as whether or not it is in progress, the group it belongs to,
		the round history, and when the next action will be

		:param group: the group that the game belongs to
		"""
		self.in_progress = False
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
		self.in_progress = True

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
		self.in_progress = False