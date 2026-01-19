# [EzanVakti API](https://ezanvakti.emushaf.net)

Tüm dünya ülkeleri için Türkiye Cumhuriyeti Diyanet İşleri Başkanlığı'nın yayınladığı aylık ezan vakitleri.

> ↗️ [ezanvakti.emushaf.net](https://ezanvakti.emushaf.net)

## Heroku Servisi Güncellemesi

1 Ocak 2025 tarihi itibarı ile heroku servisi hizmet vermeyi durduracaktır. Sadece URL değişikliği yaparak ezan vakti servisini aynı şekilde kullanabilirsiniz.

- ~~https://ezanvakti.herokuapp.com~~ → https://ezanvakti.emushaf.net

## Kullanım

- Ülkeler Listesi: `GET` `/ulkeler`
- Şehirler Listesi: `GET` `/sehirler/[ULKE_KODU]`
- İlçeler Listesi: `GET` `/ilceler/[SEHIR_KODU]`
- Vakitler: `GET` `/vakitler/[ILCE_KODU]`
- Şehrin tüm ilçeleri için Bayram Namazı Saatleri: `GET` `/bayram-namazi/[SEHIR_KODU]`

## Bilinen Sorunlar

> Bu sorunların çözülmesi beklenmemektedir.

- Ülkelerin İngilizce isimlendirmeleri hatalı. Örneğin: İngilizcede `Central African Republic` olması gereken isim `ORTA AFRIKA CUMHURIYETI`.
- Ülkelerin isimlerinde Türkçe karakterler yerine İngilizce karakterler kullanılmış. Örneğin: `ÇİN` yerine `CIN`.
- Hatalı ülke isimlendirmeleri: Birleşik Krallık şehirleri `INGILTERE` altında toplanmış.
- Vakitler sonucundaki `MiladiTarihUzunIso8601` değeri her zaman Türkiye'nin geçerli zaman dilimini gösteriyor. Bu durum Türkiye harici zaman dilimlerinde ezan vakti hesaplamalarında hatalara sebep olmakta. Bundan dolayı, yurtdışı kullanımlarını göz önünde bulundurarak, alınan vakitlerinin zaman diliminin ihmal edilmesi gerekiyor. Sağlanan vakitler, cihazın zaman dilimine göre doğru vakitleri göstermektedir.
- Bazı ülkelerin vakitleri sadece şehir bazında verilmiş ve bu ülkelerin şehirleri "ilçe" olarak listelenmiştir. Örneğin, [Birleşik Krallık için şehirler](/sehirler/15) listelendiğinde tek bir şehir listelenmekte, [bu şehrin ilçeleri](/ilceler/725) istendiğinde ise Birleşik Krallık'taki şehirler listelenmektedir.

## Örnek Kullanım ve Dökümantasyon

- [OpenAPI ve Swagger](https://ezanvakti.emushaf.net/docs)
- [ReDoc](https://ezanvakti.emushaf.net/redoc)

## Geliştirme ortamı kurulumu

```bash
git clone https://github.com/furkantektas/EzanVaktiAPI.git
cd EzanVaktiAPI

# Install uv and dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv sync --all-extras --dev

# Populate the static data
sh scripts/setup.sh
```

> Vakitlerin çekilmesi için gerekli olan bilgiler projede (maalesef) mevcut değildir.

Muhabbetle yapılmıştır.

2014 - ...
