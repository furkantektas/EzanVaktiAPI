from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from requests.exceptions import RequestException
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import get_settings
from .rate_limit import rate_limiter
from .routes import router

description = """
Tüm dünya ülkeleri için Türkiye Cumhuriyeti Diyanet İşleri Başkanlığı'nın yayınladığı aylık ezan vakitleri.

### Heroku servisi güncellemesi

1 Ocak 2025 tarihi itibarı ile heroku servisi hizmet vermeyi durduracaktır. Sadece URL değişikliği yaparak ezan vakti servisini aynı şekilde kullanabilirsiniz.

- [~~https://ezanvakti.herokuapp.com~~](https://ezanvakti.herokuapp.com) → [https://ezanvakti.emushaf.net](https://ezanvakti.emushaf.net)

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

"""

settings = get_settings()


app = FastAPI(
    title="Ezan Vakti API",
    description=description,
    summary="Diyanet İşleri Başkanlığı tarafından yayınlanan ezan vakti bilgilerini sağlar.",
    version="0.4.0",
)

rate_limiter.init_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)
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
