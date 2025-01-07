import os
from contextlib import asynccontextmanager
from typing import Optional

import requests
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mysql.connector import Error, connect
from parcel_tw import Platform, track
from pydantic import BaseModel

MYSQL_URL = os.getenv("MYSQL_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

PLATFORM_TO_ID = {"seven_eleven": 1, "family_mart": 2, "ok_mart": 3, "shopee": 4}


class Subscription(BaseModel):
    order_id: str
    email_id: Optional[str] = None
    discord_id: Optional[str] = None
    platform: str


# Schedule the background task
@asynccontextmanager
async def lifespan(app: FastAPI):
    trigger = IntervalTrigger(minutes=10)
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_subscriptions, trigger)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


# Define the API endpoints
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

        # Check if the subscription already exists
        cursor.execute(
            "SELECT * FROM Subscriptions WHERE order_id = %s AND platform_id = %s AND (email = %s OR discord_id = %s)",
            (order_id, platform_id, email, discord_id),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Subscription already exists")

        # Track the parcel status
        result = track(Platform(platform), order_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Parcel not found")

        # Check if the parcel status is already existed in the database
        cursor.execute(
            "SELECT * FROM Parcels WHERE platform_id = %s AND order_id = %s",
            (platform_id, order_id),
        )
        if not cursor.fetchone():
            # Insert the result into the database
            cursor.execute(
                """
            INSERT INTO Parcels (platform_id, order_id, status, update_time) VALUES (%s, %s, %s, %s)
            """,
                (platform_id, order_id, result.status, result.time),
            )

        # Insert the subscription into the database
        cursor.execute(
            """
        INSERT INTO Subscriptions (order_id, email, discord_id, platform_id)
        VALUES (%s, %s, %s, %s)
        """,
            (order_id, email, discord_id, platform_id),
        )
        conn.commit()

        return {"message": "success"}
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

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return {"message": "success"}
    except Error as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete subscription: {str(e)}"
        )
    finally:
        if conn:
            conn.close()


def check_subscriptions():
    # Connect to the database
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()

        # Get all subscriptions
        cursor.execute(
            """
        SELECT S.order_id, S.email, S.discord_id, PL.name, P.status, P.update_time
        FROM Subscriptions S
        JOIN Parcels P ON S.order_id = P.order_id AND S.platform_id = P.platform_id
        JOIN Platforms PL ON S.platform_id = PL.platform_id
        """
        )
        subscriptions = cursor.fetchall()

        for subscription in subscriptions:
            order_id, email, discord_id, platform, status, update_time = subscription
            result = track(Platform(platform), order_id)

            if result is None or result.status == status:
                continue

            # Update the parcel status in the database
            cursor.execute(
                "UPDATE Parcels SET status = %s, update_time = %s WHERE order_id = %s AND platform_id = %s",
                (result.status, result.time, order_id, PLATFORM_TO_ID[platform]),
            )

            # Send a notification to the user
            if email:
                # TODO: Send an email
                pass
            if discord_id:
                # send to discord webhook
                payload = {
                    "user_id": discord_id,
                    "platform": platform,
                    "order_id": order_id,
                    "status": result.status,
                    "time": result.time,
                }
                requests.post(DISCORD_WEBHOOK_URL, json=payload)

        conn.commit()
    except Error as e:
        if conn:
            conn.rollback()
        print(f"Failed to check subscriptions: {str(e)}")
    finally:
        if conn:
            conn.close()


def connect_to_mysql():
    """
    Establish a connection to the MySQL server.
    """

    try:
        conn = connect(
            host=MYSQL_URL,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
        )
        return conn
    except Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
