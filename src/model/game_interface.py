#! /usr/bin/env python3
"""The abstract interface for a multiplayer game controller."""

from abc import ABC, abstractmethod
from enum import Enum, auto

class GameInterface(ABC):
	"""Manages the actual running of the games."""

	@abstractmethod
	async def create_game(self, live=False):
		"""Create a new lobby for the game. Returns the join link (moves directly to CREATED state)"""

	@abstractmethod
	def get_join_link(self):
		"""Get the join link, or None if we are in STOPPED state"""

	@abstractmethod
	async def watch_and_get_results(self):
		"""
		Starts running matches automatically, yielding match results (as a generator)

		Requires we are in CREATED state, moves to WATCHING state immediately.
		Intermittently enters RUNNING state, while a match is running.
		When the generator is done, will enter STOPPED state.

		Is a generator, yields lists of [(Player, Score), ...]
		"""

	@abstractmethod
	async def quit(self):
		"""
		Stops running matches and leaves the lobby as soon as we are between matches
		Moves directly to STOPPED state, eventually
		"""

	@abstractmethod
	async def force_quit(self):
		"""Stops running matches and leaves the lobby IMMEDIATELY (moves directly to STOPPED state)"""

	@abstractmethod
	def get_state(self):
		"""Get the current state of the game manager, as a GameState object"""

class GameState(Enum):
	"""The possible states of the GameInterface."""

	STOPPED = auto()
	CREATED = auto()
	WATCHING = auto()
	RUNNING = auto()
