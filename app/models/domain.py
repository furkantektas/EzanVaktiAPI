from pydantic import BaseModel


class Ulke(BaseModel):
    """Country model."""

    UlkeAdi: str
    UlkeAdiEn: str
    UlkeID: str


class Sehir(BaseModel):
    """City model."""

    SehirAdi: str
    SehirAdiEn: str
    SehirID: str


class Ilce(BaseModel):
    """District model."""

    IlceAdi: str
    IlceAdiEn: str
    IlceID: str


class Vakit(BaseModel):
    """Prayer times model."""

    HicriTarihKisa: str
    HicriTarihKisaIso8601: str | None = None
    HicriTarihUzun: str
    HicriTarihUzunIso8601: str | None = None
    AyinSekliURL: str
    MiladiTarihKisa: str
    MiladiTarihKisaIso8601: str
    MiladiTarihUzun: str
    MiladiTarihUzunIso8601: str
    GreenwichOrtalamaZamani: float
    Aksam: str
    Gunes: str
    GunesBatis: str
    GunesDogus: str
    Ikindi: str
    Imsak: str
    KibleSaati: str
    Ogle: str
    Yatsi: str
