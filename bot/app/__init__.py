import discord

from .bot import Bot

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix='!', intents=intents)