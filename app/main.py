from fastapi import FastAPI
from app.database import engine, Base
from app.models.item import Item
from app.routers.item_router import router as item_router
from fastapi import Request
from fastapi.responses import JSONResponse


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
    
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )