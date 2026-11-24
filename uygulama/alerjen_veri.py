from veritabani import baglanti


def alerjenleri_getir(kullanici_id):
    db = baglanti("okuma")
    imlec = db.cursor(dictionary=True)

    try:
        imlec.execute("""
            SELECT a.id, a.ad,
                   IF(ka.kullanici_id IS NULL, 0, 1) AS secili
            FROM alerjenler a
            LEFT JOIN kullanici_alerjenleri ka
                ON a.id = ka.alerjen_id
                AND ka.kullanici_id = %s
            ORDER BY a.id
        """, (kullanici_id,))

        return imlec.fetchall()

    finally:
        imlec.close()
        db.close()


def alerjenleri_kaydet(kullanici_id, alerjenler):
    db = baglanti("yazma")
    imlec = db.cursor()

    try:
        db.start_transaction()

        imlec.execute("SELECT id FROM alerjenler")
        gecerli_idler = [satir[0] for satir in imlec.fetchall()]

        for alerjen_id in alerjenler:
            if alerjen_id not in gecerli_idler:
                raise ValueError("Geçersiz alerjen seçimi.")

        imlec.execute("""
            DELETE FROM kullanici_alerjenleri
            WHERE kullanici_id = %s
        """, (kullanici_id,))

        for alerjen_id in set(alerjenler):
            imlec.execute("""
                INSERT INTO kullanici_alerjenleri
                    (kullanici_id, alerjen_id)
                VALUES (%s, %s)
            """, (kullanici_id, alerjen_id))

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        imlec.close()
        db.close()