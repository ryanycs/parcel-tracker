import asyncio

import uvicorn
from fastapi import FastAPI, Request

PAYLOAD_SCHEMA = ["user_id", "platform", "order_id", "status", "time"]

webhook = FastAPI()
message_queue = asyncio.Queue()

@webhook.post("/webhook")
async def webhook_handler(request: Request):
    """
    Put the webhook data into the message queue
    """

    data = await request.json()

    if is_valid_payload(data):
        await message_queue.put(data)
        return {"message": "success"}
    else:
        return {"message": "invalid payload"}

def is_valid_payload(data: dict) -> bool:
    """
    Validate the webhook data

    Parameters
    ----------
    data : dict
        The webhook data

    Returns
    -------
    bool
        True if the data is valid, False otherwise
    """

    for key in PAYLOAD_SCHEMA:
        if key not in data:
            return False

    return True

def run_webhook_server():
    uvicorn.run(webhook, port=5000)