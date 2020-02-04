#! /usr/bin/env python3
"""Fetches and stores player information."""

import sys
import sqlite3

from model import DatabaseInterface
from entities import Player

def dump(*args, **kwargs):
	"""Alias for print and flush stdout."""
	print(*args, **kwargs)
	sys.stdout.flush()

class SQLiteDatabase(DatabaseInterface):
	"""Uses SQLite to store player information."""
	def __init__(self, db_file):
		self.conn = sqlite3.connect(db_file)
		self._exec_sql('CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY, rating REAL)')
		self.commit()

	def read_player(self, name, create_if_not_found=True):
		cursor = self._exec_sql('SELECT name,rating FROM players WHERE name LIKE ?', (name,))
		row = cursor.fetchone()
		if row is not None:
			dump('Player %s exists with rating %s' % (name, row[1]))
			return Player(row[0], rating=row[1])

		if not create_if_not_found:
			return None

		dump('Player %s does not exist, creating one' % name)
		return Player(name)

	def update_player(self, player):
		self._exec_sql('INSERT OR REPLACE INTO players(name, rating) VALUES(?, ?)',
		               (player.name, player.rating))
		return self

	def delete_player(self, name):
		self._exec_sql('DELETE from players WHERE name=?', (name,))
		return self

	def get_ranking(self, player):
		cursor = self._exec_sql('SELECT COUNT(*) FROM players WHERE rating > ? AND name != ?',
		                        (player.get_rating(), player.name))
		count = cursor.fetchone()[0]
		return count + 1

	def get_leaderboard(self, amount=20, offset=0):
		cursor = self._exec_sql('SELECT name,rating FROM players ORDER BY rating DESC LIMIT ? OFFSET ?',
		                        (amount, offset))
		for (name, rating) in cursor.fetchall():
			yield Player(name, rating=rating)

	def create_game(self, game):
		raise NotImplementedError

	def delete_game(self, game_id):
		raise NotImplementedError

	def get_games(self, amount, offset=0, player_name=None):
		raise NotImplementedError

	def commit(self):
		self.conn.commit()
		return self

	def _exec_sql(self, *args, **kwargs):
		cursor = self.conn.cursor()
		cursor.execute(*args, **kwargs)
		return cursor

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
