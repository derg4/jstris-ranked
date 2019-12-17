#! /usr/bin/env python3

from selenium.webdriver import Firefox, FirefoxOptions, FirefoxProfile

from jstris import Jstris

import time
import sys

if __name__ == '__main__':
	profile = FirefoxProfile()
	profile.set_preference('media.volume_scale', '0.0') # Mute audio
	driver = Firefox(firefox_profile=profile)

	try:
		jstris = Jstris(driver)
		jstris.log_in()
		jstris.go_to_live()
		jstris.enter_spectator_mode()
		jstris.setup_script()
		while True:
			jstris.start_game()
			jstris.wait_for_game_end()
			jstris.get_game_results()
	except Exception as e:
		print("Exc:", e)
		input("...")
		raise e
	finally:
		time.sleep(5)
		driver.quit()
