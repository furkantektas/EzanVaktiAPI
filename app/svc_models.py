import json
import logging
from typing import Any, Callable

import requests.sessions
from zeep import Client
from zeep.cache import SqliteCache
from zeep.helpers import serialize_object
from zeep.transports import Transport

from .cache import cache
from .config import get_settings
from .models import BayramNamazi, Ilce, IlceDetay, Sehir, Ulke, Vakit

# suppress zeep logging
logging.getLogger("zeep.wsdl.bindings.soap").setLevel(logging.ERROR)

session = requests.Session()
session.headers.update(
    {
        "User-Agent": "okhttp/5.0.0-alpha.2",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
        "Host": "namazvakti.diyanet.gov.tr",
    }
)
settings = get_settings()


def service_call(
    func: Callable[..., dict[str, str]],
) -> Callable[[], list | dict | Any]:
    """Decorator to make SOAP calls and convert responses to json response.
    Make sure the wrapped function returns a dictionary with `op_name`
    corresponding to the SOAP operation to call along with all the required
    parameters."""

    def wrapper(*args, **kwargs) -> list | dict | Any:
        # get service call name and arguments
        params = func(*args, **kwargs)
        op_name = params.pop("op_name")
        # Initialize Redis client

        # Define a cache key based on the operation name and parameters
        cache_key = f"{op_name}:{':'.join(f'{k}={v}' for k, v in params.items())}"

        # Try to get the cached response
        cached_response = cache.get(cache_key)
        if cached_response:
            return json.loads(cached_response)

        # configure zeep client
        transport = Transport(
            cache=SqliteCache(timeout=settings.cache_default_timeout),  # 5 days
            session=session,
            operation_timeout=10,
            timeout=10,
        )

        auth = dict(username=settings.svc_username, password=settings.svc_password)

        client = Client(settings.svc_wsdl_url, transport=transport)

        # get the operation proxy
        svc_call = getattr(client.service, op_name)
        # call the operation proxy with the parameters and auth credentials
        svc_response = svc_call(**params, **auth)

        response = serialize_object(svc_response)
        json_response = json.dumps(response)
        # cache the response
        cache.set(cache_key, json_response, ex=settings.cache_default_timeout)

        return response

    return wrapper


@service_call
def ulkeler() -> Ulke:
    return {"op_name": "Ulkeler"}


@service_call
def sehirler(ulke_id: str) -> list[Sehir]:
    return {"op_name": "Sehirler", "UlkeID": ulke_id}


@service_call
def ilceler(sehir_id: str) -> list[Ilce]:
    return {"op_name": "Ilceler", "EyaletSehirID": sehir_id}


@service_call
def ilce_detay(ilce_id: str) -> IlceDetay:
    return {
        "op_name": "IlceBilgisiDetay",
        "ilceId": ilce_id,  # keep the key as-is. not IlceID
    }


@service_call
def vakitler(ilce_id: str) -> list[Vakit]:
    return {"op_name": "AylikNamazVakti", "IlceID": ilce_id}


@service_call
def bayram_namazi(sehir_id: str) -> list[BayramNamazi]:
    return {"op_name": "BayramNamaziVaktiIlceListesi", "EyaletSehirID": sehir_id}
