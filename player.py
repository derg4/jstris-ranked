#! /usr/bin/env python3

class Player:
	def __init__(self, player_id, name, rating=1000, k=16):
		self.id = str(player_id)
		self.name = str(name)
		self.rating = rating
		self.k = 32

	def get_rating(self):
		return int(round(self.rating))
