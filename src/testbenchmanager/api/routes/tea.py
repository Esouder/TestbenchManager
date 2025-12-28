"""Instrument API routes"""

from fastapi import APIRouter, Response, status

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

