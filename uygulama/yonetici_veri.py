from veritabani import baglanti
from menu_onbellek import menu_onbellek_temizle


def yonetici_menuleri_getir():
    db = baglanti("okuma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.execute("""
            SELECT
                m.id AS menu_id,
                m.tarih,
                y.ad AS yemekhane,
                o.ad AS ogun,
                m.ogrenci_fiyati,
                m.personel_fiyati,
                d.kapasite,
                d.rezerve,
                d.bos_yer,
                d.doluluk_yuzde,
                p.oy_sayisi,
                p.ortalama_puan
            FROM menuler m
            JOIN yemekhaneler y ON m.yemekhane_id = y.id
            JOIN ogunler o ON m.ogun_id = o.id
            JOIN v_menu_doluluk d ON d.menu_id = m.id
            LEFT JOIN v_menu_puan p ON p.menu_id = m.id
            ORDER BY m.tarih DESC, y.ad, o.sira
        """)

        return imlec.fetchall()

    finally:
        if imlec is not None:
            imlec.close()
        db.close()


def yonetici_menu_ekle(yemekhane_id, tarih, ogun_id,
                       ogrenci_fiyati, personel_fiyati, yemek_idleri):

    db = baglanti("yazma")
    db.autocommit = False
    imlec = None

    try:
        db.start_transaction()
        imlec = db.cursor()

        imlec.execute("""
            INSERT INTO menuler
                (yemekhane_id, tarih, ogun_id, ogrenci_fiyati, personel_fiyati)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            yemekhane_id, tarih, ogun_id,
            ogrenci_fiyati, personel_fiyati
        ))

        menu_id = imlec.lastrowid

        for yemek_id in yemek_idleri:
            imlec.execute("""
                INSERT INTO menu_yemekleri (menu_id, yemek_id)
                VALUES (%s, %s)
            """, (menu_id, yemek_id))

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        if imlec is not None:
            imlec.close()
        db.close()

    menu_onbellek_temizle(yemekhane_id, tarih, ogun_id)

    return menu_id


def yonetici_menu_duzenle(menu_id, ogrenci_fiyati,
                          personel_fiyati, yemek_idleri):

    db = baglanti("yazma")
    db.autocommit = False
    imlec = None

    try:
        db.start_transaction()
        imlec = db.cursor()

        imlec.execute("""
            SELECT yemekhane_id, tarih, ogun_id
            FROM menuler
            WHERE id = %s
            FOR UPDATE
        """, (menu_id,))

        bilgi = imlec.fetchone()

        if bilgi is None:
            db.rollback()
            return False

        yemekhane_id, tarih, ogun_id = bilgi

        imlec.execute("""
            UPDATE menuler
            SET ogrenci_fiyati = %s,
                personel_fiyati = %s
            WHERE id = %s
        """, (ogrenci_fiyati, personel_fiyati, menu_id))

        imlec.execute("""
            DELETE FROM menu_yemekleri
            WHERE menu_id = %s
        """, (menu_id,))

        for yemek_id in yemek_idleri:
            imlec.execute("""
                INSERT INTO menu_yemekleri (menu_id, yemek_id)
                VALUES (%s, %s)
            """, (menu_id, yemek_id))

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        if imlec is not None:
            imlec.close()
        db.close()

    menu_onbellek_temizle(yemekhane_id, tarih, ogun_id)

    return True