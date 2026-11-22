from veritabani import baglanti


def gunluk_menuleri_getir(tarih):
    db = baglanti("okuma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.execute(
            """
            SELECT
                menu_id, tarih, yemekhane_id, yemekhane,
                ogun_id, ogun, ogun_sira, rezervasyon_son,
                ogrenci_fiyati, personel_fiyati,
                yemek_id, yemek, kategori, kategori_sira,
                kalori, vejetaryen, alerjenler
            FROM v_menu_detay
            WHERE tarih = %s
            ORDER BY yemekhane_id, ogun_sira, kategori_sira, yemek
            """,
            (tarih,)
        )

        return imlec.fetchall()

    finally:
        if imlec is not None:
            imlec.close()
        db.close()

def haftalik_menuleri_getir(baslangic, bitis):
    db = baglanti("okuma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.execute(
            """
            SELECT
                menu_id, tarih, yemekhane_id, yemekhane,
                ogun_id, ogun, ogun_sira, rezervasyon_son,
                ogrenci_fiyati, personel_fiyati,
                yemek_id, yemek, kategori, kategori_sira,
                kalori, vejetaryen, alerjenler
            FROM v_menu_detay
            WHERE tarih BETWEEN %s AND %s
            ORDER BY tarih, yemekhane_id, ogun_sira,
                     kategori_sira, yemek
            """,
            (baslangic, bitis)
        )

        return imlec.fetchall()

    finally:
        if imlec is not None:
            imlec.close()
        db.close()

def menu_doluluk_getir(menu_id):
    db = baglanti("okuma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.execute(
            """
            SELECT menu_id, kapasite, rezerve, bos_yer,
                   doluluk_yuzde, rezervasyon_son
            FROM v_menu_doluluk
            WHERE menu_id = %s
            """,
            (menu_id,)
        )

        return imlec.fetchone()

    finally:
        if imlec is not None:
            imlec.close()
        db.close()