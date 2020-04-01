import time
import asyncio

from . import shared
from . import utilities
from . import g_round

async def game_controller():
	utilities.log('Started the controller')
	while 1:
		for game in shared.games:
			# Skip if game is finished/hasn't started
			if not game.in_progress:
				continue

			# Skip if the next action is still coming up
			if game.next_action > int(time.time()):
				continue

			if len(game.rounds) == 0 or game.rounds[-1].finished == True:
				# Make a new round if the last round is finished, or there are no
				# other rounds
				new_team = game.get_current_team()
				new_round = g_round.Round(game, new_team)
				game.rounds.append(new_round)
				game.next_action = int(time.time()) + 30

				await new_round.start()

				utilities.log('Started round ' + str(len(game.rounds)), game.group)
			else:
				# Otherwise, end the round
				await game.rounds[-1].end()

				utilities.log('Ended round ' + str(len(game.rounds)), game.group)

		# Sleep for a small amount of time so as to not overload the server
		await asyncio.sleep(0.1)