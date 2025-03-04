from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from requests.exceptions import RequestException


async def diyanet_exception_handler(request: Request, exc: RequestException):
    """
    Handle exceptions from the Diyanet API.

    Args:
        request: The incoming request
        exc: The exception that occurred

    Returns:
        JSONResponse: A formatted error response
    """
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=jsonable_encoder(
            {
                "error": {
                    "status": 502,
                    "message": "Diyanet Isleri Baskanligi servisine baglanilamiyor.",
                }
            }
        ),
    )
