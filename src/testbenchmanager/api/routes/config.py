from fastapi import APIRouter, HTTPException, status

from testbenchmanager.instruments.instrument_manager import instrument_manager
from testbenchmanager.report_generator.report_manager import report_manager

config_router = APIRouter(prefix="/config")


@config_router.post("/reload/")
def reload_configuration() -> None:
    reload_instrument_configuration()
    reload_report_configuration()
    return None


@config_router.post("/reload/instruments/")
def reload_instrument_configuration() -> None:
    """
    Reload the instrument configuration.

    Raises:
        HTTPException: If reloading the configuration fails.
    """
    try:
        instrument_manager.load_all_configurations()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload instrument configuration: {e}",
        ) from e

    return None


@config_router.post("/reload/reports/")
def reload_report_configuration() -> None:
    """
    Reload the report configuration.

    Raises:
        HTTPException: If reloading the configuration fails.
    """
    try:
        report_manager.load_all_configurations()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload report configuration: {e}",
        ) from e

    return None
