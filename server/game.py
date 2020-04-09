import random
import time

from . import shared

class Game:
	def __init__(self, group):
		""" Game object that stores information about the game, such as whether
		or not it is in progress, the group it belongs to, the round history,
		and when the next action will be

		:param group: the group that the game belongs to
		"""
		self.in_progress = False
		self.group = group
		self.teams = []
		self.rounds = []
		self.next_action = 0

		shared.games.append(self)

	@property
	def is_finished(self):
		""" Whether or not the game is finished """
		for score in self.scores:
			if score >= 25:
				return True

		return False

	def construct_teams(self):
		""" Randomly generate the teams """
		members = self.group.members.copy()
		random.shuffle(members)

		teams = []

		for i in range(0, int(len(members) / 2)):
			teams.append([members[(i * 2)], members[(i * 2) + 1]])

		return teams

	def get_current_team(self):
		""" Get the currently playing team """
		return self.teams[len(self.rounds) % len(self.teams)]

	async def start(self):
		""" Start the game """
		self.group.game = self
		self.group.in_game = True
		self.in_progress = True

		self.teams = self.construct_teams()

		await self.group.send(1, 'GAME_START', {
			'teams': [
				[x.as_safe_dict(), y.as_safe_dict()] for x, y in self.teams
			],
			'cooldown': 10
		})

		self.next_action = int(time.time()) + 10

	async def end(self):
		""" End the game """
		self.in_progress = False

		scores = [{
			'team': [x.as_safe_dict() for x in team],
			'score': 0}
		for team in self.teams]
		
		for game_round in self.rounds:
			scores[self.teams.index(game_round.team)]['score'] += game_round.score

		await self.group.send(1, 'GAME_END', {
			'scores': scores
		})