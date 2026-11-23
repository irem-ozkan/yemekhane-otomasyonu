from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error
from oturum import oturum_bul
from bakiye_veri import bakiye_yukle, bakiye_bilgilerini_getir

bakiye_bp = Blueprint("bakiye", __name__)


@bakiye_bp.route("/api/bakiye/yukle", methods=["POST"])
def bakiye_yukleme():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    veri = request.get_json(silent=True) or {}
    tutar = veri.get("tutar")

    if type(tutar) not in (int, float) or not (10 <= tutar <= 1000):
        return jsonify({
            "hata": "Yükleme tutarı 10 ile 1000 TL arasında olmalıdır."
        }), 400

    try:
        sonuc = bakiye_yukle(kullanici["id"], tutar)

        if sonuc is None:
            return jsonify({"hata": "Bakiye yükleme sonucu alınamadı."}), 500

        return jsonify({
            "mesaj": "Bakiye başarıyla yüklendi.",
            "sonuc": sonuc
        }), 200

    except Error as hata:
        if hata.sqlstate == "45000":
            return jsonify({"hata": hata.msg}), 400

        current_app.logger.exception("Bakiye yükleme hatası")
        return jsonify({"hata": "Bakiye yüklenirken bir hata oluştu."}), 500


@bakiye_bp.route("/api/bakiye", methods=["GET"])
def bakiye_bilgileri():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    bilgi, satirlar = bakiye_bilgilerini_getir(kullanici["id"])

    if bilgi is None:
        return jsonify({"hata": "Kullanıcı bulunamadı."}), 404

    hareketler = []

    for satir in satirlar:
        hareketler.append({
            "id": satir["id"],
            "tur": satir["tur"],
            "tutar": float(satir["tutar"]),
            "rezervasyon_id": satir["rezervasyon_id"],
            "aciklama": satir["aciklama"],
            "olusturma": str(satir["olusturma"])
        })

    return jsonify({
        "bakiye": float(bilgi["bakiye"]),
        "hareketler": hareketler
    })
