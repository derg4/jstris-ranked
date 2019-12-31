#! /usr/bin/env python3
"""Fetches and stores player information."""

from player import Player

class PlayerDatabase():
	"""Fetches and stores player information."""
	def __init__(self):
		pass

	def get(self, player_id, name):
		"""Fetches or inits a player from the database by player_id (name is in case you have to init)."""

	def save(self, player):
		"""Saves a player to the database"""

class MemoryDatabase(PlayerDatabase):
	"""Uses an in-memory python dict to store player information."""
	def __init__(self):
		self.dict = {}
		PlayerDatabase.__init__(self)

	def get(self, player_id, name):
		if player_id not in self.dict:
			player = Player(player_id, name)
			self.dict[player_id] = player
		return self.dict[player_id]

	def save(self, player):
		self.dict[player.id] = player
