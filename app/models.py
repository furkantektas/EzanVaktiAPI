import re

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


# Models for the new API response
class Konum(BaseModel):
    konum_Id: int
    timezone: str


class NamazVakti(BaseModel):
    imsak: str
    gunes: str
    ogle: str
    ikindi: str
    aksam: str
    yatsi: str
    gunes_dogus: str
    gunes_batis: str
    kible_saati: str
    hicri_tarih_uzun: str
    hicri_tarih_kisa: str
    miladi_tarih_uzun: str
    miladi_tarih_uzun_Iso8601: str
    miladi_tarih_kisa_Iso8601: str
    ayin_sekli_url: str
    imsak_bg: str | None = None
    gunes_bg: str | None = None
    ogle_bg: str | None = None
    ikindi_bg: str | None = None
    aksam_bg: str | None = None
    yatsi_bg: str | None = None


class ResultMessage(BaseModel):
    messageType: int
    messageContent: str
    messageCode: int


class ResultObject(BaseModel):
    konum: Konum
    namazVakti: list[NamazVakti]


class ExternalApiResponse(BaseModel):
    success: bool
    resultMessage: ResultMessage
    resultObject: ResultObject


def _extract_time(iso_str: str) -> str:
    """
    Extract time component from an ISO format string.

    Args:
        iso_str: A string in ISO 8601 format (e.g., "2023-09-15T08:30:00")

    Returns:
        The time portion in "HH:MM" format

    Raises:
        ValueError: If the input string doesn't contain a valid time pattern
    """
    if not iso_str:
        raise ValueError("Empty input string provided")

    time_match = re.search(r"T(\d{2}:\d{2})", iso_str)
    if not time_match:
        raise ValueError(f"Could not extract time from ISO string: {iso_str}")

    # Extract the time and ensure it's in HH:MM format
    return time_match.group(1)


def convert_vakit_response(external_data: ExternalApiResponse) -> list[Vakit]:
    """Convert new API response format to previously used Vakit model."""
    vakitler = []

    for namaz_vakti in external_data.resultObject.namazVakti:
        vakitler.append(
            Vakit(
                HicriTarihKisa=namaz_vakti.hicri_tarih_kisa,
                HicriTarihKisaIso8601=None,  # Keep it for backward compatibility
                HicriTarihUzun=namaz_vakti.hicri_tarih_uzun,
                HicriTarihUzunIso8601=None,  # Keep it for backward compatibility
                AyinSekliURL=namaz_vakti.ayin_sekli_url,
                MiladiTarihKisa=namaz_vakti.miladi_tarih_kisa_Iso8601,
                MiladiTarihKisaIso8601=namaz_vakti.miladi_tarih_kisa_Iso8601,
                MiladiTarihUzun=namaz_vakti.miladi_tarih_uzun,
                MiladiTarihUzunIso8601=namaz_vakti.miladi_tarih_uzun_Iso8601,
                GreenwichOrtalamaZamani=3.0,  # Keep it for backward compatibility
                Aksam=_extract_time(namaz_vakti.aksam),
                Gunes=_extract_time(namaz_vakti.gunes),
                GunesBatis=_extract_time(namaz_vakti.gunes_batis),
                GunesDogus=_extract_time(namaz_vakti.gunes_dogus),
                Ikindi=_extract_time(namaz_vakti.ikindi),
                Imsak=_extract_time(namaz_vakti.imsak),
                KibleSaati=_extract_time(namaz_vakti.kible_saati),
                Ogle=_extract_time(namaz_vakti.ogle),
                Yatsi=_extract_time(namaz_vakti.yatsi),
            )
        )

    return vakitler
