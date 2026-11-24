from veritabani import baglanti


def rezervasyon_yap(kullanici_id, menu_id, porsiyon):
    db = baglanti("yazma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.callproc(
            "sp_rezervasyon_yap",
            [kullanici_id, menu_id, porsiyon]
        )

        for sonuc in imlec.stored_results():
            satir = sonuc.fetchone()

            if satir is not None:
                return {
                    "rezervasyon_id": satir["rezervasyon_id"],
                    "ucret": float(satir["ucret"]),
                    "bakiye": float(satir["bakiye"]),
                    "porsiyon": satir["porsiyon"]
                }

        return None

    finally:
        if imlec is not None:
            imlec.close()
        db.close()


def rezervasyonlari_getir(kullanici_id):
    db = baglanti("okuma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.execute("""
            SELECT
                r.id,
                r.menu_id,
                r.durum,
                r.ucret,
                r.porsiyon,
                r.olusturma,
                r.kullanma_zamani,
                r.iptal_zamani,
                m.tarih,
                y.ad AS yemekhane,
                o.ad AS ogun
            FROM rezervasyonlar r
            JOIN menuler m ON r.menu_id = m.id
            JOIN yemekhaneler y ON m.yemekhane_id = y.id
            JOIN ogunler o ON m.ogun_id = o.id
            WHERE r.kullanici_id = %s
            ORDER BY r.olusturma DESC
        """, (kullanici_id,))

        return imlec.fetchall()

    finally:
        if imlec is not None:
            imlec.close()
        db.close()


def rezervasyon_iptal(kullanici_id, rezervasyon_id):
    db = baglanti("yazma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.callproc(
            "sp_rezervasyon_iptal",
            [kullanici_id, rezervasyon_id]
        )

        for sonuc in imlec.stored_results():
            satir = sonuc.fetchone()

            if satir is not None:
                return {
                    "rezervasyon_id": satir["rezervasyon_id"],
                    "iade": float(satir["iade"]),
                    "bakiye": float(satir["bakiye"])
                }

        return None

    finally:
        if imlec is not None:
            imlec.close()
        db.close()