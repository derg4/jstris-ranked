#! /usr/bin/env python3

from credentials import jstris_creds

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import operator
import pprint
import time
import sys

jstris_url = 'https://jstris.jezevec10.com'

class Jstris:
	def __init__(self, driver):
		self.driver = driver
		self.timeout = 10

	def log_in(self):
		# TODO: Assumes we are logged out, should update later
		self.driver.get(jstris_url + '/login')
		self.driver.find_element_by_name('name').send_keys(jstris_creds['username'])
		self.driver.find_element_by_name('password').send_keys(jstris_creds['password'] + Keys.ENTER)
		self.wait(EC.title_contains(jstris_creds['username']))

	def set_up_lobby(self):
		self.go_to_practice()
		join_link = self.create_lobby()

		print(join_link)

		# Go to spectator mode
		self.send_chat(self, '/spec')
		return join_link

	def go_to_live(self):
		self.driver.get(jstris_url)
		# TODO doesn't *properly* wait for page to load
		time.sleep(2)

	def go_to_practice(self):
		self.driver.get(jstris_url + '/?play=2')

		# Wait for automatic practice game to start... Find element that says GO! and wait for it to disappear
		ready_go_xpath = '//div[@id="stage"]/div[@class="gCapt"][last()]'
		self.wait(EC.visibility_of_element_located((By.XPATH, ready_go_xpath)))
		self.wait(EC.invisibility_of_element((By.XPATH, ready_go_xpath)))

	def create_lobby(self):
		# Create a new lobby
		self.click_button('lobby')
		self.click_button('createRoomButton')

		# TODO Think about setting a preset? When things are more set in stone? Settings:
		self.check_box('isPrivate')
		self.select_radio('more_adv') # More settings: "All"
		self.check_box('hostStart')
		self.click_button('create')

		# Waits for lobby to load and gets a useful value
		join_link = self.get_join_link()
		self.setup_script()

		return join_link

	def setup_script(self):
		self.driver.execute_script("""
			window.game = null;
			var gud = Game.prototype.update;
			Game.prototype.update = function() {
				gud.apply(this, arguments);
				window.game = this;
			};

			window.gameResults = null;
			var dr = Live.prototype.displayResults;
			Live.prototype.displayResults = function() {
				dr.apply(this, arguments);
				window.gameResults = arguments[0];
				console.log("Game ended!"); // TODO remove
			};""");
		time.sleep(1)

	def start_game(self):
		self.driver.execute_script("window.gameResults = null")
		#self.click_button('res')
		self.clients = self.get_clients()

		player_ids = self.get_player_ids()
		self.players = set()
		for player_id in player_ids:
			pid_str = str(player_id)
			if pid_str in self.clients:
				self.players.add(self.clients[pid_str])
			else:
				print("Player ID %s not in clients!" % pid_str)

		pp = pprint.PrettyPrinter()
		print("Clients:")
		pp.pprint(self.clients)
		print("Players:")
		print(self.players)
		sys.stdout.flush()

	def wait_for_game_end(self):
		while True:
			self.check_connection()
			if self.has_game_ended():
				return
			time.sleep(0.5)

	def get_game_results(self):
		results = self.driver.execute_script("return window.gameResults")
		pp = pprint.PrettyPrinter()
		print("Results:")
		pp.pprint(results)
		results_players = set()

		for (place, result) in enumerate(results, start=1):
			pid_str = str(result['c'])
			if pid_str in self.clients:
				name = self.clients[pid_str]
				results_players.add(name)
			else:
				name = "UNKNOWN"

			if not result['forfeit']:
				print("#%2s: %s" % (place, name))
			else:
				print(" FF: %s" % name)

		missing_players = self.players - results_players
		for name in missing_players:
			print(" MP: %s" % name)

		sys.stdout.flush()

	# Returns a dictionary of player id string -> player name
	def get_clients(self):
		return self.driver.execute_script("""
			var clients = {};
			for (client in game.Live.clients) {
				clients[client.toString()] = game.Live.clients[client].name;
			};
			return clients;
		""")

	def get_player_ids(self):
		return self.driver.execute_script("return game.Live.players")

	def check_connection(self):
		if not self.driver.execute_script("return game.Live.connected"):
			print('We were disconnected!')
			raise DisconnectionException()

	def has_game_ended(self):
		return self.driver.execute_script("return gameResults != null")

	def enter_spectator_mode(self):
		self.send_chat('/spec')

	def send_chat(self, text):
		self.driver.find_element_by_id('chatInput').send_keys(text + Keys.ENTER)

	def click_button(self, element_id):
		self.driver.find_element_by_id(element_id).click()

	def select_radio(self, element_id):
		self.driver.find_element_by_id(element_id).click()

	def check_box(self, element_id):
		box = self.driver.find_element_by_id(element_id)
		if not box.is_selected():
			box.click()

	def uncheck_box(self, element_id):
		box = self.driver.find_element_by_id(element_id)
		if box.is_selected():
			box.click()

	def get_players(self):
		players_xpath = '//div[@id="gameSlots"]/div[@class="slot" or @class="slot np"]/span'
		players = [element.text for element in self.driver.find_elements_by_xpath(players_xpath) if element.text != '']
		# This grabs current players, players who have died, and players lined up for next round
		# Probably not so good... Hard to tell difference between active players and players lined up for next round
		return players

	def get_join_link(self):
		join_link = self.wait(EC.presence_of_element_located((By.CLASS_NAME, 'joinLink')))
		return join_link.text

	def wait(self, condition):
		return WebDriverWait(self.driver, self.timeout).until(condition)

class DisconnectionException(Exception):
	pass
