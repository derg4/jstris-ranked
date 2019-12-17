#! /usr/bin/env python3

from player import Player

def clamp(n, smallest, largest):
	return max(smallest, min(n, largest))

class Elo:
	def __init__(self, d=400):
		self.d = d
		pass

	# Takes a list of (player, score) and adjusts the players' skill ratings based on performance
	def report_game(self, players_scores):
		num_players = len(players_scores)
		score_changes = [0 for _ in range(num_players)]

		k_mult = 1 / (num_players - 1)

		# For each matchup, simulate a game
		for i in range(num_players - 1):
			(p1, score1) = players_scores[i]
			for j in range(i + 1, num_players):
				(p2, score2) = players_scores[j]
				(p1_delta, p2_delta) = self.calc_score_changes_2p(p1, score1, p2, score2, k_mult)
				score_changes[i] += p1_delta
				score_changes[j] += p2_delta
				print("Score change: %s (%+s) vs %s (%+s)" % (p1.name, p1_delta, p2.name, p2_delta))

		print("New ratings:")
		for (i, (player, _)) in enumerate(players_scores):
			player.rating += score_changes[i]
			print("%s: %s (%+s)" % (player.name, player.rating, score_changes[i]))

	# Calculates the amount each player's rating should shift in a 2-player game, returns (rating_delta1, rating_delta2)
	def calc_score_changes_2p(self, player1, score1, player2, score2, k_mult):
		p1_estimated_score = self.estimate_score_vs_one(player1.rating, player2.rating)
		p1_actual_score = self.get_actual_score(score1, score2)
		p1_rating_delta = (player1.k * k_mult) * (p1_actual_score - p1_estimated_score)

		p2_estimated_score = 1 - p1_estimated_score
		p2_actual_score = 1 - p1_actual_score
		p2_rating_delta = (player2.k * k_mult) * (p2_actual_score - p2_estimated_score)

		return (p1_rating_delta, p2_rating_delta)

	def get_actual_score(self, player_score, opponent_score):
		if player_score > opponent_score:
			return 1
		elif player_score < opponent_score:
			return 0
		else:
			return 0.5

	def estimate_score_vs_one(self, player_rating, opponent_rating):
		return 1 / (1 + pow(10, clamp(opponent_rating - player_rating, -400, 400) / self.d))

if __name__ == '__main__':
	elo = Elo()
	players = [
		Player(1, "Derg",    1150),
		Player(2, "Starlis", 1200),
		Player(3, "Pepega",  1000),]
	scores_list = [[2, 3, 1]]#, 1]]

	for scores in scores_list:
		print("New game! Scores:")
		for (i, score) in enumerate(scores):
			print("%s (rating: %s) lasted for %ss" % (players[i].name, players[i].rating, score))
		elo.report_game(list(zip(players, scores)))

	print(elo.estimate_score_vs_one(players[0].rating, players[1].rating))
