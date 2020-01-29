#! /usr/bin/env python3
"""Fetches and stores player information."""

import sys
import sqlite3

from entities import Player

def dump(*args, **kwargs):
	"""Alias for print and flush stdout."""
	print(*args, **kwargs)
	sys.stdout.flush()

class PlayerDatabase():
	"""Fetches and stores player information."""
	def __init__(self):
		pass

	def get(self, name, init_if_not_found=True):
		"""Fetches or inits a player from the database by name."""

	def get_leaderboard(self, amount, offset):
		"""Fetches the top <amount> players by rating (offset by offset)."""

	def save(self, player):
		"""Creates a transaction to save a player to the database"""

	def commit(self):
		"""Writes saved changes to the database"""

class MemoryDatabase(PlayerDatabase):
	"""Uses an in-memory python dict to store player information."""
	def __init__(self):
		self.dict = {}
		PlayerDatabase.__init__(self)

	def get(self, name, init_if_not_found=True):
		if name not in self.dict:
			if not init_if_not_found:
				return None
			player = Player(name)
			self.dict[name] = player
		return self.dict[name]

	def get_leaderboard(self, amount, offset):
		pass #TODO

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

	def get(self, name, init_if_not_found=True):
		cursor = self.conn.cursor()
		cursor.execute('SELECT name,rating FROM players WHERE name LIKE ?', (name,))
		row = cursor.fetchone()
		if row is not None:
			dump('Player %s exists with rating %s' % (name, row[1]))
			return Player(row[0], rating=row[1])

		if not init_if_not_found:
			return None

		dump('Player %s does not exist, creating one' % name)
		return Player(name)

	def get_leaderboard(self, amount=20, offset=0):
		cursor = self.conn.cursor()
		cursor.execute('SELECT name,rating FROM players ORDER BY rating DESC LIMIT ? OFFSET ?',
		               (amount, offset))
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
	return sqldb.save(alice).save(bob).save(charlie)

def _delete_player(sqldb, name):
	cursor = sqldb.conn.cursor()
	cursor.execute('DELETE from players WHERE name=?', (name,))

def _main():
	sqldb = SQLiteDatabase('debug_players.db')
	#_dummy_init(sqldb)
	for player in sqldb.get_leaderboard(20, 0):
		dump('%s: %s' % (player.name, player.rating))

	_delete_player(sqldb, 'rankedbot')

	for player in sqldb.get_leaderboard(20, 0):
		dump('%s: %s' % (player.name, player.rating))
	#sqldb.commit()

if __name__ == '__main__':
	_main()
