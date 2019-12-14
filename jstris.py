#! /usr/bin/env python3

from credentials import jstris_creds

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sys
def debug(msg):
	print(msg)
	sys.stdout.flush()

jstris_url = 'https://jstris.jezevec10.com'

class Jstris:
	def __init__(self, driver):
		self.driver = driver
		self.timeout = 10
		self.log_in()

	def log_in(self):
		# TODO: Assumes we are logged out, should update later
		self.driver.get(jstris_url + '/login')
		self.driver.find_element_by_name('name').send_keys(jstris_creds['username'])
		self.driver.find_element_by_name('password').send_keys(jstris_creds['password'] + Keys.ENTER)
		self.wait(EC.title_contains(jstris_creds['username']))

	def make_lobby(self):
		# Navigate to "practice" and make a lobby from there
		self.driver.get(jstris_url + '/?play=2')

		# Wait for automatic practice game to start... Find element that says GO! and wait for it to disappear
		ready_go_xpath = '//div[@id="stage"]/div[@class="gCapt"][last()]'
		self.wait(EC.visibility_of_element_located((By.XPATH, ready_go_xpath)))
		self.wait(EC.invisibility_of_element((By.XPATH, ready_go_xpath)))

		# Create a new lobby
		self.click_button('lobby')
		self.click_button('createRoomButton')
		# TODO Think about setting a preset? When things are more set in stone? Settings:
		self.check_box('isPrivate')
		self.select_radio('more_adv') # More settings: "All"
		self.check_box('hostStart')
		self.click_button('create')

		# Wait for lobby to load (with join link)
		join_link = self.wait(EC.presence_of_element_located((By.CLASS_NAME, 'joinLink')))
		print(join_link.text)

		# Go to spectator mode
		self.driver.find_element_by_id('chatInput').send_keys('/spec' + Keys.ENTER)
		return join_link.text

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

	def wait(self, condition):
		return WebDriverWait(self.driver, self.timeout).until(condition)
