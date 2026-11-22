from veritabani import baglanti


def rezervasyon_yap(kullanici_id, menu_id):
    db = baglanti("yazma")
    imlec = None

    try:
        imlec = db.cursor(dictionary=True)

        imlec.callproc(
            "sp_rezervasyon_yap",
            [kullanici_id, menu_id]
        )

        for sonuc in imlec.stored_results():
            satir = sonuc.fetchone()
            if satir is not None:
                return {
                    "rezervasyon_id": satir["rezervasyon_id"],
                    "ucret": float(satir["ucret"]),
                    "bakiye": float(satir["bakiye"])
                }

        return None

    finally:
        if imlec is not None:
            imlec.close()
        db.close()