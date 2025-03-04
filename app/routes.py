import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import FileResponse

from . import svc_models
from .models import Ilce, Sehir, Ulke, Vakit
from .rate_limit import no_limit, ratelimit
from .utils import STATIC_DATA_PATH, get_int_param, load_json_data

router = APIRouter(
    tags=["Ezan Vakti"],
    responses={
        502: {"description": "Diyanet Isleri Baskanligi servisine baglanilamiyor."}
    },
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

    return JSONResponse(svc_models.vakitler(ilce_id=ilce))
