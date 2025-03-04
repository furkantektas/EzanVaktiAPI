import logging

import httpx
from fastapi import HTTPException

from app.models.schemas import ExternalApiResponse

logger = logging.getLogger(__name__)


class ApiClient:
    """Client for accessing the Diyanet Namaz Vakti API."""

    def __init__(
        self, api_url: str, api_username: str, api_password: str, timeout: int = 30
    ):
        """
        Initialize the API client.

        Args:
            api_url: Base URL for the API
            api_username: API username
            api_password: API password
            timeout: Request timeout in seconds
        """
        self.api_username = api_username
        self.api_password = api_password
        self.api_url = api_url
        self.timeout = timeout

    async def get_monthly_prayer_times(self, ilce_id: str) -> ExternalApiResponse:
        """
        Fetch monthly prayer times for a specific location.

        Args:
            ilce_id: The district ID to get prayer times for

        Returns:
            ExternalApiResponse object containing the prayer times

        Raises:
            HTTPException: If the API request fails
        """
        url = f"{self.api_url}/NamazVakti/Aylik"
        params = {"ilceId": ilce_id}

        headers = {
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive",
            "Host": "namazvakti.diyanet.gov.tr",
            "User-Agent": "okhttp/5.0.0-alpha.3",
        }

        auth = httpx.BasicAuth(username=self.api_username, password=self.api_password)

        try:
            logger.debug(f"Requesting prayer times for ilceID: {ilce_id}")
            async with httpx.AsyncClient(auth=auth, timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                # Parse the response into our model
                try:
                    data = response.json()
                    logger.debug("Successfully received API response")
                    return ExternalApiResponse.model_validate(data)
                except ValueError as e:
                    logger.error(f"Failed to parse API response: {e}")
                    raise HTTPException(
                        status_code=500, detail="Failed to parse Diyanet API response"
                    ) from e
                except Exception as e:
                    logger.error(f"Unexpected error processing API response: {e}")
                    raise HTTPException(
                        status_code=500, detail="Error processing API response"
                    ) from e

        except httpx.HTTPStatusError as e:
            r = e.response
            logger.exception(f"HTTP error from Diyanet API: {r.status_code} - {r.text}")
            raise HTTPException(
                status_code=r.status_code, detail=f"Diyanet API error: {r.text}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error to Diyanet API: {str(e)}")
            raise HTTPException(
                status_code=503, detail="Unable to connect to Diyanet API"
            ) from e
