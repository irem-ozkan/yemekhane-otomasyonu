from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error
from oturum import oturum_bul
from rezervasyon_veri import rezervasyon_yap, rezervasyonlari_getir, rezervasyon_iptal

rezervasyon_bp = Blueprint("rezervasyon", __name__)


@rezervasyon_bp.route("/api/rezervasyon/yap", methods=["POST"])
def rezervasyon_olustur():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    veri = request.get_json(silent=True) or {}
    menu_id = veri.get("menu_id")

    if type(menu_id) is not int or menu_id <= 0:
        return jsonify({"hata": "Geçerli bir menü numarası giriniz."}), 400

    try:
        sonuc = rezervasyon_yap(kullanici["id"], menu_id)

        if sonuc is None:
            return jsonify({"hata": "Rezervasyon sonucu alınamadı."}), 500

        return jsonify({
            "mesaj": "Rezervasyon başarılı.",
            "rezervasyon": sonuc
        }), 201

    except Error as hata:
        if hata.sqlstate == "45000":
            return jsonify({"hata": hata.msg}), 400

        current_app.logger.exception("Rezervasyon veritabanı hatası")
        return jsonify({"hata": "Rezervasyon sırasında bir hata oluştu."}), 500


@rezervasyon_bp.route("/api/rezervasyonlar", methods=["GET"])
def rezervasyonlari_listele():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    satirlar = rezervasyonlari_getir(kullanici["id"])

    rezervasyonlar = []

    for satir in satirlar:
        rezervasyonlar.append({
            "id": satir["id"],
            "menu_id": satir["menu_id"],
            "durum": satir["durum"],
            "ucret": float(satir["ucret"]),
            "olusturma": str(satir["olusturma"]),
            "kullanma_zamani": str(satir["kullanma_zamani"]) if satir["kullanma_zamani"] else None,
            "iptal_zamani": str(satir["iptal_zamani"]) if satir["iptal_zamani"] else None,
            "tarih": str(satir["tarih"]),
            "yemekhane": satir["yemekhane"],
            "ogun": satir["ogun"]
        })

    return jsonify({"rezervasyonlar": rezervasyonlar})


@rezervasyon_bp.route("/api/rezervasyon/iptal", methods=["POST"])
def rezervasyon_iptal_et():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    veri = request.get_json(silent=True) or {}
    rezervasyon_id = veri.get("rezervasyon_id")

    if type(rezervasyon_id) is not int or rezervasyon_id <= 0:
        return jsonify({"hata": "Geçerli bir rezervasyon numarası giriniz."}), 400

    try:
        sonuc = rezervasyon_iptal(kullanici["id"], rezervasyon_id)

        if sonuc is None:
            return jsonify({"hata": "İptal sonucu alınamadı."}), 500

        return jsonify({
            "mesaj": "Rezervasyon iptal edildi.",
            "sonuc": sonuc
        })

    except Error as hata:
        if hata.sqlstate == "45000":
            return jsonify({"hata": hata.msg}), 400

        current_app.logger.exception("Rezervasyon iptal hatası")
        return jsonify({"hata": "Rezervasyon iptal edilirken bir hata oluştu."}), 500
