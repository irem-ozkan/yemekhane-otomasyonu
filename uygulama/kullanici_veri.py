from veritabani import baglanti


def kullanici_bul(eposta):
    db = baglanti("okuma")

    try:
        imlec = db.cursor(dictionary=True)

        imlec.execute(
            """
            SELECT id, ad, soyad, eposta, sifre_hash, rol, aktif
            FROM kullanicilar
            WHERE eposta = %s
            """,
            (eposta,)
        )

        return imlec.fetchone()

    finally:
        imlec.close()
        db.close()