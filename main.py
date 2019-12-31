#! /usr/bin/env python3
""" The main module, which kicks off everything. """

import asyncio
import time

from database import MemoryDatabase
from jstris import Jstris
from model import JstrisModel

async def main():
	""" Sets up everything from the different modules and starts the discord bot. """
	try:
		database = MemoryDatabase()
		jstris = Jstris()
		model = JstrisModel(jstris, database)
		await model.watch_live()
	except Exception as exc:
		print("Exc:", exc)
		raise exc
	finally:
		time.sleep(5)
		jstris.driver.quit()

if __name__ == '__main__':
	asyncio.run(main())
