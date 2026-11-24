import json
from datetime import datetime, timedelta
from oturum import redis_db


def menu_anahtari(yemekhane_id, tarih, ogun_id):
    return f"menu:{yemekhane_id}:{tarih}:{ogun_id}"


def kalan_sure(tarih):
    gun_sonu = datetime.fromisoformat(str(tarih)) + timedelta(days=1)
    return int((gun_sonu - datetime.now()).total_seconds())


def menu_kaydet(yemekhane_id, tarih, ogun_id, menu):
    sure = kalan_sure(tarih)

    if sure > 0:
        redis_db.setex(
            menu_anahtari(yemekhane_id, tarih, ogun_id),
            sure,
            json.dumps(menu, ensure_ascii=False)
        )


def menu_getir(yemekhane_id, tarih, ogun_id):
    veri = redis_db.get(menu_anahtari(yemekhane_id, tarih, ogun_id))

    if veri is None:
        return None

    return json.loads(veri)


def menu_sil(yemekhane_id, tarih, ogun_id):
    redis_db.delete(menu_anahtari(yemekhane_id, tarih, ogun_id))


def gunluk_menu_getir(tarih):
    veri = redis_db.get("gunluk:" + str(tarih))

    if veri is None:
        return None

    return json.loads(veri)


def gunluk_menu_kaydet(tarih, menuler):
    sure = kalan_sure(tarih)

    if sure > 0:
        redis_db.setex(
            "gunluk:" + str(tarih),
            sure,
            json.dumps(menuler, ensure_ascii=False)
        )


def gunluk_menu_sil(tarih):
    redis_db.delete("gunluk:" + str(tarih))


def haftalik_menu_getir(baslangic):
    veri = redis_db.get("haftalik:" + str(baslangic))

    if veri is None:
        return None

    return json.loads(veri)


def haftalik_menu_kaydet(baslangic, bitis, menuler):
    sure = kalan_sure(bitis)

    if sure > 0:
        redis_db.setex(
            "haftalik:" + str(baslangic),
            sure,
            json.dumps(menuler, ensure_ascii=False)
        )


def haftalik_menu_sil(tarih):
    secilen_tarih = datetime.fromisoformat(str(tarih)).date()
    pazartesi = secilen_tarih - timedelta(days=secilen_tarih.weekday())

    redis_db.delete("haftalik:" + pazartesi.isoformat())


def menu_onbellek_temizle(yemekhane_id, tarih, ogun_id):
    menu_sil(yemekhane_id, tarih, ogun_id)
    gunluk_menu_sil(tarih)
    haftalik_menu_sil(tarih)