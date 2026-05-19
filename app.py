from functools import wraps

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    session,
    Response,
)

from config import Config
from services.gemini_service import GeminiService
from services.openemr_service import OpenEMRService, OpenEMRServiceError
from services.db_service import (
    init_db,
    create_patient_intake,
    create_kiosk_event,
    list_recent_events,
    list_recent_intakes,
)
from services.validation_service import (
    validate_new_patient_data,
    validate_existing_patient_data,
)


def check_admin_auth(username, password):
    return (
        username == Config.ADMIN_USERNAME
        and Config.ADMIN_PASSWORD
        and password == Config.ADMIN_PASSWORD
    )


def admin_auth_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth = request.authorization

        if not auth or not check_admin_auth(auth.username, auth.password):
            return Response(
                "Acceso restringido al panel interno del kiosko.",
                401,
                {"WWW-Authenticate": 'Basic realm="OpenEMR Kiosk Admin"'},
            )

        return view_func(*args, **kwargs)

    return wrapper


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db()

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/nuevo", methods=["GET", "POST"])
    def nuevo():
        if request.method == "POST":
            data, errors = validate_new_patient_data(
                request.form,
                Config.PROFESSIONALS,
            )

            if errors:
                create_kiosk_event(
                    event_type="validation_error",
                    flow_type="nuevo",
                    status="error",
                    message="Formulario de paciente nuevo con datos incompletos o inválidos",
                    metadata={"errors": errors},
                )

                return render_template(
                    "nuevo.html",
                    errors=errors,
                    form=data,
                    professionals=Config.PROFESSIONALS,
                )

            session["pending_intake"] = data

            create_kiosk_event(
                event_type="pending_confirmation",
                flow_type="nuevo",
                status="ok",
                message="Datos capturados, normalizados y pendientes de confirmación final",
                metadata={
                    "ci_documento_present": bool(data.get("ci_documento")),
                    "telefono_present": bool(data.get("telefono")),
                    "es_menor": bool(data.get("es_menor")),
                    "padre_present": bool(data.get("padre_nombre")),
                    "madre_present": bool(data.get("madre_nombre")),
                    "profesional_area": data.get("profesional_area"),
                },
            )

            return redirect(url_for("confirmar"))

        return render_template(
            "nuevo.html",
            errors=[],
            form={},
            professionals=Config.PROFESSIONALS,
        )

    @app.route("/antiguo", methods=["GET", "POST"])
    def antiguo():
        if request.method == "POST":
            data, errors = validate_existing_patient_data(
                request.form,
                Config.PROFESSIONALS,
            )

            if errors:
                create_kiosk_event(
                    event_type="validation_error",
                    flow_type="antiguo",
                    status="error",
                    message="Búsqueda de paciente antiguo con datos incompletos o inválidos",
                    metadata={"errors": errors},
                )

                return render_template(
                    "antiguo.html",
                    errors=errors,
                    form=data,
                    professionals=Config.PROFESSIONALS,
                )

            session["pending_existing"] = data

            create_kiosk_event(
                event_type="pending_confirmation",
                flow_type="antiguo",
                status="ok",
                message="Datos de paciente antiguo capturados, normalizados y pendientes de confirmación final",
                metadata={
                    "nombre_present": bool(data.get("nombre")),
                    "telefono_present": bool(data.get("telefono")),
                    "profesional_area": data.get("profesional_area"),
                    "motivo_consulta_present": bool(data.get("motivo_consulta")),
                },
            )

            return redirect(url_for("confirmar_antiguo"))

        return render_template(
            "antiguo.html",
            errors=[],
            form={},
            professionals=Config.PROFESSIONALS,
        )

    @app.route("/confirmar", methods=["GET", "POST"])
    def confirmar():
        data = session.get("pending_intake")

        if not data:
            return redirect(url_for("index"))

        if request.method == "POST":
            intake_id = create_patient_intake(data)
            session.pop("pending_intake", None)

            return redirect(url_for("exito", intake_id=intake_id))

        return render_template("confirmar.html", data=data)

    @app.route("/confirmar-antiguo", methods=["GET", "POST"])
    def confirmar_antiguo():
        data = session.get("pending_existing")

        if not data:
            return redirect(url_for("index"))

        if request.method == "POST":
            create_kiosk_event(
                event_type="existing_patient_search_confirmed",
                flow_type="antiguo",
                status="pending_openemr",
                message="Paciente antiguo confirmado localmente; pendiente búsqueda/encounter en OpenEMR",
                metadata={
                    "nombre_present": bool(data.get("nombre")),
                    "telefono_present": bool(data.get("telefono")),
                    "profesional_area": data.get("profesional_area"),
                    "motivo_consulta_present": bool(data.get("motivo_consulta")),
                },
            )

            session.pop("pending_existing", None)

            return redirect(url_for("exito"))

        return render_template("confirmar_antiguo.html", data=data)

    @app.route("/exito")
    def exito():
        intake_id = request.args.get("intake_id")
        return render_template("exito.html", intake_id=intake_id)

    @app.route("/admin/logs")
    @admin_auth_required
    def admin_logs():
        events = list_recent_events(limit=100)
        intakes = list_recent_intakes(limit=100)

        return render_template(
            "admin_logs.html",
            events=events,
            intakes=intakes,
        )

    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "service": "openemr-kiosk",
            "version": "flask-mvp",
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
                "response": result,
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "service": "gemini",
                "message": str(e),
            }), 500

    return app
    
    @app.route("/health/openemr")
    @admin_auth_required
    def health_openemr():
        try:
            openemr = OpenEMRService()
            result = openemr.health_check()

            return jsonify({
                "status": "ok",
                "service": "openemr",
                "result": result,
            })

        except OpenEMRServiceError as e:
            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": str(e),
            }), 500

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)