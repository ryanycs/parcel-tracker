import os
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from mysql.connector import Error, connect
from parcel_tw import Platform, track
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")

PLATFORM_TO_ID = {"seven_eleven": 1, "family_mart": 2, "ok_mart": 3, "shopee": 4}

app = FastAPI()


class Subscription(BaseModel):
    order_id: str
    email_id: Optional[str] = None
    discord_id: Optional[str] = None
    platform: str


@app.get("/")
async def root():
    return {"message": "It works!"}


@app.get("/api/track/{platform}/{order_id}")
async def track_parcel(platform: str, order_id: str):
    result = track(Platform(platform), order_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    else:
        response = {
            "platform": result.platform,
            "order_id": result.order_id,
            "status": result.status,
            "time": result.time,
        }
        return response


@app.post("/api/subscriptions")
async def subscription(sub: Subscription):
    platform = sub.platform
    order_id = sub.order_id
    email = sub.email_id
    discord_id = sub.discord_id

    # Check if email or discord_id is provided
    if email is None and discord_id is None:
        raise HTTPException(
            status_code=400, detail="Either 'email' or 'discord_id' must be provided."
        )

    # Convert platform to platform_id
    platform_id = PLATFORM_TO_ID.get(platform)
    if not platform_id:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

    conn = None
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute(
            """
        INSERT INTO Subscriptions (order_id, email, discord_id, platform_id)
        VALUES (%s, %s, %s, %s)
        """,
            (order_id, email, discord_id, platform_id),
        )
        conn.commit()

        return {"message": "Subscription created"}
    except Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create subscription: {str(e)}"
        )
    finally:
        if conn:
            conn.close()


@app.delete("/api/subscriptions")
async def unsubscription(sub: Subscription):
    platform = sub.platform
    order_id = sub.order_id
    email = sub.email_id
    discord_id = sub.discord_id

    # Convert platform to platform_id
    platform_id = PLATFORM_TO_ID.get(platform)
    if not platform_id:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

    conn = None
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Subscriptions where order_id = %s AND platform_id = %s AND (email = %s OR discord_id = %s) ",
            (order_id, platform_id, email, discord_id),
        )
        conn.commit()

        # Delete return conut
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return {"message": f"Subscription {id.order_id} deleted"}
    except Error as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete subscription: {str(e)}"
        )
    finally:
        if conn:
            conn.close()


def connect_to_mysql():
    """
    Establish a connection to the MySQL server.
    """

    try:
        conn = connect(
            host=DATABASE_URL,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
        )
        return conn

    except Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app)
