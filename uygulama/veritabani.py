import os
import mysql.connector


def baglanti(tur="okuma"):
    if tur == "yazma":
        sunucu = os.environ["DB_YAZMA_HOST"]
    else:
        sunucu = os.environ["DB_OKUMA_HOST"]

    return mysql.connector.connect(
        host=sunucu,
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_KULLANICI"],
        password=os.environ["DB_SIFRE"],
        database=os.environ["DB_ADI"],
        charset="utf8mb4",
        autocommit=True
    )