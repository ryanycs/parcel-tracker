import threading

from discord import File
from discord.ext import commands

from .parcel import Parcel
from .utils import create_embed, get_file_path
from .webhook import message_queue, run_webhook_server


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):

        # Start the FastAPI webhook server
        server = threading.Thread(target=run_webhook_server)
        server.start()

        # Start the webhook handler task
        self.loop.create_task(self.webhook_handler())

        # Load all cogs
        await self.add_cog(Parcel(self))

        # Sync application(slash) commands
        # await self.tree.sync()

        print(f'Logged in as {self.user} ({self.user.id})')

    async def webhook_handler(self):
        """
        Handle the webhook requests
        """

        while True:
            data = await message_queue.get()

            # Fetch the user
            user = await self.fetch_user(data["user_id"])
            embed = create_embed("包裹狀態更新", data)
            file = File(get_file_path(data["platform"]), filename=f"{data['platform']}.png")
            await user.send(embed=embed, file=file)

            message_queue.task_done()