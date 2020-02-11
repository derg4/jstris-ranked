#! /usr/bin/env python3
"""Handles the interaction with discord."""

import asyncio
import logging
import sys
import traceback

import discord
from discord.ext import commands
from discord import Embed, Game

from credentials import discord_creds

logger = logging.getLogger('detsbot')

# Discord.py:     https://discordpy.readthedocs.io/en/latest/api.html
# Discord.py ext: https://discordpy.readthedocs.io/en/latest/ext/commands/api.html

class JstrisCog(commands.Cog):
	"""Discord.py Cog, which implements the discord bot interface"""
	def __init__(self, bot, model=None):
		self.bot = bot
		self.model = model
		self.join_link = None
		self.quit_flag = False

	##### Bot Events #######################################################
	@commands.Cog.listener()
	async def on_ready(self):
		"""Bot event that gets called after initialization completes"""
		await self.bot.change_presence(activity=Game(name='%sjstris' % self.bot.command_prefix[0]))

	@commands.Cog.listener()
	async def on_message(self, message):
		"""Bot event that gets called when a user sends a message the bot sees"""
		if message.author.id == self.bot.user.id or message.content == '':
			return

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		"""Bot event that gets called when an error occurs"""

		if isinstance(error, discord.DiscordException):
			logger.warning('Error processing message %s: "%s", "%s"',
			               ctx.author, ctx.message.content, str(error))
			logger.warning(''.join(traceback.format_tb(error.__traceback__)))

			await ctx.send(str(error))
		else:
			logger.error('Error processing message %s: "%s", "%s"',
			             ctx.author, ctx.message.content, str(error))
			logger.error(''.join(traceback.format_tb(error.__traceback__)))

			await ctx.send('An error occurred processing your command, and it has been logged')

	##### Bot Commands #####################################################

	@commands.command()
	@commands.is_owner()
	async def watch_live(self, ctx):
		"""Either creates a lobby for a jstris match, or sends the link to an existing lobby."""
		if self.join_link is not None:
			if self.quit_flag:
				await ctx.send('Cancelled the quit command')
				self.quit_flag = False
			else:
				await ctx.send('Already watching a game: {}'.format(self.join_link))
			return
		self.quit_flag = False
		self.join_link = "Live"

		await ctx.send('Ok, watching')
		await self.model.watch_live()

		async for game_result in self.model.run_matches():
			try:
				await ctx.send(embed=JstrisCog.make_game_result_embed(game_result))
				# TODO: what do I do if the message is too long? >2000
			except Exception as exc:
				await self.model.quit_watching()
				self.join_link = None
				raise exc

			if self.quit_flag:
				await ctx.send('Stopping watching')
				await self.model.quit_watching()
				self.join_link = None
				return

	@staticmethod
	def make_game_result_embed(game_result):
		res_strs = []
		if game_result is None:
			res_strs.append('No change recorded (need at least 2 registered players)')
		else:
			last_place = None
			last_score = None

			for (i, (player, score, delta)) in enumerate(game_result):
				place = None
				if last_score is not None and score == last_score:
					place = last_place
				else:
					place = '#' + str(i + 1)
					last_place = place
					last_score = score

				if score == 0.0:
					place = 'DQ'
				res_strs.append('**{} - {}**: {:.2f} ({:+.2f})'.format(place, player.name, player.rating, delta))
		return Embed(title='New Game Result', description='\n'.join(res_strs))

	@commands.command(aliases=['tetris'])
	async def jstris(self, ctx):
		"""Either creates a lobby for a jstris match, or sends the link to an existing lobby."""
		try:
			if self.join_link is not None:
				if self.quit_flag:
					await ctx.send('Cancelled the quit command')
					self.quit_flag = False
				else:
					await ctx.send('Already watching a game: {}'.format(self.join_link))
				return
			self.quit_flag = False

			await ctx.send('Creating a lobby')
			self.join_link = await self.model.watch_lobby()
			await ctx.send('Join link: <%s>' % self.join_link)

			async for game_result in self.model.run_matches():
				try:
					await ctx.send(embed=JstrisCog.make_game_result_embed(game_result))
					# TODO: what do I do if the message is too long? >2000
				except Exception as exc:
					await self.model.quit_watching()
					self.join_link = None
					raise exc

				if self.quit_flag:
					await ctx.send('Stopping watching')
					await self.model.quit_watching()
					self.join_link = None
					return

			await ctx.send('Stopping watching (not enough players)')
			await self.model.quit_watching()
			self.join_link = None
		except Exception as exc:
			logger.exception(exc)
			logger.error('d/jstris error:' + ''.join(traceback.format_tb(exc.__traceback__)))
			raise exc

	@commands.command()
	async def leaderboard(self, ctx, page: int = 1):
		"""Displays the top rated players."""
		page_size = 15
		(players, num_pages) = self.model.get_leaderboard(page, page_size)

		if len(players) == 0 or page <= 0:
			await ctx.send('"page" should be a number from 1 to {}'.format(num_pages))
		else:
			desc = '\n'.join('**#{0} - {1.name}** ({1.rating:.2f})'.format(i + 1 + page_size*(page - 1), player)
			                 for (i, player) in enumerate(players))
			embed = Embed(title='Detstris Leaderboard', description=desc)
			embed.set_footer(text='Page {} / {}'.format(page, num_pages))
			await ctx.send(embed=embed)

	@commands.command()
	async def player(self, ctx, name: str):
		"""Shows info about the given player (jstris name)."""
		result = self.model.get_player_ranking(name)
		if result is None:
			await ctx.send('Player `{}` not found!'.format(name))
			return

		(player, ranking) = result
		await ctx.send('Player `{}` with rating `{:.2f}` is \\#{} on the leaderboard!'.format(
			player.name, player.rating, ranking))

	@commands.command()
	async def simulate(self, ctx, player1: str, player2: str):
		"""Displays the predicted win rate between two players."""
		p1_player = self.model.get_player(player1)
		p2_player = self.model.get_player(player2)

		messages = []
		if p1_player is None:
			messages.append('Player `{}` not found!'.format(player1))
		if p2_player is None:
			messages.append('Player `{}` not found!'.format(player2))

		if len(messages) == 0:
			p1_winrate = self.model.simulate_1v1(p1_player, p2_player)
			msg = 'According to the mathematical model:```\n' \
				'{0.name:16} ({0.rating:7.2f}) would win {1:5.2%} of the time.\n' \
				'{2.name:16} ({2.rating:7.2f}) would win {3:5.2%} of the time.```'
			messages.append(msg.format(p1_player, p1_winrate, p2_player, 1-p1_winrate))

		await ctx.send('\n'.join(messages))

	@commands.command()
	@commands.is_owner()
	async def reset_player(self, ctx, player: str):
		"""Resets the given player."""
		self.model.reset_player(player)
		await ctx.send('Done')

	@commands.command()
	@commands.is_owner()
	async def set_rating(self, ctx, player: str, rating: float):
		"""Sets the rating for the given player."""
		if self.model.set_player_rating(player, rating):
			await ctx.send('Done')
		else:
			await ctx.send('Player `{}` not found!'.format(player))

	@commands.command()
	@commands.is_owner()
	async def quit(self, ctx):
		"""Quits spectating after the current game."""
		if self.join_link is not None:
			self.quit_flag = True
			await ctx.send('Will stop watching after the current game')
		else:
			await ctx.send('Not watching a game')

	@commands.command('eval')
	@commands.is_owner()
	async def eval_cmd(self, ctx, *, expr):
		"""Calls eval() on expr, and sends back the result. Owner only."""
		#pylint: disable=eval-used
		ret = eval(expr, globals(), locals())
		await ctx.send(str(ret))

	@commands.command()
	@commands.is_owner()
	async def await_eval(self, ctx, *, expr):
		"""Calls eval() on expr, awaits the result, and sends back the result of that. Owner only."""
		#pylint: disable=eval-used
		ret = await eval(expr, globals(), locals())
		await ctx.send(str(ret))

async def start_bot(model=None):
	"""Starts up the DetsBot discord bot"""
	cmd_prefix = 'd/'
	detsbot = commands.Bot(command_prefix=[cmd_prefix], description='Detectives\' Jstris Bot')

	detsbot.add_cog(JstrisCog(detsbot, model))
	#await detsbot.run(discord_creds['token'])
	task = asyncio.create_task(detsbot.start(discord_creds['token']))
	return (detsbot, task)

def _dump(*args, **kwargs):
	print(*args, **kwargs)
	sys.stdout.flush()

async def _main():
	(_, task) = await start_bot()
	await task

if __name__ == '__main__':
	asyncio.run(_main())
