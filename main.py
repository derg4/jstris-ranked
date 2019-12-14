#! /usr/bin/env python3

from selenium.webdriver import Firefox, FirefoxOptions, FirefoxProfile

from jstris import Jstris

def dump(obj):
	for attr in dir(obj):
		print("obj.%s = %r" % (attr, getattr(obj, attr)))

if __name__ == '__main__':
	profile = FirefoxProfile()
	profile.set_preference('media.volume_scale', '0.0') # Mute audio
	driver = Firefox(firefox_profile=profile)

	try:
		jstris = Jstris(driver)
		jstris.make_lobby()
		x = input('...')
	finally:
		driver.quit()
