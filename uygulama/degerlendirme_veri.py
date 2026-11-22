from veritabani import baglanti


def degerlendirme_ekle(kullanici_id, menu_id, puan, yorum):
    db = baglanti("yazma")
    imlec = None

    try:
        imlec = db.cursor()

        imlec.execute("""
            SELECT id
            FROM rezervasyonlar
            WHERE kullanici_id = %s
              AND menu_id = %s
              AND durum = 'kullanildi'
        """, (kullanici_id, menu_id))

        if imlec.fetchone() is None:
            return "kullanilmadi"

        imlec.execute("""
            SELECT id
            FROM degerlendirmeler
            WHERE kullanici_id = %s AND menu_id = %s
        """, (kullanici_id, menu_id))

        if imlec.fetchone() is not None:
            return "zaten_var"

        imlec.execute("""
            INSERT INTO degerlendirmeler
                (kullanici_id, menu_id, puan, yorum)
            VALUES (%s, %s, %s, %s)
        """, (kullanici_id, menu_id, puan, yorum))

        return "basarili"

    finally:
        if imlec is not None:
            imlec.close()
        db.close() 