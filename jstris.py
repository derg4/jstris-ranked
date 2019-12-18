#! /usr/bin/env python3
"""Handles the interaction with the jstris website."""

import pprint
import time
import sys

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from credentials import jstris_creds

JSTRIS_URL = 'https://jstris.jezevec10.com'

class Jstris:
	"""Handles the interaction with the jstris website."""
	def __init__(self, driver):
		self.driver = driver
		self.timeout = 10
		self.clients = None
		self.players = None

	def log_in(self):
		"""Log into the jstris website."""
		# TODO: Assumes we are logged out, should update later
		self.driver.get(JSTRIS_URL + '/login')
		self.driver.find_element_by_name('name').send_keys(jstris_creds['username'])
		self.driver.find_element_by_name('password').send_keys(jstris_creds['password'] + Keys.ENTER)
		self.wait(EC.title_contains(jstris_creds['username']))

	def set_up_lobby(self):
		"""Create a new private game lobby."""
		self.go_to_practice()
		join_link = self.__create_lobby()

		print(join_link)

		# Go to spectator mode
		self.send_chat('/spec')
		return join_link

	def go_to_live(self):
		"""Go to a live public game lobby."""
		self.driver.get(JSTRIS_URL)
		# TODO doesn't *properly* wait for page to load
		time.sleep(2)

	def go_to_practice(self):
		"""Go to a practice room."""
		self.driver.get(JSTRIS_URL + '/?play=2')

		# Wait for auto practice game to start... Find element that says GO! and wait for it to disappear
		ready_go_xpath = '//div[@id="stage"]/div[@class="gCapt"][last()]'
		self.wait(EC.visibility_of_element_located((By.XPATH, ready_go_xpath)))
		self.wait(EC.invisibility_of_element((By.XPATH, ready_go_xpath)))

	def __create_lobby(self):
		"""Handles private game lobby creation."""
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
		self.__setup_script()

		return join_link

	def __setup_script(self):
		"""Inject custom javascript onto the lobby page to keep track of the game state."""
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
			};""")
		time.sleep(1)

	def start_game(self):
		"""Start a game in the private room."""
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

		pprinter = pprint.PrettyPrinter()
		print("Clients:")
		pprinter.pprint(self.clients)
		print("Players:")
		print(self.players)
		sys.stdout.flush()

	def wait_for_game_end(self):
		"""Wait for a tetris game to end."""
		while True:
			self.check_connection()
			if self.has_game_ended():
				return
			time.sleep(0.5)

	def get_game_results(self):
		"""Get the results of the last game that was played in this room."""
		results = self.driver.execute_script("return window.gameResults")
		pprinter = pprint.PrettyPrinter()
		print("Results:")
		pprinter.pprint(results)
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

	def get_clients(self):
		"""Get the list of other people in the room, players or spectators.

		Returns a dictionary of player_id -> player_name
		"""
		return self.driver.execute_script("""
			var clients = {};
			for (client in game.Live.clients) {
				clients[client.toString()] = game.Live.clients[client].name;
			};
			return clients;
		""")

	def get_player_ids(self):
		"""Get the list of player ids of players playing, who have lost, or are waiting for a game."""
		return self.driver.execute_script("return game.Live.players")

	def check_connection(self):
		"""Raise an exception if the client javascript thinks we are disconnected."""
		if not self.driver.execute_script("return game.Live.connected"):
			print('We were disconnected!')
			raise DisconnectionException()

	def has_game_ended(self):
		"""Returns True if a game has ended since calling start_game()"""
		return self.driver.execute_script("return gameResults != null")

	def enter_spectator_mode(self):
		"""Send /spec to the chat, entering spectator mode."""
		self.send_chat('/spec')

	def send_chat(self, text):
		"""Send text to the chat box."""
		self.driver.find_element_by_id('chatInput').send_keys(text + Keys.ENTER)

	def click_button(self, element_id):
		"""Click a button on the page by element id."""
		self.driver.find_element_by_id(element_id).click()

	def select_radio(self, element_id):
		"""Select a radio option on the page by element id."""
		self.driver.find_element_by_id(element_id).click()

	def check_box(self, element_id):
		"""Check a checkbox on the page by element id."""
		box = self.driver.find_element_by_id(element_id)
		if not box.is_selected():
			box.click()

	def uncheck_box(self, element_id):
		"""Uncheck a checkbox on the page by element id."""
		box = self.driver.find_element_by_id(element_id)
		if box.is_selected():
			box.click()

	def get_join_link(self):
		"""Wait for a join link to appear on the page, and return the URL contained within it."""
		join_link = self.wait(EC.presence_of_element_located((By.CLASS_NAME, 'joinLink')))
		return join_link.text

	def wait(self, condition):
		"""Wait for a condition on the current webpage."""
		return WebDriverWait(self.driver, self.timeout).until(condition)

class DisconnectionException(Exception):
	"""An exception that is raised if we are disconnected from the jstris server."""
