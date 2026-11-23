from datetime import date, timedelta
from flask import Blueprint, jsonify, request
from menu_veri import gunluk_menuleri_getir, haftalik_menuleri_getir, menu_doluluk_getir

menu_bp = Blueprint("menu", __name__)


@menu_bp.route("/api/menuler/gunluk", methods=["GET"])
def gunluk_menuler():
    tarih = request.args.get("tarih", date.today().isoformat())

    try:
        date.fromisoformat(tarih)
    except ValueError:
        return jsonify({"hata": "Tarih YYYY-AA-GG biçiminde olmalıdır."}), 400

    satirlar = gunluk_menuleri_getir(tarih)

    menuler = {}

    for satir in satirlar:
        menu_id = satir["menu_id"]

        if menu_id not in menuler:
            menuler[menu_id] = {
                "menu_id": menu_id,
                "tarih": str(satir["tarih"]),
                "yemekhane_id": satir["yemekhane_id"],
                "yemekhane": satir["yemekhane"],
                "ogun_id": satir["ogun_id"],
                "ogun": satir["ogun"],
                "rezervasyon_son": str(satir["rezervasyon_son"]),
                "ogrenci_fiyati": float(satir["ogrenci_fiyati"]),
                "personel_fiyati": float(satir["personel_fiyati"]),
                "toplam_kalori": 0,
                "yemekler": []
            }

        menuler[menu_id]["yemekler"].append({
            "id": satir["yemek_id"],
            "ad": satir["yemek"],
            "kategori": satir["kategori"],
            "kalori": satir["kalori"],
            "vejetaryen": bool(satir["vejetaryen"]),
            "alerjenler": satir["alerjenler"] or ""
        })

        menuler[menu_id]["toplam_kalori"] += satir["kalori"]

    return jsonify({"menuler": list(menuler.values())})


@menu_bp.route("/api/menuler/haftalik", methods=["GET"])
def haftalik_menuler():
    tarih = request.args.get("tarih", date.today().isoformat())

    try:
        secilen_tarih = date.fromisoformat(tarih)
    except ValueError:
        return jsonify({"hata": "Tarih YYYY-AA-GG biçiminde olmalıdır."}), 400

    baslangic = secilen_tarih - timedelta(days=secilen_tarih.weekday())
    bitis = baslangic + timedelta(days=6)

    satirlar = haftalik_menuleri_getir(baslangic, bitis)

    menuler = {}

    for satir in satirlar:
        menu_id = satir["menu_id"]

        if menu_id not in menuler:
            menuler[menu_id] = {
                "menu_id": menu_id,
                "tarih": str(satir["tarih"]),
                "yemekhane_id": satir["yemekhane_id"],
                "yemekhane": satir["yemekhane"],
                "ogun_id": satir["ogun_id"],
                "ogun": satir["ogun"],
                "rezervasyon_son": str(satir["rezervasyon_son"]),
                "ogrenci_fiyati": float(satir["ogrenci_fiyati"]),
                "personel_fiyati": float(satir["personel_fiyati"]),
                "toplam_kalori": 0,
                "yemekler": []
            }

        menuler[menu_id]["yemekler"].append({
            "id": satir["yemek_id"],
            "ad": satir["yemek"],
            "kategori": satir["kategori"],
            "kalori": satir["kalori"],
            "vejetaryen": bool(satir["vejetaryen"]),
            "alerjenler": satir["alerjenler"] or ""
        })

        menuler[menu_id]["toplam_kalori"] += satir["kalori"]

    return jsonify({
        "baslangic": baslangic.isoformat(),
        "bitis": bitis.isoformat(),
        "menuler": list(menuler.values())
    })


@menu_bp.route("/api/menuler/<int:menu_id>/doluluk", methods=["GET"])
def menu_doluluk(menu_id):
    bilgi = menu_doluluk_getir(menu_id)

    if bilgi is None:
        return jsonify({"hata": "Menü bulunamadı."}), 404

    return jsonify({
        "menu_id": bilgi["menu_id"],
        "kapasite": bilgi["kapasite"],
        "rezerve": bilgi["rezerve"],
        "bos_yer": bilgi["bos_yer"],
        "doluluk_yuzde": float(bilgi["doluluk_yuzde"]),
        "rezervasyon_son": str(bilgi["rezervasyon_son"])
    })
