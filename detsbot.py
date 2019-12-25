#! /usr/bin/env python3
"""Handles the interaction with discord."""

from discord.ext import commands
from discord import Game

from credentials import discord_creds

# Discord.py:     https://discordpy.readthedocs.io/en/latest/api.html
# Discord.py ext: https://discordpy.readthedocs.io/en/latest/ext/commands/api.html

class JstrisCog(commands.Cog):
	"""Discord.py Cog, which implements the discord bot interface"""
	def __init__(self, bot):
		self.bot = bot

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
		await ctx.send(str(error))
		if not isinstance(error, commands.MissingRequiredArgument):
			raise error

	##### Bot Commands #####################################################

	@commands.command()
	async def jstris(self, ctx):
		"""Either creates a lobby for a jstris match, or sends the link to an existing lobby."""
		await ctx.send('Not yet, but soon')

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

def start_bot():
	"""Starts up the DetsBot discord bot"""
	cmd_prefix = '!'
	detsbot = commands.Bot(command_prefix=[cmd_prefix], description='Detectives\' Jstris Bot')
	detsbot.add_cog(JstrisCog(detsbot))
	detsbot.run(discord_creds['token'])

if __name__ == '__main__':
	start_bot()
