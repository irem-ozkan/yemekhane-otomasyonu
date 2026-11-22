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
from yonetici_veri import yonetici_menuleri_getir, yonetici_menu_ekle, yonetici_menu_duzenle

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

@app.route("/api/yonetici/menuler", methods=["GET"])
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
@app.route("/api/yonetici/menu/ekle", methods=["POST"])
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

        app.logger.exception("Yönetici menü ekleme hatası")
        return jsonify({"hata": "Menü oluşturulurken bir hata oluştu."}), 500
    
@app.route("/api/yonetici/menu/duzenle", methods=["PUT"])
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

        app.logger.exception("Yönetici menü düzenleme hatası")
        return jsonify({"hata": "Menü güncellenirken bir hata oluştu."}), 500
     
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)  