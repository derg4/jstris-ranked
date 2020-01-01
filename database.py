#! /usr/bin/env python3
"""Fetches and stores player information."""

import sys
import sqlite3

from player import Player

def dump(*args, **kwargs):
	"""Alias for print and flush stdout."""
	print(*args, **kwargs)
	sys.stdout.flush()

class PlayerDatabase():
	"""Fetches and stores player information."""
	def __init__(self):
		pass

	def get(self, name):
		"""Fetches or inits a player from the database by name."""

	def get_all(self):
		"""Fetches a list of all players in the database."""

	def save(self, player):
		"""Creates a transaction to save a player to the database"""

	def commit(self):
		"""Writes saved changes to the database"""

class MemoryDatabase(PlayerDatabase):
	"""Uses an in-memory python dict to store player information."""
	def __init__(self):
		self.dict = {}
		PlayerDatabase.__init__(self)

	def get(self, name):
		if name not in self.dict:
			player = Player(name)
			self.dict[name] = player
		return self.dict[name]

	def get_all(self):
		return self.dict.values()

	def save(self, player):
		self.dict[player.name] = player
		return self

	def commit(self):
		return self

class SQLiteDatabase(PlayerDatabase):
	"""Uses SQLite to store player information."""
	def __init__(self, db_file):
		self.conn = sqlite3.connect(db_file)
		cursor = self.conn.cursor()
		cursor.execute('CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY, rating REAL)')
		self.conn.commit()

		PlayerDatabase.__init__(self)

	def get(self, name):
		cursor = self.conn.cursor()
		cursor.execute('SELECT rating FROM players WHERE name=?', (name,))
		row = cursor.fetchone()
		if row is not None:
			dump('Player %s exists with rating %s' % (name, row[0]))
			return Player(name, rating=row[0])

		# No need to save/commit because if they don't play a game, they'll just be default anyway
		dump('Player %s does not exist, creating one' % name)
		return Player(name)

	def get_all(self):
		cursor = self.conn.cursor()
		cursor.execute('SELECT name,rating FROM players ORDER BY rating DESC')
		for (name, rating) in cursor.fetchall():
			yield Player(name, rating=rating)

	def save(self, player):
		cursor = self.conn.cursor()
		cursor.execute('INSERT OR REPLACE INTO players(name, rating) VALUES(?, ?)',
		               (player.name, player.rating))
		return self

	def commit(self):
		self.conn.commit()
		return self

def _dummy_init(sqldb):
	alice = Player("Alice", 1200)
	bob = Player("Bob", 1400)
	charlie = Player("Charlie", 1600)
	sqldb.save(alice).save(bob).save(charlie).commit()

def _main():
	sqldb = SQLiteDatabase('debug_players.db')
	#_dummy_init(sqldb)
	for player in sqldb.get_all():
		dump('%s: %s' % (player.name, player.rating))

if __name__ == '__main__':
	_main()
