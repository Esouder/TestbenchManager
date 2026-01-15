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

@tea_router.get("/test")
def test_endpoint() -> None:
    report = report_manager.generate_report(ReportMetadata(
        uid="test-report-001",
        name="Test Report",
        start_time=datetime.now()
    ))
    report.new_data_point("instrument-001", DataPoint(value=42, timestamp=datetime.now()))
    report.close()
    

