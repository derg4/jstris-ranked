#! /usr/bin/env python3
""" The main module, which kicks off everything. """

import asyncio
import sys
import time

from db import SQLiteDatabase
import ui
from game import Jstris
from model import JstrisModel

def dump(*args, **kwargs):
	"""Alias for print and flush stdout."""
	print(*args, **kwargs)
	sys.stdout.flush()

async def main():
	"""Sets up everything from the different modules and starts the discord bot."""
	try:
		database = SQLiteDatabase('players.db')
		jstris = Jstris()
		model = JstrisModel(jstris, database)

		dump('starting bot...')
		(bot, task) = await ui.start_bot(model)
		dump('bot started...')
		await task
		input('...')

	except Exception as exc:
		print("Exc:", exc)
		raise exc
	finally:
		time.sleep(5)
		await bot.close()
		jstris.driver.quit()

if __name__ == '__main__':
	asyncio.run(main())
