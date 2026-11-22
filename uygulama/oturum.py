import json
import secrets
import redis

redis_db = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)


def oturum_olustur(kullanici):
    token = secrets.token_urlsafe(32)

    bilgi = {
        "id": kullanici["id"],
        "ad": kullanici["ad"],
        "soyad": kullanici["soyad"],
        "rol": kullanici["rol"]
    }

    redis_db.setex(
        "oturum:" + token,
        1800,
        json.dumps(bilgi, ensure_ascii=False)
    )

    return token


def oturum_bul(token):
    anahtar = "oturum:" + token

    bilgi = redis_db.get(anahtar)

    if bilgi is None:
        return None

    redis_db.expire(anahtar, 1800)

    return json.loads(bilgi)


def oturum_sil(token):
    redis_db.delete("oturum:" + token)