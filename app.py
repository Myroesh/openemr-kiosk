from flask import Flask, render_template, jsonify, request, redirect, url_for, session

from config import Config
from services.gemini_service import GeminiService
from services.db_service import (
    init_db,
    create_patient_intake,
    create_kiosk_event,
    list_recent_events,
    list_recent_intakes,
)


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
            data = {
                "flow_type": "nuevo",
                "nombres": request.form.get("nombres", "").strip(),
                "apellidos": request.form.get("apellidos", "").strip(),
                "fecha_nacimiento": request.form.get("fecha_nacimiento", "").strip(),
                "ci_documento": request.form.get("ci_documento", "").strip(),
                "telefono": request.form.get("telefono", "").strip(),
                "direccion": request.form.get("direccion", "").strip(),
                "motivo_consulta": request.form.get("motivo_consulta", "").strip(),
                "profesional_area": request.form.get("profesional_area", "").strip(),
                "es_menor": 1 if request.form.get("es_menor") == "1" else 0,
                "padre_nombre": request.form.get("padre_nombre", "").strip(),
                "padre_ci": request.form.get("padre_ci", "").strip(),
                "padre_telefono": request.form.get("padre_telefono", "").strip(),
                "madre_nombre": request.form.get("madre_nombre", "").strip(),
                "madre_ci": request.form.get("madre_ci", "").strip(),
                "madre_telefono": request.form.get("madre_telefono", "").strip(),
            }

            errors = []

            if not data["nombres"]:
                errors.append("El nombre es obligatorio.")

            if not data["apellidos"]:
                errors.append("El apellido es obligatorio.")

            if not data["fecha_nacimiento"]:
                errors.append("La fecha de nacimiento es obligatoria.")

            if not data["telefono"]:
                errors.append("El teléfono es obligatorio.")

            if not data["motivo_consulta"]:
                errors.append("El motivo de consulta es obligatorio.")

            if not data["profesional_area"]:
                errors.append("Debe seleccionar un profesional.")

            if data["profesional_area"] and data["profesional_area"] not in Config.PROFESSIONALS:
                errors.append("El profesional seleccionado no es válido.")

            if data["es_menor"] and not data["padre_nombre"] and not data["madre_nombre"]:
                errors.append("Para menores de edad, registre al menos el nombre del padre o de la madre.")

            if errors:
                create_kiosk_event(
                    event_type="validation_error",
                    flow_type="nuevo",
                    status="error",
                    message="Formulario de paciente nuevo con datos incompletos",
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
                message="Datos capturados, pendientes de confirmación final",
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
            data = {
                "flow_type": "antiguo",
                "nombre": request.form.get("nombre", "").strip(),
                "telefono": request.form.get("telefono", "").strip(),
                "profesional_area": request.form.get("profesional_area", "").strip(),
                "motivo_consulta": request.form.get("motivo_consulta", "").strip(),
            }

            errors = []

            if not data["nombre"] and not data["telefono"]:
                errors.append("Debe ingresar nombre del paciente o teléfono.")

            if not data["profesional_area"]:
                errors.append("Debe seleccionar un profesional.")

            if data["profesional_area"] and data["profesional_area"] not in Config.PROFESSIONALS:
                errors.append("El profesional seleccionado no es válido.")

            if not data["motivo_consulta"]:
                errors.append("Debe ingresar el motivo de consulta.")

            if errors:
                create_kiosk_event(
                    event_type="validation_error",
                    flow_type="antiguo",
                    status="error",
                    message="Búsqueda de paciente antiguo con datos incompletos",
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
                message="Datos de paciente antiguo capturados, pendientes de confirmación final",
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


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)