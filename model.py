#! /usr/bin/env python3
"""Mediates the interaction between UI (detsbot) and other layers (jstris, elo, etc)."""

import asyncio

from elo import Elo

class JstrisModel():
	"""Mediates the interaction between UI (detsbot) and other layers (jstris, elo, etc)."""
	def __init__(self, jstris, database):
		self.jstris = jstris
		self.database = database
		self.elo = Elo()

	async def watch_live(self):
		"""Watches live matches until quit_watching is called."""
		await self.jstris.go_to_live()
		self.jstris.enter_spectator_mode()
		while True:
			await self.jstris.start_game_live()
			await self.jstris.wait_for_game_end()
			yield self._process_game_results(self.jstris.get_game_results())

	async def create_lobby(self):
		"""Creates a lobby and returns the join link."""
		return await self.jstris.get_lobby()

	async def watch_lobby(self):
		"""Assumes a lobby is created, and runs the game."""
		self.jstris.enter_spectator_mode()
		while True:
			await asyncio.sleep(10)
			await self.jstris.start_game()
			await self.jstris.wait_for_game_end()
			yield self._process_game_results(self.jstris.get_game_results())

	def _process_game_results(self, raw_results):
		raw_results = self.jstris.get_game_results()
		results = [(self.database.get(res['id'], res['name']), res['score']) for res in raw_results]

		elo_result = self.elo.report_game(results)
		if elo_result is None:
			return None

		(players, scores, score_changes) = elo_result
		for player in players:
			self.database.save(player)
		return zip(players, scores, score_changes)

	async def quit_watching(self):
		"""Quits watching matches"""
		await self.jstris.log_in()

	def run(self):
		"""Set up the various modules and wait for input from detsbot."""

	def get_join_link(self):
		"""Returns the join link to the existing lobby, or None if there is none."""

	def get_or_start_match(self):
		"""Fetch the join link for an existing match, or start one.

		Returns the join link to the existing or new"""
