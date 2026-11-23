from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error
from oturum import oturum_bul
from degerlendirme_veri import degerlendirme_ekle

degerlendirme_bp = Blueprint("degerlendirme", __name__)


@degerlendirme_bp.route("/api/degerlendirme/ekle", methods=["POST"])
def degerlendirme_olustur():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    veri = request.get_json(silent=True) or {}

    menu_id = veri.get("menu_id")
    puan = veri.get("puan")
    yorum = veri.get("yorum", "")

    if type(menu_id) is not int or menu_id <= 0:
        return jsonify({"hata": "Geçerli bir menü numarası giriniz."}), 400

    if type(puan) is not int or not (1 <= puan <= 5):
        return jsonify({"hata": "Puan 1 ile 5 arasında olmalıdır."}), 400

    if not isinstance(yorum, str) or len(yorum) > 500:
        return jsonify({"hata": "Yorum en fazla 500 karakter olabilir."}), 400

    try:
        sonuc = degerlendirme_ekle(kullanici["id"], menu_id, puan, yorum)

        if sonuc == "kullanilmadi":
            return jsonify({
                "hata": "Yalnızca kullandığınız rezervasyonları değerlendirebilirsiniz."
            }), 400

        if sonuc == "zaten_var":
            return jsonify({
                "hata": "Bu menüyü daha önce değerlendirdiniz."
            }), 400

        return jsonify({"mesaj": "Değerlendirme başarıyla kaydedildi."}), 201

    except Error:
        current_app.logger.exception("Değerlendirme hatası")
        return jsonify({"hata": "Değerlendirme kaydedilemedi."}), 500
