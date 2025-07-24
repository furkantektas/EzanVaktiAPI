import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import FileResponse, JSONResponse

from app.core.config import get_settings
from app.infrastructure.diyanet_api.client import ApiClient
from app.middleware.rate_limit import no_limit
from app.models.domain import Ilce, Lookup, Sehir, Ulke, Vakit
from app.models.schemas import convert_vakit_response
from app.utils import STATIC_DATA_PATH, get_int_param, load_json_data

router = APIRouter(
    tags=["Ezan Vakti"],
    responses={
        502: {"description": "Diyanet Isleri Baskanligi servisine baglanilamiyor."}
    },
)

# Initialize API client with settings
settings = get_settings()
api_client = ApiClient(
    api_url=settings.api_url,
    api_username=settings.api_username,
    api_password=settings.api_password,
    timeout=settings.api_timeout,
)


@router.get("/", include_in_schema=False)
@no_limit
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@router.get("/up", include_in_schema=False)
@router.head("/up", include_in_schema=False)
@no_limit
async def up():
    return JSONResponse({"status": "up"})


@router.get("/lookup", include_in_schema=False)
# @ratelimit
@no_limit
async def lookup(request: Request) -> list[Lookup]:
    try:
        file_path = STATIC_DATA_PATH / "lookup.json"
        with open(file_path, encoding="utf-8") as f:
            countries_data = json.load(f)
        return JSONResponse(countries_data)
    except FileNotFoundError:
        return JSONResponse([])


@router.get("/ulkeler")
# @ratelimit
@no_limit
async def ulkeler(request: Request) -> list[Ulke]:
    try:
        file_path = STATIC_DATA_PATH / "countries.json"
        with open(file_path, encoding="utf-8") as f:
            countries_data = json.load(f)
        return JSONResponse(countries_data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Ulke not found") from None


# backward compatibility sehirler?ulke=1 -> sehirler/1
@router.get("/sehirler", include_in_schema=False)
@router.get(
    "/sehirler/{ulke}", openapi_extra={"examples": {"1": {"summary": "Türkiye"}}}
)
# @ratelimit
@no_limit
async def sehirler(request: Request, ulke: int | None = None) -> list[Sehir]:
    if ulke is None:
        ulke = get_int_param(request, "ulke")

    data = load_json_data("sehirler", ulke, "Sehir not found")
    return JSONResponse(data)


@router.get("/ilceler", include_in_schema=False)
@router.get("/ilceler/{sehir}")
# @ratelimit
@no_limit
async def ilceler(request: Request, sehir: int | None = None) -> list[Ilce]:
    if sehir is None:
        sehir = get_int_param(request, "sehir")

    data = load_json_data("ilceler", sehir, "Ilce not found")
    return JSONResponse(data)


@router.get("/vakitler", include_in_schema=False)
@router.get("/vakitler/{ilce}")
# @ratelimit
@no_limit
async def vakitler(request: Request, ilce: int | None = None) -> list[Vakit]:
    if ilce is None:
        ilce = get_int_param(request, "ilce")

    # Fetch prayer times from the API
    api_response = await api_client.get_monthly_prayer_times(str(ilce))

    # Transform the API response to the expected format
    transformed_response = convert_vakit_response(api_response)

    return JSONResponse([vakit.model_dump() for vakit in transformed_response])
