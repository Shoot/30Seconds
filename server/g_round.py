import logging
import time

from . import utilities

log = logging.getLogger(__name__)

# This file had to be renamed due to "round()" already being a function

class Round:
	def __init__(self, game, team):
		""" Round object that stores information about a round, such as teams,
		words, and score

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
		""" The current score """
		score = 0
		for word in self.words:
			score += 1 if word['scored'] else 0
		return score

	@property
	def is_finished(self):
		""" Whether or not the game is finished """
		return self.score == 5

	async def answer(self, word):
		""" Try to guess a word for the round

		:param word: the word to guess
		"""
		for index, word_data in enumerate(self.words):
			if word_data != word:
				continue

			word_data['scored'] = True
			await self.game.group.send(1, 'CORRECT_WORD', {
				'word': word,
				'index': index
			})

		if self.is_finished:
			await self.end()

	async def start(self):
		""" Start the round """
		self.questioner, self.answerer = tuple(self.team)
		self.words = [{
			'word': utilities.get_random_word(),
			'scored': False
		} for _ in range(5)]

		await self.game.group.send(1, 'ROUND_START', {
			'questioner': self.questioner.as_safe_dict(),
			'answerer': self.answerer.as_safe_dict(),
			'round': len(self.game.rounds)
		})

		await self.questioner.send(1, 'QUESTIONER_START', {
			'words': self.words
		})

		await self.answerer.send(1, 'ANSWERER_START')

	async def end(self):
		""" End the round """
		self.finished = True
		self.game.next_action = int(time.time()) + 10

		await self.game.group.send(1, 'ROUND_END', {
			'words': self.words,
			'cooldown': 10
		})