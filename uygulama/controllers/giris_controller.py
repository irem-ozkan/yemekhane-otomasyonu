import bcrypt
from flask import Blueprint, jsonify, request
from kullanici_veri import kullanici_bul
from oturum import oturum_olustur, oturum_bul, oturum_sil

giris_bp = Blueprint("giris", __name__)


@giris_bp.route("/api/giris", methods=["POST"])
def giris():
    veri = request.get_json(silent=True) or {}

    eposta = str(veri.get("eposta", "")).strip()
    sifre = str(veri.get("sifre", ""))

    if not eposta or not sifre:
        return jsonify({"hata": "E-posta ve şifre zorunludur."}), 400

    kullanici = kullanici_bul(eposta)

    if kullanici is None or not kullanici["aktif"]:
        return jsonify({"hata": "E-posta veya şifre hatalı."}), 401

    if not bcrypt.checkpw(
        sifre.encode("utf-8"),
        kullanici["sifre_hash"].encode("utf-8")
    ):
        return jsonify({"hata": "E-posta veya şifre hatalı."}), 401

    token = oturum_olustur(kullanici)

    return jsonify({
        "mesaj": "Giriş başarılı.",
        "token": token,
        "kullanici": {
            "id": kullanici["id"],
            "ad": kullanici["ad"],
            "soyad": kullanici["soyad"],
            "eposta": kullanici["eposta"],
            "rol": kullanici["rol"]
        }
    })


@giris_bp.route("/api/ben", methods=["GET"])
def ben():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    return jsonify({"kullanici": kullanici})


@giris_bp.route("/api/cikis", methods=["POST"])
def cikis():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token or oturum_bul(token) is None:
        return jsonify({"hata": "Geçerli bir oturum bulunamadı."}), 401

    oturum_sil(token)

    return jsonify({"mesaj": "Çıkış başarılı."})
