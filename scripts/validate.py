#!/usr/bin/env python3
"""
Validate the existence and structure of prayer times data files.
This script checks if all required JSON files exist in the locations directory.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ezanvakti-validator")

DATA_DIR = (
    Path(os.environ.get("EZAN_DATA_DIR"))
    if os.environ.get("EZAN_DATA_DIR")
    else Path(__file__).parent.parent / "data" / "locations"
)


def load_json_file(file_path: Path) -> dict[str, Any] | None:
    """Load and parse a JSON file."""
    try:
        if not file_path.exists():
            return None
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None


def check_country_file(base_dir: Path) -> list | None:
    """
    Validate and load countries.json file.
    Returns the countries data if valid, None otherwise.
    """
    countries_file = base_dir / "countries.json"

    if not countries_file.exists():
        logger.error(f"Countries file not found at {countries_file}")
        return None

    countries_data = load_json_file(countries_file)
    return countries_data


def check_sehir_file(base_dir: Path, country_id: str) -> dict[str, Any] | None:
    """
    Check if a sehir file exists for the given country ID and load its content.
    Returns the sehir data if valid, None otherwise.
    """
    sehir_file = base_dir / "sehirler" / f"{country_id}.json"

    if not sehir_file.exists():
        logger.warning(f"Missing sehir file: {sehir_file}")
        return None

    return load_json_file(sehir_file)


def extract_sehir_ids(sehir_data: dict, country_id: str) -> set[str]:
    """
    Extract all sehir IDs from the sehir data.
    Returns a set of sehir IDs.
    """
    sehir_ids = set()

    state_list = sehir_data.get("StateList", [])
    if not state_list:
        logger.warning(f"No cities found for country ID {country_id}")
        return sehir_ids

    for state in state_list:
        sehir_id = state.get("SehirID")
        if not sehir_id:
            logger.warning(f"City without SehirID found in country {country_id}")
            continue

        sehir_ids.add(sehir_id)

    return sehir_ids


def check_ilce_files(base_dir: Path, sehir_ids: set[str]) -> list[str]:
    """
    Check if ilce files exist for all sehir IDs.
    Returns a list of missing ilce files.
    """
    missing_files = []

    for sehir_id in sehir_ids:
        ilce_file = base_dir / "ilceler" / f"{sehir_id}.json"
        if not ilce_file.exists():
            missing_files.append(str(ilce_file))

    return missing_files


def validate_files() -> bool:
    """
    Validate all necessary JSON files exist.
    Returns True if all validations pass, False otherwise.
    """

    # Validate countries.json exists and load countries data
    countries_data = check_country_file(DATA_DIR)
    if countries_data is None:
        return False

    missing_files = []
    sehir_ids = set()

    # Check each country's sehir file
    for country in countries_data:
        country_id = country.get("CountryID")
        if not country_id:
            logger.warning(f"Country without CountryID found: {country}")
            continue

        # Load sehir data
        sehir_data = check_sehir_file(DATA_DIR, country_id)
        if sehir_data is None:
            missing_files.append(str(DATA_DIR / "sehirler" / f"{country_id}.json"))
            continue

        # Extract sehir IDs
        sehir_ids.update(extract_sehir_ids(sehir_data, country_id))

    # Check ilce files
    ilce_missing_files = check_ilce_files(DATA_DIR, sehir_ids)
    missing_files.extend(ilce_missing_files)

    # Report results
    if missing_files:
        logger.error(f"Validation failed: {len(missing_files)} files are missing:")
        for file_path in missing_files:
            logger.error(f"  - {file_path}")
        return False

    logger.info("Validation successful: All required files exist.")
    return True


if __name__ == "__main__":
    success = validate_files()
    # Use appropriate exit codes: 0 for success, 1 for failure
    sys.exit(0 if success else 1)
