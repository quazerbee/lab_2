from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import engine
from app.routers.item_router import router as item_router
from app.auth.router import router as auth_router


app = FastAPI()

app.include_router(item_router)
app.include_router(auth_router)


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