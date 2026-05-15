from flask import Flask, render_template, jsonify
from config import Config
from services.gemini_service import GeminiService


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/nuevo")
    def nuevo():
        return render_template("nuevo.html")

    @app.route("/antiguo")
    def antiguo():
        return render_template("antiguo.html")

    @app.route("/exito")
    def exito():
        return render_template("exito.html")

    @app.route("/admin/logs")
    def admin_logs():
        return render_template("admin_logs.html")

    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "service": "openemr-kiosk",
            "version": "flask-mvp"
        }

    @app.route("/health/gemini")
    def health_gemini():
        try:
            gemini = GeminiService()
            result = gemini.test_connection()

            return jsonify({
                "status": "ok",
                "service": "gemini",
                "model": Config.GEMINI_MODEL,
                "response": result
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "service": "gemini",
                "message": str(e)
            }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)