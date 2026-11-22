from veritabani import baglanti


def bakiye_yukle(kullanici_id, tutar):
    db = baglanti("yazma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.callproc(
            "sp_bakiye_yukle",
            [kullanici_id, tutar]
        )

        for sonuc in imlec.stored_results():
            satir = sonuc.fetchone()

            if satir is not None:
                return {
                    "hareket_id": satir["hareket_id"],
                    "bakiye": float(satir["bakiye"])
                }

        return None

    finally:
        if imlec is not None:
            imlec.close()
        db.close()

def bakiye_bilgilerini_getir(kullanici_id):
    db = baglanti("okuma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.execute("""
            SELECT id, bakiye
            FROM kullanicilar
            WHERE id = %s
        """, (kullanici_id,))

        kullanici = imlec.fetchone()

        imlec.execute("""
            SELECT id, tur, tutar, rezervasyon_id,
                   aciklama, olusturma
            FROM bakiye_hareketleri
            WHERE kullanici_id = %s
            ORDER BY olusturma DESC
        """, (kullanici_id,))

        hareketler = imlec.fetchall()

        return kullanici, hareketler

    finally:
        if imlec is not None:
            imlec.close()
        db.close() 