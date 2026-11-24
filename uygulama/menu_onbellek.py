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
    veri = redis_db.get(
        menu_anahtari(yemekhane_id, tarih, ogun_id)
    )

    if veri is None:
        return None

    return json.loads(veri)


def menu_sil(yemekhane_id, tarih, ogun_id):
    redis_db.delete(
        menu_anahtari(yemekhane_id, tarih, ogun_id)
    )


def gunluk_menu_getir(tarih):
    if kalan_sure(tarih) <= 0:
        return None

    menuler = []

    for yemekhane_id in (1, 2):
        for ogun_id in (1, 2, 3):
            menu = menu_getir(yemekhane_id, tarih, ogun_id)

            if menu is None:
                return None

            menuler.append(menu)

    return menuler


def gunluk_menu_kaydet(tarih, menuler):
    for menu in menuler:
        menu_kaydet(
            menu["yemekhane_id"],
            menu["tarih"],
            menu["ogun_id"],
            menu
        )


def menu_onbellek_temizle(yemekhane_id, tarih, ogun_id):
    menu_sil(yemekhane_id, tarih, ogun_id)

    redis_db.delete("gunluk:" + str(tarih))

    secilen_tarih = datetime.fromisoformat(str(tarih)).date()
    pazartesi = secilen_tarih - timedelta(days=secilen_tarih.weekday())

    redis_db.delete("haftalik:" + pazartesi.isoformat())