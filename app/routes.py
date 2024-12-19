from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import FileResponse

from . import svc_models
from .models import BayramNamazi, Ilce, IlceDetay, Sehir, Ulke, Vakit
from .rate_limit import no_limit, ratelimit

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
    return JSONResponse(svc_models.ulkeler())


# backward compatibility sehirler?ulke=1 -> sehirler/1
@router.get("/sehirler", include_in_schema=False)
@router.get(
    "/sehirler/{ulke}", openapi_extra={"examples": {"1": {"summary": "Türkiye"}}}
)
# @ratelimit
@no_limit
async def sehirler(request: Request, ulke: int = None) -> list[Sehir]:
    return JSONResponse(svc_models.sehirler(ulke_id=ulke))


@router.get("/ilceler", include_in_schema=False)
@router.get("/ilceler/{sehir}")
# @ratelimit
@no_limit
async def ilceler(request: Request, sehir: int = None) -> list[Ilce]:
    return JSONResponse(svc_models.ilceler(sehir_id=sehir))


# no need for backward compability. introduced in 0.4.0
@router.get("/ilce-detay/{ilce}")
# @ratelimit
@no_limit
async def ilce_detay(request: Request, ilce: int = None) -> IlceDetay:
    return JSONResponse(svc_models.ilce_detay(ilce_id=ilce))


@router.get("/vakitler", include_in_schema=False)
@router.get("/vakitler/{ilce}")
# @ratelimit
@no_limit
async def vakitler(request: Request, ilce: int = None) -> list[Vakit]:
    return JSONResponse(svc_models.vakitler(ilce_id=ilce))


@router.get("/bayram-namazi", include_in_schema=False)
@router.get("/bayram-namazi/{sehir}")
# @ratelimit
@no_limit
async def bayram_namazi(request: Request, sehir: int = None) -> list[BayramNamazi]:
    return JSONResponse(svc_models.bayram_namazi(sehir_id=sehir))
