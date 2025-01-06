import os

import aiohttp
from discord import File, app_commands
from discord.ext import commands

from .config import PLATFORM_CHOICES, PLATFORM_TO_ENUM
from .utils import create_embed, get_file_path

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TRACKING_URL = f"{BACKEND_URL}/api/track"
SUBSCRIPTION_URL = f"{BACKEND_URL}/api/subscriptions"


class Parcel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("parcel")
    async def parcel(self, ctx):
        await ctx.send("Parcel command works!")

    @commands.hybrid_command("track", description="追蹤包裹")
    @app_commands.describe(platform="物流平台", order_id="取貨編號")
    @app_commands.choices(platform=PLATFORM_CHOICES)
    async def track(
        self, ctx, platform: str | None = None, order_id: str | None = None
    ):
        """
        Track the parcel status

        Example:

        `/track seven_eleven 123456789`
        """

        # Check if platform and order_id are provided
        if not platform or not order_id:
            await ctx.send("參數輸入有錯誤喔！")
            return

        # Check if platform is valid
        platform = platform.lower()
        if platform not in PLATFORM_TO_ENUM:
            await ctx.send("查不到這個物流平台!")
            return

        # Convert platform to enum value
        platform = PLATFORM_TO_ENUM[platform].value

        # Fetch the parcel status
        url = f"{TRACKING_URL}/{platform}/{order_id}"
        async with aiohttp.request("GET", url) as response:
            if response.status != 200:
                await ctx.send("找不到這個包裹！")
                return

            # Send the parcel status to the user
            user_id = ctx.author.id
            embed = create_embed("包裹狀態", await response.json())
            file = File(get_file_path(platform), filename=f"{platform}.png")

            await ctx.send(f"<@{user_id}>", embed=embed, file=file)

    @commands.hybrid_command("subscribe", description="訂閱包裹狀態")
    @app_commands.describe(platform="物流平台", order_id="取貨編號")
    @app_commands.choices(platform=PLATFORM_CHOICES)
    async def subscribe(
        self, ctx, platform: str | None = None, order_id: str | None = None
    ):
        # Check if platform and order_id are provided
        if not platform or not order_id:
            await ctx.send("參數輸入有錯誤喔！")
            return

        # Check if platform is valid
        platform = platform.lower()
        if platform not in PLATFORM_TO_ENUM:
            await ctx.send("查不到這個物流平台!")
            return

        # Convert platform to enum value
        platform = PLATFORM_TO_ENUM[platform].value

        user_id = ctx.author.id
        payload = {
            "discord_id": user_id,
            "platform": platform,
            "order_id": order_id,
        }

        async with aiohttp.request("POST", SUBSCRIPTION_URL, json=payload) as response:
            if response.status == 200:
                await ctx.send("訂閱成功！")
            elif response.status == 409:
                await ctx.send("已訂閱過此包裹！")
            else:
                await ctx.send("訂閱失敗，請稍後再試！")

    @commands.hybrid_command("unsubscribe", description="取消訂閱包裹狀態")
    @app_commands.describe(platform="物流平台", order_id="取貨編號")
    @app_commands.choices(platform=PLATFORM_CHOICES)
    async def unsubscribe(
        self, ctx, platform: str | None = None, order_id: str | None = None
    ):
        # Check if platform and order_id are provided
        if not platform or not order_id:
            await ctx.send("參數輸入有錯誤喔！")
            return

        # Check if platform is valid
        platform = platform.lower()
        if platform not in PLATFORM_TO_ENUM:
            await ctx.send("查不到這個物流平台!")
            return

        # Convert platform to enum value
        platform = PLATFORM_TO_ENUM[platform].value

        user_id = ctx.author.id
        payload = {
            "discord_id": user_id,
            "platform": platform,
            "order_id": order_id,
        }

        async with aiohttp.request(
            "DELETE", SUBSCRIPTION_URL, json=payload
        ) as response:
            if response.status == 200:
                await ctx.send("取消訂閱成功！")
            elif response.status == 404:
                await ctx.send("找不到訂閱的包裹！")
            else:
                await ctx.send("取消訂閱失敗，請稍後再試！")
                await ctx.send("取消訂閱失敗，請稍後再試！")
