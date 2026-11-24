from flask import Flask, jsonify
from controllers.giris_controller import giris_bp
from controllers.menu_controller import menu_bp
from controllers.rezervasyon_controller import rezervasyon_bp
from controllers.bakiye_controller import bakiye_bp
from controllers.degerlendirme_controller import degerlendirme_bp
from controllers.yonetici_controller import yonetici_bp
from controllers.profil_controller import profil_bp

app = Flask(__name__)
app.json.ensure_ascii = False


@app.route("/api/saglik")
def saglik():
    return jsonify({"durum": "calisiyor"})


app.register_blueprint(giris_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(rezervasyon_bp)
app.register_blueprint(bakiye_bp)
app.register_blueprint(degerlendirme_bp)
app.register_blueprint(yonetici_bp)
app.register_blueprint(profil_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)