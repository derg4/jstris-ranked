#! /usr/bin/env python3
"""The abstract interface for a database to store Players and Games."""

from abc import ABC, abstractmethod

class DatabaseInterface(ABC):
	"""Fetches and stores player information."""

	@abstractmethod
	def read_player(self, name, create_if_not_found=True):
		"""Fetch a player from the database by name (perhaps creating them if not found)"""

	@abstractmethod
	def update_player(self, player):
		"""Update a player in the database"""

	@abstractmethod
	def delete_player(self, name):
		"""Delete a player from the database (by name)"""

	@abstractmethod
	def get_leaderboard(self, amount, offset=0):
		"""Fetch the top <amount> players by rating (offset by [offset])"""

	@abstractmethod
	def create_game(self, game):
		"""Save a game to the database"""

	@abstractmethod
	def delete_game(self, game_id):
		"""Delete a game from the database (by id)"""

	@abstractmethod
	def get_games(self, amount, offset=0, player_name=None):
		"""Fetch the last <amount> games played (offset by [offset]) played by [player_name]."""

	@abstractmethod
	def commit(self):
		"""Writes saved changes to the database"""
