import uvicorn
from fastapi import FastAPI, HTTPException
from parcel_tw import Platform, track

app = FastAPI()

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
async def subscription():
    return {"message": "Subscription created"}

@app.delete("/api/subscriptions")
async def unsubscription():
    return {"message": "Subscription deleted"}

if __name__ == "__main__":
    uvicorn.run(app)