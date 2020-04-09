import asyncio
import logging
import time

from . import shared
from . import g_round

log = logging.getLogger(__name__)

async def controller():
	log.info('Started the controller')

	while 1:
		for game in shared.games:
			if not game.in_progress:
				continue

			# 4 rounds per team
			if len(game.rounds) == len(game.group.members) * 4 and game.rounds[-1].finished == True:
				await game.end()

				log.info('Ended the game for \'%s\'' % (game.group.gid))

			if game.next_action > int(time.time()):
				continue

			if len(game.rounds) == 0 or game.rounds[-1].finished == True:
				new_team = game.get_current_team()
				new_round = g_round.Round(game, new_team)
				game.rounds.append(new_round)
				game.next_action = int(time.time()) + 30

				await new_round.start()

				log.info('Started a new round for \'%s\'' % (game.group.gid))
			else:
				await game.rounds[-1].end()

				log.info('Ended a round for \'%s\'' % (game.group.gid))

		await asyncio.sleep(0.1)