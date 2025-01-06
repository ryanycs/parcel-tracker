import os

from discord import Embed


def create_embed(title: str, response: dict) -> Embed:
    """
    Create a Discord embed message
    """

    embed = Embed(title=title, description=f"取貨編號: {response['order_id']}")
    embed.set_thumbnail(url=f"attachment://{response['platform']}.png")
    embed.add_field(name="包裹狀態", value=response["status"])
    if response.get("time") is not None:
        embed.add_field(name="更新時間", value=response["time"])

    return embed


def get_file_path(platform: str) -> str:
    """
    Get the file path of the platform image
    """

    return f"{os.path.dirname(os.path.abspath(__file__))}/static/imgs/{platform}.png"
