from datetime import date
from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error
from oturum import oturum_bul
from yonetici_veri import yonetici_menuleri_getir, yonetici_menu_ekle, yonetici_menu_duzenle

yonetici_bp = Blueprint("yonetici", __name__)


@yonetici_bp.route("/api/yonetici/menuler", methods=["GET"])
def yonetici_menuleri():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    if kullanici["rol"] != "yonetici":
        return jsonify({"hata": "Bu işlem için yönetici yetkisi gerekiyor."}), 403

    satirlar = yonetici_menuleri_getir()

    menuler = []

    for satir in satirlar:
        menuler.append({
            "menu_id": satir["menu_id"],
            "tarih": str(satir["tarih"]),
            "yemekhane": satir["yemekhane"],
            "ogun": satir["ogun"],
            "ogrenci_fiyati": float(satir["ogrenci_fiyati"]),
            "personel_fiyati": float(satir["personel_fiyati"]),
            "kapasite": satir["kapasite"],
            "rezerve": satir["rezerve"],
            "bos_yer": satir["bos_yer"],
            "doluluk_yuzde": float(satir["doluluk_yuzde"]),
            "oy_sayisi": satir["oy_sayisi"],
            "ortalama_puan": float(satir["ortalama_puan"]) if satir["ortalama_puan"] is not None else None
        })

    return jsonify({"menuler": menuler})


@yonetici_bp.route("/api/yonetici/menu/ekle", methods=["POST"])
def yonetici_menu_olustur():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    if kullanici["rol"] != "yonetici":
        return jsonify({"hata": "Bu işlem için yönetici yetkisi gerekiyor."}), 403

    veri = request.get_json(silent=True) or {}

    yemekhane_id = veri.get("yemekhane_id")
    tarih = veri.get("tarih")
    ogun_id = veri.get("ogun_id")
    ogrenci_fiyati = veri.get("ogrenci_fiyati")
    personel_fiyati = veri.get("personel_fiyati")
    yemek_idleri = veri.get("yemek_idleri")

    if type(yemekhane_id) is not int or yemekhane_id <= 0:
        return jsonify({"hata": "Geçerli bir yemekhane numarası giriniz."}), 400

    if type(ogun_id) is not int or ogun_id <= 0:
        return jsonify({"hata": "Geçerli bir öğün numarası giriniz."}), 400

    try:
        secilen_tarih = date.fromisoformat(tarih)
    except (ValueError, TypeError):
        return jsonify({"hata": "Tarih YYYY-AA-GG biçiminde olmalıdır."}), 400

    if secilen_tarih < date.today():
        return jsonify({"hata": "Geçmiş tarihli menü oluşturulamaz."}), 400

    if (type(ogrenci_fiyati) not in (int, float)
            or type(personel_fiyati) not in (int, float)
            or not (0 < ogrenci_fiyati <= 10000)
            or not (0 < personel_fiyati <= 10000)):
        return jsonify({"hata": "Geçerli menü fiyatları giriniz."}), 400

    if (not isinstance(yemek_idleri, list)
            or not yemek_idleri
            or any(type(x) is not int or x <= 0 for x in yemek_idleri)
            or len(yemek_idleri) != len(set(yemek_idleri))):
        return jsonify({"hata": "Geçerli ve tekrarsız yemek numaraları giriniz."}), 400

    try:
        menu_id = yonetici_menu_ekle(
            yemekhane_id,
            secilen_tarih.isoformat(),
            ogun_id,
            ogrenci_fiyati,
            personel_fiyati,
            yemek_idleri
        )

        return jsonify({
            "mesaj": "Menü başarıyla oluşturuldu.",
            "menu_id": menu_id
        }), 201

    except Error as hata:
        if hata.errno == 1062:
            return jsonify({"hata": "Bu yemekhane, tarih ve öğün için zaten menü var."}), 409

        if hata.errno == 1452:
            return jsonify({"hata": "Yemekhane, öğün veya yemek numarası bulunamadı."}), 400

        current_app.logger.exception("Yönetici menü ekleme hatası")
        return jsonify({"hata": "Menü oluşturulurken bir hata oluştu."}), 500


@yonetici_bp.route("/api/yonetici/menu/duzenle", methods=["PUT"])
def yonetici_menu_guncelle():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    if kullanici["rol"] != "yonetici":
        return jsonify({"hata": "Bu işlem için yönetici yetkisi gerekiyor."}), 403

    veri = request.get_json(silent=True) or {}

    menu_id = veri.get("menu_id")
    ogrenci_fiyati = veri.get("ogrenci_fiyati")
    personel_fiyati = veri.get("personel_fiyati")
    yemek_idleri = veri.get("yemek_idleri")

    if type(menu_id) is not int or menu_id <= 0:
        return jsonify({"hata": "Geçerli bir menü numarası giriniz."}), 400

    if (type(ogrenci_fiyati) not in (int, float)
            or type(personel_fiyati) not in (int, float)
            or not (0 < ogrenci_fiyati <= 10000)
            or not (0 < personel_fiyati <= 10000)):
        return jsonify({"hata": "Geçerli menü fiyatları giriniz."}), 400

    if (not isinstance(yemek_idleri, list)
            or not yemek_idleri
            or any(type(x) is not int or x <= 0 for x in yemek_idleri)
            or len(yemek_idleri) != len(set(yemek_idleri))):
        return jsonify({"hata": "Geçerli ve tekrarsız yemek numaraları giriniz."}), 400

    try:
        basarili = yonetici_menu_duzenle(
            menu_id,
            ogrenci_fiyati,
            personel_fiyati,
            yemek_idleri
        )

        if not basarili:
            return jsonify({"hata": "Düzenlenecek menü bulunamadı."}), 404

        return jsonify({
            "mesaj": "Menü başarıyla güncellendi.",
            "menu_id": menu_id
        })

    except Error as hata:
        if hata.errno == 1452:
            return jsonify({"hata": "Girilen yemek numaralarından biri bulunamadı."}), 400

        current_app.logger.exception("Yönetici menü düzenleme hatası")
        return jsonify({"hata": "Menü güncellenirken bir hata oluştu."}), 500
