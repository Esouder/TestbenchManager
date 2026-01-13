"""API root"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import (
    config_router,
    experiment_router,
    instrument_router,
    run_router,
    tea_router,
)

api = FastAPI()

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://dashboard.testbenchmanager.com",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

api.include_router(instrument_router)
api.include_router(tea_router)
api.include_router(experiment_router)
api.include_router(run_router)
api.include_router(config_router)
