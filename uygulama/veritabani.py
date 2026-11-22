import os
import mysql.connector


def baglanti(tur="okuma"):
    if tur == "yazma":
        sunucu = "mysql-primary"
    else:
        sunucu = "mysql-replica"

    return mysql.connector.connect(
        host=sunucu,
        port=3306,
        user=os.getenv("DB_USER", "yemekhane_app"),
        password=os.getenv("DB_PASSWORD", "Uyg_2026"),
        database="yemekhane",
        charset="utf8mb4",
        autocommit=True
    )