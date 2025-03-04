from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from requests.exceptions import RequestException
from starlette.responses import JSONResponse

from .config import get_settings
from .middleware.cache import CacheMiddleware
from .rate_limit import rate_limiter
from .routes import router
from .services.cache import CacheService

description = """
Tüm dünya ülkeleri için Türkiye Cumhuriyeti Diyanet İşleri Başkanlığı'nın yayınladığı aylık ezan vakitleri.

### İstek Limiti

30 istek / 5 dakika ve 200 istek / 1 gün

*(Namaz vakitleri 30 günlük verildiği için ayda 1 istek yeterlidir.)*

### Diyanet kaynaklı bilinen sorunlar

> Bu sorunların çözülmesi beklenmemektedir.

- Ülkelerin İngilizce isimlendirmeleri hatalı. Örneğin: İngilizcede `Central African Republic` olması gereken isim `ORTA AFRIKA CUMHURIYETI`.
- Űlkelerin isimlerinde Türkçe karakterler yerine İngilizce karakterler kullanılmış. Örneğin: `ÇİN` yerine `CIN`.
- Hatalı ülke isimlendirmeleri: Birleşik Krallık șehirleri `INGILTERE` altında toplanmış.
- Vakitler sonucundaki `MiladiTarihUzunIso8601` değeri her zaman Türkiye'nin geçerli zaman dilimini gösteriyor. Bu durum Türkiye harici zaman dilimlerinde ezan vakti hesaplamalarında hatalara sebep olmakta. Bundan dolayı, yurtdışı kullanımlarını göz önünde bulundurarak, alınan vakitlerinin zaman diliminin ihmal edilmesi gerekiyor. Sağlanan vakitler, cihazın zaman dilimine göre doğru vakitleri göstermektedir.
- Bazı ülkelerin vakitleri sadece şehir bazında verilmiş ve bu ülkelerin şehirleri "ilçe" olarak listelenmiştir. Örneğin, [Birleşik Krallık için şehirler](/sehirler/15) listelendiğinde tek bir şehir listelenmekte, [bu şehrin ilçeleri](/ilceler/725) istendiğinde ise Birleşik Krallık'taki şehirler listelenmektedir.

Muhabbetle yapılmıştır.

İrtibat: [Furkan Tektas](https://furkantektas.com)

"""  # noqa: E501

settings = get_settings()


app = FastAPI(
    title="Ezan Vakti API",
    description=description,
    summary="Diyanet İşleri Başkanlığı tarafından yayınlanan ezan vakitlerini sağlar.",
    version="0.5.0",
)

# Initialize cache service
cache_service = CacheService(
    cache_type=settings.cache_type,
    default_timeout=settings.cache_default_timeout,
    redis_url=settings.redis_url,
)

# Add middleware in order (order matters for middleware)
# Cache middleware should be before GZip to cache uncompressed responses
rate_limiter.init_app(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CacheMiddleware,
    cache_service=cache_service,
    excluded_paths=["/up"],  # Don't cache health check endpoint
)
app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)

    # Add Cache-Control header for GET requests to relevant endpoints
    if request.method == "GET" and not request.url.path.startswith("/up"):
        # Set appropriate Cache-Control headers based on endpoint
        if any(
            request.url.path.startswith(path)
            for path in ["/ulkeler", "/sehirler", "/ilceler"]
        ):
            # Static data could be cached longer
            response.headers["Cache-Control"] = "public, max-age=86400"  # 24 hours
        elif request.url.path.startswith("/vakitler"):
            # Prayer times data
            response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour

    return response


app.include_router(router)


@app.exception_handler(RequestException)
async def diyanet_exception_handler(request: Request, exc: RequestException):
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
