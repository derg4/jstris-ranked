#! /usr/bin/env python3
"""Handles the interaction with the jstris website."""

import pprint
import time
import sys

import asyncio

from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from credentials import jstris_creds

JSTRIS_URL = 'https://jstris.jezevec10.com'

class Jstris:
	"""Handles the interaction with the jstris website."""
	def __init__(self):
		profile = FirefoxProfile()
		profile.set_preference('media.volume_scale', '0.0') # Mute audio
		self.driver = Firefox(firefox_profile=profile)

		self.timeout = 10
		self.clients = None
		self.players = None
		self.lobby = None

	async def get_lobby(self):
		"""Get the current lobby, or create a new one. Returns the join link."""
		if self.lobby is not None:
			return self.lobby

		loop = asyncio.get_running_loop()
		join_link = await loop.run_in_executor(None, self.__get_lobby)
		return join_link

	def __get_lobby(self):
		if self.lobby is None:
			self.__log_in()
			self.lobby = self.__set_up_lobby()

		return self.lobby

	async def log_in(self):
		"""Usually unneeded, logs in"""
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, self.__log_in)

	def __log_in(self):
		self.driver.get(JSTRIS_URL + '/login')
		if jstris_creds['username'] in self.driver.title:
			return

		self.driver.find_element_by_name('name').send_keys(jstris_creds['username'])
		self.driver.find_element_by_name('password').send_keys(jstris_creds['password'] + Keys.ENTER)
		self.wait(EC.title_contains(jstris_creds['username']))

	def __set_up_lobby(self):
		"""Create a new private game lobby. Returns the join link for that lobby."""
		self.__reset_lobby_info()
		self.__go_to_practice()
		join_link = self.__create_lobby()

		# Go to spectator mode
		self.__send_chat('/spec')
		return join_link

	def __create_lobby(self):
		"""Handles private game lobby creation."""
		# Create a new lobby
		self.__click_button('lobby')
		self.__click_button('createRoomButton')

		# TODO Think about setting a preset? When things are more set in stone? Settings:
		self.__check_box('isPrivate')
		self.__select_radio('more_adv') # More settings: "All"
		self.__check_box('hostStart')
		self.__click_button('create')

		# Waits for lobby to load and gets a useful value
		join_link = self.__get_join_link()
		self.__setup_script()

		return join_link

	async def go_to_live(self):
		"""Go to a live public game lobby."""
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, self.__go_to_live)

		signedin_xpath = '//div[@class="chl srv"][contains(text(), "You are signed in as")]'
		await self.async_wait(EC.presence_of_element_located((By.XPATH, signedin_xpath)))

	def __go_to_live(self):
		self.__log_in()
		self.driver.get(JSTRIS_URL)
		self.__setup_script()

	async def go_to_practice(self):
		"""Go to a practice room."""
		loop = asyncio.get_running_loop()
		return await loop.run_in_executor(None, self.__go_to_practice)

	def __go_to_practice(self):
		self.driver.get(JSTRIS_URL + '/?play=2')

		# Wait for auto practice game to start... Find element that says GO! and wait for it to disappear
		ready_go_xpath = '//div[@id="stage"]/div[@class="gCapt"][last()]'
		self.wait(EC.visibility_of_element_located((By.XPATH, ready_go_xpath)))
		self.wait(EC.invisibility_of_element((By.XPATH, ready_go_xpath)))

	def __reset_lobby_info(self):
		self.clients = None
		self.players = None
		self.lobby = None

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
		time.sleep(0.1)

	async def start_game_live(self):
		"""Simulate starting a game (when we're watching live)."""
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, self.__start_game_setup)

	async def start_game(self):
		"""Start a game in the private room."""
		# TODO actually start game if we're in a private room
		loop = asyncio.get_running_loop()
		await loop.run_in_executor(None, self.__start_game)

	def __start_game(self):
		self.__click_button('res')
		self.__start_game_setup()

	def __start_game_setup(self):
		self.driver.execute_script("window.gameResults = null")
		self.clients = self.get_clients()

		self.players = set()
		player_ids = self.get_registered_players()
		for player_id in player_ids:
			self.players.add(player_id)

		print("Players:")
		print(set(self.clients.get(pid, "UNKNOWN") for pid in self.players))
		sys.stdout.flush()

	async def wait_for_game_end(self):
		"""Wait for a tetris game to end."""
		while True:
			self.check_connection()
			if self.has_game_ended():
				return
			await asyncio.sleep(0.5)

	def get_game_results(self):
		"""Get the results of the last game that was played in this room."""
		results = self.driver.execute_script("return window.gameResults")
		self.driver.execute_script("window.oldGameResults = window.gameResults")
		results_players = set()

		results_list = []
		for result in results:
			player_id = result['c']
			name = self.clients.get(player_id, 'UNKNOWN')
			if result['forfeit']:
				continue
			if player_id not in self.players:
				print('Ignoring %s, unregistered' % name)
				continue

			results_players.add(player_id)
			results_list.append({'id': result['c'], 'name': name, 'score': float(result['t'])})

		missing_players = self.players - results_players
		for player_id in missing_players:
			results_list.append({'id': player_id,
			                     'name': self.clients.get(player_id, 'UNKNOWN'),
			                     'score': 0.0})

		print("Results:")
		pprinter = pprint.PrettyPrinter()
		pprinter.pprint(results_list)
		sys.stdout.flush()

		return results_list

	def get_clients(self):
		"""Get the list of other people in the room, players or spectators.

		Returns a dictionary of player_id -> player_name
		"""
		raw_clients = self.driver.execute_script("""
			var clients = {};
			for (client in window.game.Live.clients) {
				clients[client] = window.game.Live.clients[client].name;
			};
			return clients;
		""")

		clients = {}
		for (pid_str, name) in raw_clients.items():
			clients[int(pid_str)] = name
		return clients

	def get_registered_players(self):
		"""Get the list of players who are logged in."""
		return self.driver.execute_script(r"""
			var players = [];
			for (var i = 0; i < game.Live.players.length; i++) {
				var player = game.Live.players[i];
				var regex = /^<a href="\/u\/.+" target="_blank">.*<\/a>$/;
				if (game.Live.getName(player).match(regex)) {
					players.push(player);
				}
			}
			return players;
		""")

	def get_player_ids(self):
		"""Get the list of player ids of players playing, who have lost, or are waiting for a game."""
		return self.driver.execute_script("return game.Live.players")

	def check_connection(self):
		"""Raise an exception if the client javascript thinks we are disconnected."""
		self.wait_js("return window.game != null && window.game.Live.connected")

	def has_game_ended(self):
		"""Returns True if a game has ended since calling start_game()"""
		return self.driver.execute_script("return gameResults != null")

	def enter_spectator_mode(self):
		"""Send /spec to the chat, entering spectator mode."""
		self.__send_chat('/spec')

	def __send_chat(self, text):
		"""Send text to the chat box."""
		self.driver.find_element_by_id('chatInput').send_keys(text + Keys.ENTER)

	def __click_button(self, element_id):
		"""Click a button on the page by element id."""
		self.driver.find_element_by_id(element_id).click()

	def __select_radio(self, element_id):
		"""Select a radio option on the page by element id."""
		self.driver.find_element_by_id(element_id).click()

	def __check_box(self, element_id):
		"""Check a checkbox on the page by element id."""
		box = self.driver.find_element_by_id(element_id)
		if not box.is_selected():
			box.click()

	def __uncheck_box(self, element_id):
		"""Uncheck a checkbox on the page by element id."""
		box = self.driver.find_element_by_id(element_id)
		if box.is_selected():
			box.click()

	def __get_join_link(self):
		"""Wait for a join link to appear on the page, and return the URL contained within it."""
		#join_link = await self.async_wait(EC.presence_of_element_located((By.CLASS_NAME, 'joinLink')))
		join_link = self.wait(EC.presence_of_element_located((By.CLASS_NAME, 'joinLink')))
		return join_link.text

	def wait(self, condition):
		"""Wait for a condition on the current webpage."""
		return WebDriverWait(self.driver, self.timeout).until(condition)

	def wait_js(self, javascript):
		"""Wait for a javascript expression to return true."""
		return self.wait(lambda driver: driver.execute_script(javascript))

	async def async_wait(self, condition, message=''):
		"""Wait for a condition on the current webpage."""
		end_time = time.perf_counter() + self.timeout
		screen = None
		stacktrace = None
		while True:
			try:
				value = condition(self.driver)
				if value:
					return value
			except NoSuchElementException as exc:
				screen = getattr(exc, 'screen', None)
				stacktrace = getattr(exc, 'stacktrace', None)
			await asyncio.sleep(0.1)
			if time.perf_counter() > end_time:
				raise TimeoutException(message, screen, stacktrace)

class DisconnectionException(Exception):
	"""An exception that is raised if we are disconnected from the jstris server."""

#class TimeoutException(Exception):
#	"""An exception that is raised if we are timed out while waiting for something."""
