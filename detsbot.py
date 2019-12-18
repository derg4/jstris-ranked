#! /usr/bin/env python3
"""Handles the interaction with discord."""

from discord.ext import commands
from discord import Game

from credentials import discord_creds

#import sys

# Discord.py:     https://discordpy.readthedocs.io/en/latest/api.html
# Discord.py ext: https://discordpy.readthedocs.io/en/latest/ext/commands/api.html

class DetsBot(commands.Cog):
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

def main():
	"""Starts up the DetsBot discord bot by itself, for testing"""
	cmd_prefix = '!'
	detsbot = commands.Bot(command_prefix=[cmd_prefix], description='Detectives\' Jstris Bot')
	detsbot.add_cog(DetsBot(detsbot))
	detsbot.run(discord_creds['token'])

if __name__ == '__main__':
	main()
