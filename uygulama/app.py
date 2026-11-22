import bcrypt
from rezervasyon_veri import rezervasyon_yap
from mysql.connector import Error 
from menu_veri import gunluk_menuleri_getir, haftalik_menuleri_getir, menu_doluluk_getir
from datetime import date, datetime, timedelta
from decimal import Decimal
from flask import Flask, jsonify, request
from kullanici_veri import kullanici_bul
from oturum import oturum_olustur, oturum_bul, oturum_sil
from bakiye_veri import bakiye_yukle

app = Flask(__name__)
app.json.ensure_ascii = False


@app.route("/api/saglik")
def saglik():
    return jsonify({"durum": "calisiyor"})


@app.route("/api/giris", methods=["POST"])
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


@app.route("/api/ben", methods=["GET"])
def ben():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        return jsonify({"hata": "Oturum açmanız gerekiyor."}), 401

    kullanici = oturum_bul(token)

    if kullanici is None:
        return jsonify({"hata": "Oturum süresi dolmuş veya geçersiz."}), 401

    return jsonify({"kullanici": kullanici})


@app.route("/api/cikis", methods=["POST"])
def cikis():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token or oturum_bul(token) is None:
        return jsonify({"hata": "Geçerli bir oturum bulunamadı."}), 401

    oturum_sil(token)

    return jsonify({"mesaj": "Çıkış başarılı."})

@app.route("/api/menuler/gunluk", methods=["GET"])
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


@app.route("/api/menuler/haftalik", methods=["GET"])
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

@app.route("/api/menuler/<int:menu_id>/doluluk", methods=["GET"])
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

@app.route("/api/rezervasyon/yap", methods=["POST"])
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

        app.logger.exception("Rezervasyon veritabanı hatası")
        return jsonify({"hata": "Rezervasyon sırasında bir hata oluştu."}), 500

@app.route("/api/bakiye/yukle", methods=["POST"])
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

        app.logger.exception("Bakiye yükleme hatası")
        return jsonify({"hata": "Bakiye yüklenirken bir hata oluştu."}), 500   

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)  