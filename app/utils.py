import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from starlette.requests import Request

# Base path for static data files
STATIC_DATA_PATH = Path(__file__).parent / "static" / "data"


def get_int_param(request: Request, param_name: str) -> int:
    """Extract and validate an integer parameter from query params."""
    param_value = request.query_params.get(param_name)
    if param_value is None:
        raise HTTPException(
            status_code=400, detail=f"{param_name} parameter is required"
        )
    try:
        return int(param_value)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"{param_name} must be an integer"
        ) from None


def load_json_data(subdir: str, file_id: int, error_detail: str) -> Any:
    """Load JSON data from a static file."""
    try:
        file_path = STATIC_DATA_PATH / subdir / f"{file_id}.json"
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=error_detail) from None
    except (json.JSONDecodeError, IOError) as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading data: {error_detail}"
        ) from e
