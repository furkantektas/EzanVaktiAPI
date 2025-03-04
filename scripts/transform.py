#!/usr/bin/env python3
"""
Transformation script to convert files from web format to previous API format.
This is done to maintain backward compatibility with existing systems.
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define source and destination paths
DATA_DIR = (
    Path(os.environ.get("EZAN_DATA_DIR"))
    if os.environ.get("EZAN_DATA_DIR")
    else Path(__file__).parent.parent / "data" / "locations"
)
DEST_DIR = Path(__file__).parent.parent / "app" / "static" / "data"


def load_json_file(file_path: Path) -> dict:
    """Load and parse a JSON file."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}


def save_json_file(data: Any, file_path: Path) -> None:
    """Save data to a JSON file."""
    try:
        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully saved {file_path}")
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")


def transform_countries(country_mappings: dict[str, str]) -> list[dict[str, str]]:
    """
    Transform countries data from old format to new format.

    Args:
        country_mappings: Dictionary mapping UlkeAdiEn to UlkeAdi

    Returns:
        List of transformed country dictionaries
    """
    countries_file = DATA_DIR / "countries.json"
    countries_data = load_json_file(countries_file)

    transformed_countries = []
    for country in countries_data:
        country_name_en = country["CountryName"]
        country_name = country_mappings.get(
            country_name_en, country_name_en
        )  # Default to English name if no mapping

        transformed_country = {
            "UlkeAdi": country_name,
            "UlkeAdiEn": country_name_en,
            "UlkeID": str(country["CountryID"]),
        }
        transformed_countries.append(transformed_country)

    return transformed_countries


def transform_sehir(country_id: str) -> list[dict[str, str]]:
    """
    Transform sehir data for a specific country from old format to new format.

    Args:
        country_id: ID of the country

    Returns:
        List of transformed sehir dictionaries
    """
    sehir_file = DATA_DIR / "sehirler" / f"{country_id}.json"
    if not sehir_file.exists():
        logger.warning(f"No cities file found for country ID {country_id}")
        return []

    cities_data = load_json_file(sehir_file)

    if not cities_data or "StateList" not in cities_data:
        logger.warning(f"Invalid or empty cities data for country ID {country_id}")
        return []

    transformed_cities = []
    for sehir in cities_data["StateList"]:
        transformed_sehir = {
            "SehirAdi": sehir["SehirAdi"],
            "SehirAdiEn": sehir["SehirAdiEn"],
            "SehirID": sehir["SehirID"],
        }
        transformed_cities.append(transformed_sehir)

    return transformed_cities


def transform_ilce(sehir_id: str) -> list[dict[str, str]]:
    """
    Transform ilce data for a specific sehir from old format to new format.

    Args:
        sehir_id: ID of the sehir

    Returns:
        List of transformed ilce dictionaries
    """
    ilceler_file = DATA_DIR / "ilceler" / f"{sehir_id}.json"
    if not ilceler_file.exists():
        logger.warning(f"No ilces file found for sehir ID {sehir_id}")
        return []

    ilce_data = load_json_file(ilceler_file)

    if not ilce_data or "StateRegionList" not in ilce_data:
        logger.warning(f"Invalid or empty ilces data for sehir ID {sehir_id}")
        return []

    transformed_ilces = []
    for ilce in ilce_data["StateRegionList"]:
        transformed_ilce = {
            "IlceAdi": ilce["IlceAdi"],
            "IlceAdiEn": ilce["IlceAdiEn"],
            "IlceID": ilce["IlceID"],
        }
        transformed_ilces.append(transformed_ilce)

    return transformed_ilces


def process_all_data() -> None:
    """Process all data files and transform them to the new format."""
    logger.info("Starting transformation process")

    # Create or clear the destination directory
    if DEST_DIR.exists():
        shutil.rmtree(DEST_DIR)
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Load country name mappings
    country_mappings_file = Path("country_name_mapping.json")
    country_mappings = load_json_file(country_mappings_file)

    # Transform countries
    countries = transform_countries(country_mappings)
    save_json_file(countries, DEST_DIR / "countries.json")

    # Create sehirler directory
    (DEST_DIR / "sehirler").mkdir(parents=True, exist_ok=True)

    # Create ilceler directory
    (DEST_DIR / "ilceler").mkdir(parents=True, exist_ok=True)

    # Process cities and ilces for each country
    for country in countries:
        country_id = country["UlkeID"]

        # Transform cities for this country
        cities = transform_sehir(country_id)
        if cities:
            save_json_file(cities, DEST_DIR / "sehirler" / f"{country_id}.json")

            # Transform ilces for each sehir
            for sehir in cities:
                sehir_id = sehir["SehirID"]
                ilces = transform_ilce(sehir_id)
                if ilces:
                    save_json_file(ilces, DEST_DIR / "ilceler" / f"{sehir_id}.json")

    logger.info("Transformation process completed successfully")


if __name__ == "__main__":
    try:
        process_all_data()
    except Exception as e:
        logger.error(f"An error occurred during transformation: {e}")
        sys.exit(1)
