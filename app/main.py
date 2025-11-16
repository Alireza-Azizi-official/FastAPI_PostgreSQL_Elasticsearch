import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from .db import Base, engine
from .logger_config import configure_logging
from .routers import router as api_router

load_dotenv()
configure_logging()
logger = logging.getLogger("app.main")

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


@app.post("/create-tables")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return {"status": "ok"}
