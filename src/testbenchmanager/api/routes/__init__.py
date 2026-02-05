"""API routes submodule"""

from .config import config_router as config_router
from .experiment import experiment_router as experiment_router
from .instrument import instrument_router as instrument_router
from .run import run_router as run_router
from .tea import tea_router as tea_router
