import bcrypt
from rezervasyon_veri import rezervasyon_yap, rezervasyonlari_getir, rezervasyon_iptal
from mysql.connector import Error 
from menu_veri import gunluk_menuleri_getir, haftalik_menuleri_getir, menu_doluluk_getir
from datetime import date, datetime, timedelta
from decimal import Decimal
from flask import Flask, jsonify, request
from kullanici_veri import kullanici_bul
from oturum import oturum_olustur, oturum_bul, oturum_sil
from bakiye_veri import bakiye_yukle, bakiye_bilgilerini_getir
from degerlendirme_veri import degerlendirme_ekle

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

@app.route("/api/rezervasyonlar", methods=["GET"])
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

@app.route("/api/rezervasyon/iptal", methods=["POST"])
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

        app.logger.exception("Rezervasyon iptal hatası")
        return jsonify({"hata": "Rezervasyon iptal edilirken bir hata oluştu."}), 500

@app.route("/api/bakiye", methods=["GET"])
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

@app.route("/api/degerlendirme/ekle", methods=["POST"])
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
        app.logger.exception("Değerlendirme hatası")
        return jsonify({"hata": "Değerlendirme kaydedilemedi."}), 500

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)  