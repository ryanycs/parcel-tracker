import os

from app import bot

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if __name__ == '__main__':
    bot.run(token=DISCORD_BOT_TOKEN)