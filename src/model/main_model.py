#! /usr/bin/env python3
"""Mediates the interaction between UI (detsbot) and other layers (jstris, elo, etc)."""

import math

from entities import Elo
from model import GameInterface, GameState

class JstrisModel():
	"""Mediates the interaction between UI (detsbot) and other layers (jstris, elo, etc)."""
	def __init__(self, jstris: GameInterface, database):
		self.jstris = jstris
		#pylint: disable=invalid-name
		self.db = database
		self.elo = Elo()

	async def watch_live(self):
		"""Starts watching live."""
		if self.jstris.state != GameState.STOPPED:
			return

		await self.jstris.create_game(live=True)

	async def watch_lobby(self):
		"""Creates a new lobby, returns the join link."""
		if self.jstris.state != GameState.STOPPED:
			return

		return await self.jstris.create_game()

	async def run_matches(self):
		"""Runs and processes the game matches."""
		async for result in self.jstris.watch_and_get_results():
			yield self._process_game_results(result)


	def get_player(self, name):
		"""Returns the player (None if not found)."""
		return self.db.read_player(name, create_if_not_found=False)

	def set_player_rating(self, name, rating):
		"""Sets the player's elo."""
		player = self.get_player(name)
		if player is None:
			return False

		player.set_rating(rating)
		self.db.update_player(player)
		self.db.commit()
		return True

	def reset_player(self, name):
		"""Resets the player, by deleting them from the database."""
		self.db.delete_player(name)
		self.db.commit()

	def get_player_ranking(self, name):
		"""
		Gets the player's ranking of the player (by rating) in the database.

		returns (player, ranking>
		"""
		player = self.get_player(name)
		if player is None:
			return None

		return (player, self.db.get_ranking(player))

	def get_leaderboard(self, page=1, page_size=20):
		"""Returns a list of the top rated players (20 per page by default)."""
		return (list(self.db.get_leaderboard(page_size, (page - 1) * page_size)),
		        int(math.ceil(self.db.count_players() / page_size)))

	def simulate_1v1(self, player1, player2):
		"""Returns player1's estimated winrate against player2."""
		return self.elo.estimate_score_vs_one(player1.rating, player2.rating)

	def _process_game_results(self, raw_results):
		# TODO fix the disaster that happens when people enter a game more than once
		results = [(self.db.read_player(res['name']), res['score']) for res in raw_results]

		elo_result = self.elo.report_game(results)
		if elo_result is None:
			return None

		(players, scores, score_changes) = elo_result
		for player in players:
			self.db.update_player(player)
		self.db.commit()

		return zip(players, scores, score_changes)

	async def quit_watching(self):
		"""Quits watching matches"""
		await self.jstris.quit()

	def run(self):
		"""Set up the various modules and wait for input from detsbot."""

	def get_join_link(self):
		"""Returns the join link to the existing lobby, or None if there is none."""

	def get_or_start_match(self):
		"""Fetch the join link for an existing match, or start one.

		Returns the join link to the existing or new"""
