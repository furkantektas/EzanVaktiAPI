from pydantic import BaseModel


class Ulke(BaseModel):
    UlkeAdi: str
    UlkeAdiEn: str
    UlkeID: str


class Sehir(BaseModel):
    SehirAdi: str
    SehirAdiEn: str
    SehirID: str


class Ilce(BaseModel):
    IlceAdi: str
    IlceAdiEn: str
    IlceID: str


class IlceDetay(BaseModel):
    CografiKibleAcisi: str | None = None
    IlceAdi: str
    IlceAdiEn: str
    IlceID: str
    KabeyeUzaklik: str | None = None
    KibleAcisi: str | None = None
    SehirAdi: str
    SehirAdiEn: str
    UlkeAdi: str
    UlkeAdiEn: str


class Vakit(BaseModel):
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


class BayramNamazi(BaseModel):
    KurbanBayramNamaziHTarihi: str | None = None
    KurbanBayramNamaziSaati: str | None = None
    KurbanBayramNamaziTarihi: str | None = None
    RamazanBayramNamaziHTarihi: str | None = None
    RamazanBayramNamaziSaati: str | None = None
    RamazanBayramNamaziTarihi: str | None = None
