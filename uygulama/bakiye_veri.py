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