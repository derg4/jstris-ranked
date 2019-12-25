#! /usr/bin/env python3
""" The main module, which kicks off everything. """

import asyncio
import time

from jstris import Jstris

async def main():
	""" Sets up everything from the different modules and starts the discord bot. """
	try:
		jstris = Jstris()
		input('Gonna make a lobby')
		join_link = await jstris.get_lobby()
		print('Join link:', join_link)

		input('Gonna get an existing lobby')
		join_link = await jstris.get_lobby()
		print('Join link:', join_link)

		input('End?')
	except Exception as exc:
		print("Exc:", exc)
		raise exc
	finally:
		time.sleep(5)
		jstris.driver.quit()

if __name__ == '__main__':
	asyncio.run(main())
