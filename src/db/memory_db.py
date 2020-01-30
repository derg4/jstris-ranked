#! /usr/bin/env python3
"""Fetches and stores player information."""

from model import DatabaseInterface
from entities import Player

class MemoryDatabase(DatabaseInterface):
	"""Uses an in-memory python dict to store data."""
	def __init__(self):
		self.players = {}
		DatabaseInterface.__init__(self)

	def read_player(self, name, create_if_not_found=True):
		if name not in self.players:
			if not create_if_not_found:
				return None
			player = Player(name)
			self.players[name] = player
		return self.players[name]

	def update_player(self, player):
		self.players[player.name] = player
		return self

	def delete_player(self, name):
		del self.players[name]
		return self

	def get_leaderboard(self, amount, offset=0):
		pass #TODO

	def create_game(self, game):
		pass #TODO

	def delete_game(self, game_id):
		pass #TODO

	def get_games(self, amount, offset=0, player_name=None):
		pass #TODO

	def commit(self):
		return self
