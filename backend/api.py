import uvicorn
from fastapi import FastAPI, HTTPException
from parcel_tw import Platform, track
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import Error


app = FastAPI()

class ID(BaseModel):
    order_id :str
    platform_id :int

class Subscription(BaseModel):
    order_id: str
    email_id: Optional[str] = None
    discord_id: Optional[str] = None
    platform: str

# Platform mapping
PLATFORM = [
    "seven_eleven",
    "family_mart",
    "ok_mart",
    "shopee",
]

platform_to_id = {"seven_eleven": 1, "family_mart": 2, "ok_mart": 3, "shopee": 4}

def connect_to_mysql():
    """Establish a connection to the MySQL server."""
    try:
        conn = mysql.connector.connect(
            #host="mysql_server",
            host="127.0.0.1",
            user="user",
            password="passwd",
            database="shopping"
        )
        return conn

    except Error as e:
       raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

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

    if email is None and discord_id is None:
        raise HTTPException(status_code=400, detail="Either 'email' or 'discord_id' must be provided.")


    platform_id = platform_to_id.get(platform)
    if not platform_id:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

    conn = None
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO Subscriptions (order_id, email, discord_id, platform_id)
        VALUES (%s, %s, %s, %s)
        """, (order_id, email, discord_id, platform_id))
        conn.commit()

        return {"message": "Subscription created"}

    except Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")

    finally:
        if conn:
            conn.close()

@app.delete("/api/subscriptions/{order_id}")
async def unsubscription(id: ID):
    conn = None
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Subscriptions where order_id = %s AND platform_id = %s", (id.order_id, id.platform_id), )
        conn.commit()

        # Delete return conut
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return {"message": f"Subscription {id.order_id} deleted"}

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete subscription: {str(e)}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    uvicorn.run(app)
