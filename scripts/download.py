import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://namazvakitleri.diyanet.gov.tr/assets/locations"
REG_BASE_URL = "https://namazvakitleri.diyanet.gov.tr/en-US/home/GetRegList"
DEFAULT_CULTURE = "en-US"
DATA_DIR = (
    Path(os.environ.get("EZAN_DATA_DIR"))
    if os.environ.get("EZAN_DATA_DIR")
    else Path(__file__).parent.parent / "data" / "locations"
)


# Data Models
class Country(BaseModel):
    CountryID: int
    CountryName: str


class SehirItem(BaseModel):
    ExtensionData: dict
    SehirAdi: str
    SehirAdiEn: str
    SehirID: str


class IlceItem(BaseModel):
    IlceUrl: str
    ExtensionData: dict
    IlceAdi: str
    IlceAdiEn: str
    IlceID: str


class SehirResponse(BaseModel):
    Result: str | None = None
    CountryList: list | None = None
    StateList: list[SehirItem] | None = None


class IlceResponse(BaseModel):
    Result: str | None = None
    CountryList: list | None = None
    StateList: list | None = None
    StateRegionList: list[IlceItem] | None = None


class LocationDownloader:
    """Class to handle the downloading and processing of location data."""

    def __init__(self, base_dir: Path = DATA_DIR):
        """Initialize the downloader with the specified base directory."""
        self.base_dir = base_dir
        self.countries_dir = base_dir / "country"
        self.sehirler_dir = base_dir / "sehirler"
        self.ilceler_dir = base_dir / "ilceler"

    def setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.base_dir.mkdir(exist_ok=True)
        self.countries_dir.mkdir(exist_ok=True)
        self.sehirler_dir.mkdir(exist_ok=True)
        self.ilceler_dir.mkdir(exist_ok=True)

    @retry(
        stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=1, max=60)
    )
    async def download_file(
        self, url: str, output_path: Path, params=None
    ) -> dict[str, Any]:
        """
        Download a file from a URL and save it to the specified path.
        If the file already exists and contains valid JSON, skip downloading.

        Args:
            url: The URL to download from
            output_path: Where to save the downloaded file
            params: Optional query parameters for the request

        Returns:
            Parsed JSON content

        Raises:
            httpx.HTTPError: If the download fails
        """
        # Check if the file exists and contains valid JSON
        if output_path.exists():
            try:
                content = output_path.read_bytes()
                json_content = json.loads(content)
                logger.info(f"Using existing file: {output_path}")
                return json_content
            except json.JSONDecodeError:
                logger.warning(
                    f"Existing file {output_path} has invalid JSON. Re-downloading."
                )
            except Exception as e:
                logger.warning(
                    f"Error reading existing file {output_path}: {e}. Re-downloading."
                )

        # File doesn't exist or has invalid content - proceed with download
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            content = response.content

            # Save to disk
            output_path.write_bytes(content)

            # Parse and return the JSON data
            return json.loads(content)

    async def fetch_countries(self) -> list[Country]:
        """
        Download and parse the list of countries.
        If the countries file already exists, use it instead of downloading.

        Returns:
            List of Country objects
        """
        countries_file = self.base_dir / "countries.json"
        try:
            countries_data = await self.download_file(
                f"{BASE_URL}/countries.json", countries_file
            )
            countries = [Country.model_validate(country) for country in countries_data]
            logger.info(f"Found {len(countries)} countries")
            return countries
        except Exception as e:
            logger.error(f"Failed to fetch countries: {e}")
            return []

    async def process_ilceler(self, country: Country, city: SehirItem) -> None:
        """
        Download and process ilceler for a specific city.

        Args:
            country: Country object
            city: City StateItem object
        """
        city_name = city.SehirAdiEn
        city_id = city.SehirID

        logger.info(f"Processing ilceler for {city_name}...")
        district_file = self.ilceler_dir / f"{city_id}.json"

        try:
            district_params = {
                "ChangeType": "state",
                "CountryId": country.CountryID,
                "Culture": DEFAULT_CULTURE,
                "StateId": city_id,
            }

            district_data = await self.download_file(
                REG_BASE_URL, district_file, params=district_params
            )

            # Validate the district response
            district_response = IlceResponse.model_validate(district_data)

            if district_response.StateRegionList:
                len_ilce = len(district_response.StateRegionList)
                logger.info(f"Validated {len_ilce} ilce in {city_name}")
            else:
                logger.info(f"No ilce found in {city_name}")

            # Add a small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)

        except RetryError:
            logger.exception(
                f"Failed to download ilceler for {city_name} after multiple retries"
            )
        except Exception:
            logger.exception(f"Error processing ilceler for {city_name}")

    async def process_cities(self, country: Country) -> None:
        """
        Download and process cities for a specific country.

        Args:
            country: Country object
        """
        country_name = country.CountryName
        logger.info(f"Processing cities for {country_name}...")
        city_file = self.sehirler_dir / f"{country.CountryID}.json"

        try:
            params = {
                "ChangeType": "country",
                "CountryId": country.CountryID,
                "Culture": DEFAULT_CULTURE,
            }

            city_data = await self.download_file(REG_BASE_URL, city_file, params=params)

            # Validate the city response
            city_response = SehirResponse.model_validate(city_data)

            if city_response.StateList:
                len_city = len(city_response.StateList)
                logger.info(f"Validated {len_city} cities in {country_name} response")

                # Download ilceler for each city
                await asyncio.gather(
                    *(
                        self.process_ilceler(country, city_item)
                        for city_item in city_response.StateList
                    )
                )
            else:
                logger.info(f"No cities found in {country_name} response")

        except RetryError:
            logger.exception(
                f"Failed to download cities for {country_name} after multiple retries"
            )
        except Exception:
            logger.exception(f"Error processing cities for {country_name}")

    async def process_country(self, country: Country) -> None:
        """
        Download and process data for a specific country.

        This file is not needed for the current script. Downloading in case it

        Args:
            country: Country object
        """
        try:
            # Process cities for this country
            await self.process_cities(country)

        except json.JSONDecodeError:
            logger.error(f"Error: Invalid JSON format in {country.CountryName}")
        except Exception as e:
            logger.error(f"Error validating {country.CountryName}: {e}")

        except httpx.HTTPError as e:
            logger.error(f"Error downloading {country.CountryName}: {e}")

    async def download_all_locations(self) -> None:
        """Main function to orchestrate the download of all location data."""
        self.setup_directories()

        # Get list of countries
        countries = await self.fetch_countries()

        # Process each country concurrently in batches of 3 to avoid overwhelming the
        # server.
        batch_size = 3
        for i in range(0, len(countries), batch_size):
            batch = countries[i : i + batch_size]
            await asyncio.gather(*(self.process_country(country) for country in batch))


async def main():
    """Entry point for the script."""
    downloader = LocationDownloader()
    await downloader.download_all_locations()


if __name__ == "__main__":
    asyncio.run(main())
