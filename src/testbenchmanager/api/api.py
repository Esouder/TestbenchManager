"""API root"""

from fastapi import FastAPI

from .routes import instrument_router

api = FastAPI()

api.include_router(instrument_router)
