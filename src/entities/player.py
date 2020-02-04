#! /usr/bin/env python3

class Player:
	def __init__(self, name, rating=1000, k=32):
		self.name = str(name)
		self.rating = rating
		self.k = k

	def get_rating(self):
		return int(round(self.rating))

	def set_rating(self, rating):
		self.rating = float(rating)
