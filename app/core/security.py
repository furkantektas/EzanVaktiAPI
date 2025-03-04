from fastapi import Request

from app.core.config import get_settings

trusted_clients = get_settings().trusted_clients


async def is_trusted_client(request: Request) -> bool:
    """
    Check if the client token is trusted by comparing the x-parola header
    value with the trusted clients list.

    Args:
        request: The incoming request

    Returns:
        bool: True if the client is trusted, False otherwise
    """
    x_parola = request.headers.get("x-parola", "")
    return x_parola.lower() in trusted_clients
