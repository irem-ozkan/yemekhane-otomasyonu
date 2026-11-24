from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error
from oturum import oturum_bul
from alerjen_veri import alerjenleri_getir, alerjenleri_kaydet

profil_bp = Blueprint("profil", __name__)


@profil_bp.route("/api/profil/alerjenler", methods=["GET"])
def profil_getir():
    token = request.headers.get(
        "Authorization", ""
    ).removeprefix("Bearer ").strip()

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    try:
        alerjenler = alerjenleri_getir(kullanici["id"])

        return jsonify({
            "kullanici": kullanici,
            "alerjenler": alerjenler
        })

    except Error:
        current_app.logger.exception("Profil okuma hatası")
        return jsonify({"hata": "Profil bilgileri alınamadı."}), 500


@profil_bp.route("/api/profil/alerjenler", methods=["PUT"])
def profil_guncelle():
    token = request.headers.get(
        "Authorization", ""
    ).removeprefix("Bearer ").strip()

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    veri = request.get_json(silent=True) or {}
    alerjenler = veri.get("alerjenler")

    if not isinstance(alerjenler, list):
        return jsonify({"hata": "Geçersiz alerjen listesi."}), 400

    for alerjen_id in alerjenler:
        if type(alerjen_id) is not int or alerjen_id <= 0:
            return jsonify({"hata": "Geçersiz alerjen seçimi."}), 400

    try:
        alerjenleri_kaydet(kullanici["id"], alerjenler)

        return jsonify({
            "mesaj": "Alerjen tercihleriniz kaydedildi."
        })

    except ValueError as hata:
        return jsonify({"hata": str(hata)}), 400

    except Error:
        current_app.logger.exception("Profil kaydetme hatası")
        return jsonify({"hata": "Alerjenler kaydedilemedi."}), 500