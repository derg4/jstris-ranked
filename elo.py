#! /usr/bin/env python3
"""Manages the calculations regarding Elo skill ratings."""

from player import Player

def clamp(num, smallest, largest):
	"""Clamps num between the given bounds."""
	return max(smallest, min(num, largest))

class Elo:
	"""Manages the calculations regarding Elo skill ratings."""
	def __init__(self, d=400):
		self.d_const = d

	def report_game(self, players_scores):
		"""Given the result of a game, adjust the players' skill ratings according to performance.

		players_scores -- list of (player, score), player is a Player, score is numeric
		"""
		num_players = len(players_scores)
		score_changes = [0 for _ in range(num_players)]

		k_mult = 1 / (num_players - 1)

		# For each matchup, simulate a game
		for i in range(num_players - 1):
			for j in range(i + 1, num_players):
				(p1_delta, p2_delta) = self.calc_score_changes_2p(players_scores[i], players_scores[j], k_mult)
				score_changes[i] += p1_delta
				score_changes[j] += p2_delta
				#print("Score change: %s (%+s) vs %s (%+s)" % (player1.name, p1_delta, player2.name, p2_delta))

		print("New ratings:")
		for (i, (player, _)) in enumerate(players_scores):
			player.rating += score_changes[i]
			print("%s: %s (%+s)" % (player.name, player.rating, score_changes[i]))

	def calc_score_changes_2p(self, player_score_1, player_score_2, k_mult):
		"""Calculate the amount each player's rating should shift in a 2-player game.

		player_score_1 -- tuple of (player, score), player is a Player, score is numeric
		player_score_2 -- tuple of (player, score), player is a Player, score is numeric
		returns (rating_delta1, rating_delta2)
		"""
		(player1, score1) = player_score_1
		(player2, score2) = player_score_2

		p1_estimated_score = self.estimate_score_vs_one(player1.rating, player2.rating)
		p1_actual_score = Elo.get_actual_score(score1, score2)
		p1_rating_delta = (player1.k * k_mult) * (p1_actual_score - p1_estimated_score)

		p2_estimated_score = 1 - p1_estimated_score
		p2_actual_score = 1 - p1_actual_score
		p2_rating_delta = (player2.k * k_mult) * (p2_actual_score - p2_estimated_score)

		return (p1_rating_delta, p2_rating_delta)

	@staticmethod
	def get_actual_score(player_score, opponent_score):
		"""Calculate a player's performance rating given his and his opponent's score."""
		if player_score > opponent_score:
			return 1
		if player_score < opponent_score:
			return 0
		return 0.5

	def estimate_score_vs_one(self, player_rating, opponent_rating):
		"""Estimate a player's performance rating if they were to play against opponent."""
		return 1 / (1 + pow(10, clamp(opponent_rating - player_rating, -400, 400) / self.d_const))

def main():
	"""Test the Elo module."""
	elo = Elo()
	players = [Player(1, "Derg", 1150),
	           Player(2, "Starlis", 1200),
	           Player(3, "Pepega", 1000),]
	scores_list = [[4, 3, 1]]#, 1]]

	for scores in scores_list:
		print("New game! Scores:")
		for (i, score) in enumerate(scores):
			print("%s (rating: %s) lasted for %ss" % (players[i].name, players[i].rating, score))
		elo.report_game(list(zip(players, scores)))

	print(elo.estimate_score_vs_one(players[0].rating, players[1].rating))

if __name__ == '__main__':
	main()
