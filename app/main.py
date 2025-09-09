
"""
Main entry point for the Sensor Data API application.
Initializes FastAPI, sets up database tables, and includes API endpoints.
"""
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from app.api import endpoints
from app.database import init_postgres

@asynccontextmanager
async def lifespan(fapp: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    This asynchronous generator function is used to manage application startup and shutdown events.

    Args:
        app (FastAPI): The FastAPI application instance.

    """
    print("Initializing ", fapp.title)
    await init_postgres()
    yield
    print("Shutting down app ...")

load_dotenv(override=True)
app = FastAPI(lifespan=lifespan, title="Sensory API", version="0.0.9")
app.include_router(endpoints.router, prefix="/api/v1")
