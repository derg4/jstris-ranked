#! /usr/bin/env python3
""" The main module, which kicks off everything. """

import time

from selenium.webdriver import Firefox, FirefoxProfile

from jstris import Jstris

def set_up_jstris():
	""" Sets up the Selenium Firefox WebDriver, and initializes a new instance of Jstris with it. """
	profile = FirefoxProfile()
	profile.set_preference('media.volume_scale', '0.0') # Mute audio
	driver = Firefox(firefox_profile=profile)
	jstris = Jstris(driver)
	return jstris

def main():
	""" Sets up everything from the different modules and starts the discord bot. """
	try:
		jstris = set_up_jstris()
		jstris.log_in()
		jstris.go_to_live()
		jstris.enter_spectator_mode()
		jstris.setup_script()
		while True:
			jstris.start_game()
			jstris.wait_for_game_end()
			jstris.get_game_results()
	except Exception as exc:
		print("Exc:", exc)
		raise exc
	finally:
		time.sleep(5)
		jstris.driver.quit()

if __name__ == '__main__':
	main()
