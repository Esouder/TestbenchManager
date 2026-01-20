"""Instrument API routes"""

from datetime import datetime

from fastapi import APIRouter, Response, status

from testbenchmanager.report_generator.report import DataPoint
from testbenchmanager.report_generator.report_manager import report_manager
from testbenchmanager.report_generator.report_metadata import ReportMetadata

tea_router = APIRouter(prefix="/tea")

TEAPOT = """
             ;,'
     _o_    ;:;'
 ,-.'---`.__ ;
((j`=====',-'
 `-\\     /
    `-=-'"""


@tea_router.get("/", status_code=status.HTTP_418_IM_A_TEAPOT)
def teapot() -> Response:
    """
    List all registered instrument UIDs.

    Returns:
        list[str]: List of instrument UIDs.
    """
    return Response(content=TEAPOT,
                    status_code=status.HTTP_418_IM_A_TEAPOT,
                    media_type="text/plain")