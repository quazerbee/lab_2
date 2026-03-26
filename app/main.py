from fastapi import FastAPI
from app.database import engine, Base
from app.models.item import Item
from app.routers.item_router import router as item_router
from app.database import Base
from app.models.item import Item


app = FastAPI()
app.include_router(item_router)

@app.get("/")
def root():
    return {"message": "API is working"}

@app.get("/db-check")
def check_db():
    try:
        connection = engine.connect()
        connection.close()
        return {"message": "DB connected!"}
    except:
        return {"message": "DB connection failed"}