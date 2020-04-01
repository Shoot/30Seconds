import time

from . import utilities

# This file had to be renamed due to "round()" already being a function

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

	@property
	def score(self):
		score = 0
		for word in self.words:
			score += 1 if word.scored else 0
		return score

	@property
	def is_finished(self):
		return self.score == 5

	async def answer(self, word):
		for index, round_word in enumerate(self.words):
			if str(round_word) != word:
				continue

			round_word.scored = True
			await self.game.group.send(utilities.message(1, 'CORRECT_WORD', {
				'word': word,
				'index': index
			}))

		if self.is_finished:
			await self.end()

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
			'words': [str(x) for x in self.words]
		}))

		await self.answerer.send(utilities.message(1, 'ANSWERER_START'))

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
			word_score.append([str(word), word.scored])

		await self.game.group.send(utilities.message(1, 'ROUND_END', {
			'words': word_score,
			'cooldown': 10
		}))