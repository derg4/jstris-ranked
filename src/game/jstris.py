#! /usr/bin/env python3
"""Handles the interaction with the jstris website."""

import pprint
import sys
import time

import asyncio

from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from credentials import jstris_creds
from model import GameInterface, GameState

JSTRIS_URL = 'https://jstris.jezevec10.com'

async def _run_in_executor(func, *args):
	loop = asyncio.get_running_loop()
	return await loop.run_in_executor(None, func, *args)

class DisconnectionException(Exception):
	"""An exception that is raised if we are disconnected from the jstris server."""

class QuitException(Exception):
	"""An exception that is raised if we have quit."""

class Jstris(GameInterface):
	"""Handles the interaction with the jstris website."""
	def __init__(self):
		profile = FirefoxProfile()
		profile.set_preference('media.volume_scale', '0.0') # Mute audio
		self.driver = Firefox(firefox_profile=profile)

		self.clients = None
		self.players = None
		self.join_link = None
		self.state = GameState.STOPPED

		self.quit_flag = False

	async def create_game(self, live=False):
		await _run_in_executor(self._create_game)
		self.state = GameState.CREATED

		return self.get_join_link()

	def get_join_link(self):
		return self.join_link

	async def watch_and_get_results(self):
		self.state = GameState.WATCHING

		while self.state != GameState.STOPPED and not self.quit_flag:
			try:
				result = await self._run_a_match()
				yield result
			except QuitException:
				break
		await _run_in_executor(self._log_in)

	async def quit(self): #TODO implement quit
		self.quit_flag = True

	async def force_quit(self): #TODO make this not break everything
		await _run_in_executor(self._log_in)
		self.quit_flag = True

	def get_state(self):
		return self.state

	###############################################################################
	# Private methods
	###############################################################################

	# Methods to create rooms

	def _create_game(self, live=False):
		"""Handles the whole set-up of creating or joining a new game"""
		self._log_in()
		if live:
			self._go_to_live()
		else:
			self._create_lobby()

		# Go to spectator mode
		self._send_chat('/spec', private_only=False)

	def _log_in(self):
		"""Ensures we are logged in, exits any lobby"""
		self._reset_game_info()

		self.driver.get(JSTRIS_URL + '/login')
		if jstris_creds['username'] in self.driver.title:
			return

		self.driver.find_element_by_name('name').send_keys(jstris_creds['username'])
		self.driver.find_element_by_name('password').send_keys(jstris_creds['password'] + Keys.ENTER)
		self._wait(EC.title_contains(jstris_creds['username']))

	def _reset_game_info(self):
		"""Reset any info we get in a game"""
		self.clients = None
		self.players = None
		self.join_link = None
		self.state = GameState.STOPPED

		self.quit_flag = False

	def _go_to_live(self):
		"""Goes to live, mocks private lobby."""
		self._log_in()
		self.driver.get(JSTRIS_URL)
		self._setup_script()
		self.join_link = 'live'

	def _create_lobby(self):
		"""Handles private game lobby creation."""
		self._go_to_practice()

		# Create a new lobby
		self._click_button('lobby')
		self._click_button('createRoomButton')

		# TODO Think about setting a preset? When things are more set in stone? Settings:
		self._check_box('isPrivate')
		self._select_radio('more_adv') # More settings: "All"
		self._check_box('hostStart')
		self._click_button('create')

		# Waits for lobby to load and gets a useful value
		self.join_link = self._get_join_link()
		self._setup_script()

	def _go_to_practice(self):
		self.driver.get(JSTRIS_URL + '/?play=2')

		# Wait for auto practice game to start... Find element that says GO! and wait for it to disappear
		ready_go_xpath = '//div[@id="stage"]/div[@class="gCapt"][last()]'
		self._wait(EC.visibility_of_element_located((By.XPATH, ready_go_xpath)))
		self._wait(EC.invisibility_of_element((By.XPATH, ready_go_xpath)))

	def _get_join_link(self):
		"""Wait for a join link to appear on the page, and return the URL contained within it."""
		join_link = self._wait(EC.presence_of_element_located((By.CLASS_NAME, 'joinLink')))
		return join_link.text

	def _setup_script(self):
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
			};""")
		time.sleep(0.1) #TODO hacky

	# Methods involved in running a match

	async def _run_a_match(self):
		while await self._wait_for_ok_to_start_game():
			if not self._have_players_joined() or not await _run_in_executor(self._start_game):
				self.state = GameState.WATCHING
				print('ERROR: Hmm... wait for ok to start game worked, but players haven\'t joined?')
				sys.stdout.flush()
				continue

			self._send_chat("Starting now!")
			self.state = GameState.RUNNING
			result = await self._wait_for_game_end()
			self.state = GameState.WATCHING
			return result
		return None

	async def _wait_for_ok_to_start_game(self):
		"""Wait for at least two registered players to join, and count down in chat to game start.

		Returns True if/when we can start the game, or False otherwise (if we time out)."""
		wait_time = 300
		wait_incr = 60
		periodic_msg = "Will wait for up to {:d}s for at least two registered players to join."
		start_time = time.perf_counter()
		end_time = start_time + wait_time

		while time.perf_counter() < end_time:
			if not self._have_players_joined():
				now = time.perf_counter()
				incrs_waited = int((now - start_time) / wait_incr)
				time_to_wait = (incrs_waited + 1) * wait_incr + start_time - now
				self._send_chat(periodic_msg.format(int(round(end_time - now))))

				try:
					await self._wait_for_players_to_join(time_to_wait)
				except TimeoutException:
					continue

			if await self._count_down_to_start_game():
				return True

		self._send_chat("Not enough registered players to start game.")
		return False

	_HAVE_TWO_PLAYERS_JOINED_JS = r"""
		var players = [];
		for (var i = 0; i < game.Live.players.length; i++) {
			var player = game.Live.players[i];
			var regex = /^<a href="\/u\/.+" target="_blank">.*<\/a>$/;
			if (game.Live.getName(player).match(regex)) {
				players.push(player);
			}
		}
		return players.length >= 2;
		"""

	def _have_players_joined(self):
		"""Check if 2 registered players have joined."""
		return self.driver.execute_script(Jstris._HAVE_TWO_PLAYERS_JOINED_JS)

	async def _wait_for_players_to_join(self, timeout):
		"""Wait for 2 registered players to join, using async_wait."""
		return await self._async_wait_js(Jstris._HAVE_TWO_PLAYERS_JOINED_JS, timeout=timeout)

	async def _count_down_to_start_game(self):
		"""Count down to the game start, checking intermittently if _have_players_joined()."""
		wait_time = 30
		wait_incr = 10
		time_waited = 0
		starting_in = 'Starting next game in {:d} seconds...'

		while time_waited < wait_time:
			if not self._have_players_joined():
				return False

			self._send_chat(starting_in.format(wait_time - time_waited))
			await asyncio.sleep(wait_incr)
			time_waited += wait_incr

		return self._have_players_joined()

	def _start_game(self):
		self._click_button('res')
		self._start_game_setup()
		return len(self.players) >= 2

	def _start_game_setup(self):
		self.driver.execute_script("window.gameResults = null")
		self.clients = self._get_clients()

		self.players = set()
		player_ids = self._get_registered_players()
		for player_id in player_ids:
			self.players.add(player_id)

		print("Players:")
		print(set(self.clients.get(pid, "UNKNOWN") for pid in self.players))
		sys.stdout.flush()

	async def _wait_for_game_end(self):
		"""Wait for a tetris game to end."""
		while True:
			self._check_connection()
			if self._has_game_ended():
				return self._get_game_results()
			await asyncio.sleep(0.5)

	def _check_connection(self):
		"""Raise an exception if the client javascript thinks we are disconnected."""
		self._wait_js("return window.game != null && window.game.Live.connected")

	def _has_game_ended(self):
		"""Returns True if a game has ended since calling start_game()"""
		return self.driver.execute_script("return gameResults != null")

	def _get_game_results(self):
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

	###############################################################################
	# Utility methods
	###############################################################################

	def _send_chat(self, text, private_only=True):
		"""Send text to the chat box."""
		if self.join_link != "live" or not private_only:
			self.driver.find_element_by_id('chatInput').send_keys(text + Keys.ENTER)

	def _get_clients(self):
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

	def _get_registered_players(self):
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

	def _click_button(self, element_id):
		"""Click a button on the page by element id."""
		self.driver.find_element_by_id(element_id).click()

	def _select_radio(self, element_id):
		"""Select a radio option on the page by element id."""
		self.driver.find_element_by_id(element_id).click()

	def _check_box(self, element_id):
		"""Check a checkbox on the page by element id."""
		box = self.driver.find_element_by_id(element_id)
		if not box.is_selected():
			box.click()

	def _uncheck_box(self, element_id):
		"""Uncheck a checkbox on the page by element id."""
		box = self.driver.find_element_by_id(element_id)
		if box.is_selected():
			box.click()

	def _wait(self, condition, timeout=10):
		"""Wait for a condition on the current webpage."""
		return WebDriverWait(self.driver, timeout).until(condition)

	def _wait_js(self, javascript, timeout=10):
		"""Wait for a javascript expression to return true."""
		return self._wait(lambda driver: driver.execute_script(javascript), timeout=timeout)

	async def _async_wait(self, condition, message='', timeout=10):
		"""Wait for a condition on the current webpage."""
		end_time = time.perf_counter() + timeout
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

	async def _async_wait_js(self, javascript, timeout=10):
		"""Wait for a javascript expression to return true."""
		return await self._async_wait(lambda driver: driver.execute_script(javascript), timeout=timeout)
