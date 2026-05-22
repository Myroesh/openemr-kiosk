import secrets
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
from services.token_store import (
    calculate_expires_at,
    public_token_status,
    save_openemr_tokens,
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

            try:
                openemr = OpenEMRService()
                duplicate_result = openemr.search_patients(
                    query=f"{data.get('nombres', '')} {data.get('apellidos', '')}",
                    phone=data.get("telefono"),
                    limit=5,
                )

            except OpenEMRServiceError as e:
                create_kiosk_event(
                    event_type="openemr_duplicate_search_error",
                    flow_type="nuevo",
                    status="error",
                    message="Error al buscar duplicados en OpenEMR antes de crear paciente nuevo",
                    metadata={
                        "error": str(e),
                        "ci_documento_present": bool(data.get("ci_documento")),
                        "telefono_present": bool(data.get("telefono")),
                    },
                )

                return render_template(
                    "nuevo.html",
                    errors=[
                        "No se pudo verificar si el paciente ya existe. Avise a recepción."
                    ],
                    form=data,
                    professionals=Config.PROFESSIONALS,
                )

            duplicate_count = duplicate_result.get("matched_count", 0)

            if duplicate_count > 0:
                create_kiosk_event(
                    event_type="new_patient_possible_duplicate",
                    flow_type="nuevo",
                    status="blocked",
                    message="Posible paciente duplicado detectado antes de crear paciente nuevo",
                    metadata={
                        "duplicate_count": duplicate_count,
                        "ci_documento_present": bool(data.get("ci_documento")),
                        "telefono_present": bool(data.get("telefono")),
                    },
                )

                return render_template(
                    "nuevo.html",
                    errors=[
                        "Encontramos un paciente registrado con datos similares. Por seguridad, pida ayuda en recepción."
                    ],
                    form=data,
                    professionals=Config.PROFESSIONALS,
                )

            session.pop("pending_intake_processing", None)
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

            try:
                openemr = OpenEMRService()
                search_result = openemr.search_patients(
                    query=data.get("nombre"),
                    phone=data.get("telefono"),
                    limit=5,
                )

            except OpenEMRServiceError as e:
                create_kiosk_event(
                    event_type="openemr_search_error",
                    flow_type="antiguo",
                    status="error",
                    message="Error al buscar paciente antiguo en OpenEMR",
                    metadata={
                        "error": str(e),
                        "nombre_present": bool(data.get("nombre")),
                        "telefono_present": bool(data.get("telefono")),
                    },
                )

                return render_template(
                    "antiguo.html",
                    errors=[
                        "No se pudo consultar OpenEMR en este momento. Avise a recepción."
                    ],
                    form=data,
                    professionals=Config.PROFESSIONALS,
                )

            matches = search_result.get("patients", [])
            matched_count = search_result.get("matched_count", 0)

            if matched_count == 0:
                create_kiosk_event(
                    event_type="existing_patient_not_found",
                    flow_type="antiguo",
                    status="not_found",
                    message="No se encontró paciente antiguo en OpenEMR",
                    metadata={
                        "nombre_present": bool(data.get("nombre")),
                        "telefono_present": bool(data.get("telefono")),
                    },
                )

                return render_template(
                    "antiguo.html",
                    errors=[
                        "No encontramos un paciente registrado con esos datos. Revise el nombre/teléfono o pida ayuda en recepción."
                    ],
                    form=data,
                    professionals=Config.PROFESSIONALS,
                )

            if matched_count > 1:
                create_kiosk_event(
                    event_type="existing_patient_multiple_matches",
                    flow_type="antiguo",
                    status="multiple_matches",
                    message="La búsqueda devolvió múltiples pacientes posibles",
                    metadata={
                        "matched_count": matched_count,
                        "nombre_present": bool(data.get("nombre")),
                        "telefono_present": bool(data.get("telefono")),
                    },
                )

                return render_template(
                    "antiguo.html",
                    errors=[
                        "Encontramos más de un paciente posible. Por seguridad, pida ayuda en recepción."
                    ],
                    form=data,
                    professionals=Config.PROFESSIONALS,
                )

            matched_patient = matches[0]

            data["openemr_patient"] = matched_patient
            data["openemr_pid"] = matched_patient.get("pid")
            data["openemr_uuid"] = matched_patient.get("uuid")
            data["openemr_pubpid"] = matched_patient.get("pubpid")

            session.pop("pending_existing_processing", None)
            session["pending_existing"] = data

            create_kiosk_event(
                event_type="existing_patient_found_pending_confirmation",
                flow_type="antiguo",
                status="ok",
                message="Paciente antiguo encontrado en OpenEMR y pendiente de confirmación final",
                metadata={
                    "openemr_pid_present": bool(data.get("openemr_pid")),
                    "openemr_uuid_present": bool(data.get("openemr_uuid")),
                    "openemr_pubpid_present": bool(data.get("openemr_pubpid")),
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
            if session.get("pending_intake_processing"):
                create_kiosk_event(
                    event_type="new_patient_duplicate_submit_blocked",
                    flow_type="nuevo",
                    status="blocked",
                    message="Intento duplicado de confirmar paciente nuevo bloqueado",
                    metadata={
                        "ci_documento_present": bool(data.get("ci_documento")),
                        "telefono_present": bool(data.get("telefono")),
                    },
                )

                return redirect(url_for("exito"))

            session["pending_intake_processing"] = True

            try:
                openemr = OpenEMRService()

                duplicate_result = openemr.search_patients(
                    query=f"{data.get('nombres', '')} {data.get('apellidos', '')}",
                    phone=data.get("telefono"),
                    limit=5,
                )

                duplicate_count = duplicate_result.get("matched_count", 0)

                if duplicate_count > 0:
                    create_kiosk_event(
                        event_type="new_patient_duplicate_found_on_confirmation",
                        flow_type="nuevo",
                        status="blocked",
                        message="Posible duplicado detectado al confirmar creación de paciente nuevo",
                        metadata={
                            "duplicate_count": duplicate_count,
                            "ci_documento_present": bool(data.get("ci_documento")),
                            "telefono_present": bool(data.get("telefono")),
                        },
                    )

                    session.pop("pending_intake_processing", None)

                    return render_template(
                        "confirmar.html",
                        data=data,
                        errors=[
                            "Antes de guardar, encontramos un paciente registrado con datos similares. Por seguridad, pida ayuda en recepción."
                        ],
                    )

                patient_payload = openemr.build_kiosk_patient_payload(data)
                patient_result = openemr.create_patient(patient_payload)

                patient_result_data = (
                    patient_result.get("data", {})
                    if isinstance(patient_result, dict)
                    else {}
                )
                openemr_patient_id = patient_result_data.get("pid")
                openemr_patient_uuid = patient_result_data.get("uuid")

                if not openemr_patient_uuid:
                    raise OpenEMRServiceError(
                        "OpenEMR creó el paciente, pero no devolvió uuid para crear encounter."
                    )

                encounter_payload = openemr.build_kiosk_encounter_payload(
                    motivo_consulta=data.get("motivo_consulta"),
                    professional_area=data.get("profesional_area"),
                )

                encounter_result = openemr.create_encounter_for_patient(
                    patient_uuid=openemr_patient_uuid,
                    encounter_data=encounter_payload,
                )

                encounter_result_data = (
                    encounter_result.get("data", {})
                    if isinstance(encounter_result, dict)
                    else {}
                )
                openemr_encounter_id = encounter_result_data.get("encounter")
                openemr_encounter_uuid = encounter_result_data.get("uuid")

                intake_id = create_patient_intake(data)

                create_kiosk_event(
                    event_type="new_patient_created_with_encounter",
                    flow_type="nuevo",
                    status="ok",
                    message="Paciente nuevo y encounter inicial creados en OpenEMR después de confirmación final",
                    intake_id=intake_id,
                    metadata={
                        "openemr_patient_id": openemr_patient_id,
                        "openemr_patient_uuid_present": bool(openemr_patient_uuid),
                        "openemr_encounter_id": openemr_encounter_id,
                        "openemr_encounter_uuid_present": bool(openemr_encounter_uuid),
                        "ci_documento_present": bool(data.get("ci_documento")),
                        "telefono_present": bool(data.get("telefono")),
                        "sexo_present": bool(data.get("sexo")),
                        "profesional_area": data.get("profesional_area"),
                        "motivo_consulta_present": bool(data.get("motivo_consulta")),
                    },
                )

                session.pop("pending_intake", None)
                session.pop("pending_intake_processing", None)

                return redirect(url_for("exito", intake_id=intake_id))

            except OpenEMRServiceError as e:
                create_kiosk_event(
                    event_type="new_patient_openemr_create_error",
                    flow_type="nuevo",
                    status="error",
                    message="Error al crear paciente nuevo o encounter inicial en OpenEMR después de confirmación final",
                    metadata={
                        "error": str(e),
                        "ci_documento_present": bool(data.get("ci_documento")),
                        "telefono_present": bool(data.get("telefono")),
                        "sexo_present": bool(data.get("sexo")),
                    },
                )

                session.pop("pending_intake_processing", None)

                return render_template(
                    "confirmar.html",
                    data=data,
                    errors=[
                        "No se pudo completar el registro del paciente en OpenEMR. Avise a recepción."
                    ],
                )

        return render_template("confirmar.html", data=data, errors=[])

    @app.route("/confirmar-antiguo", methods=["GET", "POST"])
    def confirmar_antiguo():
        data = session.get("pending_existing")

        if not data:
            return redirect(url_for("index"))

        if request.method == "POST":
            if session.get("pending_existing_processing"):
                create_kiosk_event(
                    event_type="existing_patient_duplicate_submit_blocked",
                    flow_type="antiguo",
                    status="blocked",
                    message="Intento duplicado de confirmar paciente antiguo bloqueado",
                    metadata={
                        "openemr_pid_present": bool(data.get("openemr_pid")),
                        "openemr_uuid_present": bool(data.get("openemr_uuid")),
                        "openemr_pubpid_present": bool(data.get("openemr_pubpid")),
                    },
                )

                return redirect(url_for("exito"))

            session["pending_existing_processing"] = True
            patient_uuid = data.get("openemr_uuid")
            motivo_consulta = data.get("motivo_consulta")

            try:
                openemr = OpenEMRService()
                encounter_payload = openemr.build_kiosk_encounter_payload(
                    motivo_consulta=motivo_consulta,
                    professional_area=data.get("profesional_area"),
                )

                result = openemr.create_encounter_for_patient(
                    patient_uuid=patient_uuid,
                    encounter_data=encounter_payload,
                )

                result_data = result.get("data", {}) if isinstance(result, dict) else {}
                encounter_id = result_data.get("encounter")
                encounter_uuid = result_data.get("uuid")

                create_kiosk_event(
                    event_type="existing_patient_encounter_created",
                    flow_type="antiguo",
                    status="ok",
                    message="Encounter creado en OpenEMR para paciente antiguo confirmado",
                    metadata={
                        "openemr_pid_present": bool(data.get("openemr_pid")),
                        "openemr_uuid_present": bool(patient_uuid),
                        "openemr_pubpid_present": bool(data.get("openemr_pubpid")),
                        "encounter_id": encounter_id,
                        "encounter_uuid_present": bool(encounter_uuid),
                        "profesional_area": data.get("profesional_area"),
                        "motivo_consulta_present": bool(motivo_consulta),
                    },
                )

                session.pop("pending_existing", None)
                session.pop("pending_existing_processing", None)

                return redirect(url_for("exito"))

            except OpenEMRServiceError as e:
                create_kiosk_event(
                    event_type="existing_patient_encounter_error",
                    flow_type="antiguo",
                    status="error",
                    message="Error al crear encounter en OpenEMR para paciente antiguo",
                    metadata={
                        "openemr_pid_present": bool(data.get("openemr_pid")),
                        "openemr_uuid_present": bool(patient_uuid),
                        "openemr_pubpid_present": bool(data.get("openemr_pubpid")),
                        "error": str(e),
                    },
                )

                session.pop("pending_existing_processing", None)

                return render_template(
                    "confirmar_antiguo.html",
                    data=data,
                    errors=[
                        "No se pudo crear el encuentro en OpenEMR. Avise a recepción."
                    ],
                )

        return render_template("confirmar_antiguo.html", data=data, errors=[])

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

    @app.route("/admin/openemr/patients/search")
    @admin_auth_required
    def admin_openemr_patient_search():
        query = request.args.get("q", "")
        phone = request.args.get("phone", "")
        limit = request.args.get("limit", 10)

        if not query and not phone:
            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": "Debe enviar al menos q o phone.",
                "example": "/admin/openemr/patients/search?q=juan",
            }), 400

        try:
            openemr = OpenEMRService()
            result = openemr.search_patients(
                query=query,
                phone=phone,
                limit=limit,
            )

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

    @app.route("/admin/openemr/patients/<path:patient_uuid>/encounters")
    @admin_auth_required
    def admin_openemr_patient_encounters(patient_uuid):
        try:
            openemr = OpenEMRService()
            result = openemr.get_patient_encounters(patient_uuid)

            data = result.get("data", [])

            return jsonify({
                "status": "ok",
                "service": "openemr",
                "result": {
                    "patient_uuid": patient_uuid,
                    "encounters_count": len(data) if isinstance(data, list) else None,
                    "raw": result,
                },
            })

        except OpenEMRServiceError as e:
            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": str(e),
            }), 500

    @app.route(
        "/admin/openemr/patients/<path:patient_uuid>/encounter/test",
        methods=["POST"],
    )
    @admin_auth_required
    def admin_openemr_create_encounter_test(patient_uuid):
        encounter_data = request.get_json(silent=True) or {}

        if request.args.get("confirm") != "CREATE":
            return jsonify({
                "status": "dry_run",
                "service": "openemr",
                "message": "No se creó ningún encounter. Para ejecutar, agregue ?confirm=CREATE.",
                "patient_uuid": patient_uuid,
                "payload_received": encounter_data,
            })

        try:
            openemr = OpenEMRService()
            result = openemr.create_encounter_for_patient(
                patient_uuid=patient_uuid,
                encounter_data=encounter_data,
            )

            create_kiosk_event(
                event_type="admin_test_encounter_created",
                flow_type="antiguo",
                status="ok",
                message="Encounter creado desde ruta admin de prueba",
                metadata={
                    "patient_uuid_present": bool(patient_uuid),
                    "response_keys": list(result.keys()) if isinstance(result, dict) else [],
                },
            )

            return jsonify({
                "status": "ok",
                "service": "openemr",
                "message": "Encounter creado en OpenEMR.",
                "result": result,
            })

        except OpenEMRServiceError as e:
            create_kiosk_event(
                event_type="admin_test_encounter_error",
                flow_type="antiguo",
                status="error",
                message="Error al crear encounter desde ruta admin de prueba",
                metadata={
                    "patient_uuid_present": bool(patient_uuid),
                    "error": str(e),
                },
            )

            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": str(e),
            }), 500

    @app.route("/admin/openemr/patient/test", methods=["POST"])
    @admin_auth_required
    def admin_openemr_create_patient_test():
        raw_data = request.get_json(silent=True) or {}

        try:
            openemr = OpenEMRService()
            patient_payload = openemr.build_kiosk_patient_payload(raw_data)

        except OpenEMRServiceError as e:
            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": str(e),
            }), 400

        if request.args.get("confirm") != "CREATE":
            return jsonify({
                "status": "dry_run",
                "service": "openemr",
                "message": "No se creó ningún paciente. Para ejecutar, agregue ?confirm=CREATE.",
                "payload_received": raw_data,
                "payload_to_openemr": patient_payload,
            })

        try:
            result = openemr.create_patient(patient_payload)

            create_kiosk_event(
                event_type="admin_test_patient_created",
                flow_type="nuevo",
                status="ok",
                message="Paciente creado desde ruta admin de prueba",
                metadata={
                    "response_keys": list(result.keys()) if isinstance(result, dict) else [],
                },
            )

            return jsonify({
                "status": "ok",
                "service": "openemr",
                "message": "Paciente creado en OpenEMR.",
                "result": result,
            })

        except OpenEMRServiceError as e:
            create_kiosk_event(
                event_type="admin_test_patient_error",
                flow_type="nuevo",
                status="error",
                message="Error al crear paciente desde ruta admin de prueba",
                metadata={
                    "error": str(e),
                },
            )

            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": str(e),
            }), 500

    @app.route("/admin/gemini/consultation-reason/test", methods=["POST"])
    @admin_auth_required
    def admin_gemini_consultation_reason_test():
        payload = request.get_json(silent=True) or {}
        user_text = str(payload.get("text") or "").strip()

        if not user_text:
            return jsonify({
                "status": "error",
                "service": "gemini",
                "message": "Debe enviar el campo text.",
                "example": {
                    "text": "vengo a revisar mis resultados"
                },
            }), 400

        try:
            gemini = GeminiService()
            result = gemini.classify_consultation_reason(user_text)

            create_kiosk_event(
                event_type="gemini_consultation_reason_test",
                flow_type="admin",
                status=result.get("status", "unknown"),
                message="Prueba admin de clasificación de motivo de consulta con Gemini",
                metadata={
                    "text_present": bool(user_text),
                    "reason": result.get("reason"),
                    "confidence": result.get("confidence"),
                    "fallback_used": bool(result.get("fallback_used")),
                    "error_present": bool(result.get("error")),
                },
            )

            return jsonify({
                "status": "ok",
                "service": "gemini",
                "result": result,
            })

        except Exception as e:
            create_kiosk_event(
                event_type="gemini_consultation_reason_error",
                flow_type="admin",
                status="error",
                message="Error en prueba admin de clasificación con Gemini",
                metadata={
                    "text_present": bool(user_text),
                    "error": str(e),
                },
            )

            return jsonify({
                "status": "error",
                "service": "gemini",
                "message": str(e),
            }), 500

    @app.route("/admin/openemr/token/status")
    @admin_auth_required
    def admin_openemr_token_status():
        return jsonify({
            "status": "ok",
            "service": "openemr",
            "token": public_token_status(),
        })

    @app.route("/admin/openemr/token/save-manual", methods=["POST"])
    @admin_auth_required
    def admin_openemr_token_save_manual():
        payload = request.get_json(silent=True) or {}

        access_token = str(payload.get("access_token") or "").strip()
        refresh_token = str(payload.get("refresh_token") or "").strip()
        expires_in = payload.get("expires_in")
        scope = str(payload.get("scope") or "").strip()

        if access_token.startswith("Bearer "):
            access_token = access_token.replace("Bearer ", "", 1).strip()

        if not access_token and not refresh_token:
            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": "Debe enviar access_token o refresh_token.",
            }), 400

        save_openemr_tokens({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "expires_at": calculate_expires_at(expires_in),
            "scope": scope,
            "source": "manual_admin",
        })

        create_kiosk_event(
            event_type="openemr_token_saved_manual",
            flow_type="admin",
            status="ok",
            message="Tokens de OpenEMR guardados manualmente desde panel admin",
            metadata={
                "access_token_present": bool(access_token),
                "refresh_token_present": bool(refresh_token),
                "expires_in_present": bool(expires_in),
                "scope_present": bool(scope),
            },
        )

        return jsonify({
            "status": "ok",
            "service": "openemr",
            "message": "Tokens guardados.",
            "token": public_token_status(),
        })

    @app.route("/admin/openemr/oauth/start")
    @admin_auth_required
    def admin_openemr_oauth_start():
        state = secrets.token_urlsafe(32)
        session["openemr_oauth_state"] = state

        try:
            openemr = OpenEMRService()
            authorization_url = openemr.build_authorization_url(
                redirect_uri=Config.OPENEMR_OAUTH_REDIRECT_URI,
                state=state,
                scope=Config.OPENEMR_OAUTH_SCOPES,
            )

            create_kiosk_event(
                event_type="openemr_oauth_start",
                flow_type="admin",
                status="ok",
                message="Inicio de flujo OAuth OpenEMR desde panel admin",
                metadata={
                    "redirect_uri_present": bool(Config.OPENEMR_OAUTH_REDIRECT_URI),
                    "scopes_present": bool(Config.OPENEMR_OAUTH_SCOPES),
                },
            )

            return redirect(authorization_url)

        except OpenEMRServiceError as e:
            create_kiosk_event(
                event_type="openemr_oauth_start_error",
                flow_type="admin",
                status="error",
                message="Error al iniciar OAuth OpenEMR",
                metadata={"error": str(e)},
            )

            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": str(e),
            }), 500

    @app.route("/admin/openemr/oauth/callback")
    def admin_openemr_oauth_callback():
        error = request.args.get("error")
        error_description = request.args.get("error_description")

        if error:
            create_kiosk_event(
                event_type="openemr_oauth_callback_error",
                flow_type="admin",
                status="error",
                message="OpenEMR devolvió error en callback OAuth",
                metadata={
                    "error": error,
                    "error_description": error_description,
                },
            )

            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": error,
                "description": error_description,
            }), 400

        code = request.args.get("code")
        state = request.args.get("state")
        expected_state = session.pop("openemr_oauth_state", None)

        if not expected_state or state != expected_state:
            create_kiosk_event(
                event_type="openemr_oauth_state_error",
                flow_type="admin",
                status="error",
                message="OAuth state inválido o ausente",
                metadata={
                    "state_present": bool(state),
                    "expected_state_present": bool(expected_state),
                },
            )

            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": "OAuth state inválido o ausente.",
            }), 400

        if not code:
            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": "OpenEMR no devolvió authorization code.",
            }), 400

        try:
            openemr = OpenEMRService()
            exchange_result = openemr.exchange_authorization_code(
                code=code,
                redirect_uri=Config.OPENEMR_OAUTH_REDIRECT_URI,
            )

            create_kiosk_event(
                event_type="openemr_oauth_callback_success",
                flow_type="admin",
                status="ok",
                message="OAuth OpenEMR completado y tokens guardados",
                metadata={
                    "access_token_present": bool(exchange_result.get("access_token_present")),
                    "refresh_token_present": bool(exchange_result.get("refresh_token_present")),
                    "expires_in_present": bool(exchange_result.get("expires_in")),
                    "scope_present": bool(exchange_result.get("scope")),
                },
            )

            return jsonify({
                "status": "ok",
                "service": "openemr",
                "message": "OAuth completado. Tokens guardados.",
                "exchange": exchange_result,
                "token": public_token_status(),
            })

        except OpenEMRServiceError as e:
            create_kiosk_event(
                event_type="openemr_oauth_callback_exchange_error",
                flow_type="admin",
                status="error",
                message="Error al intercambiar authorization code por tokens",
                metadata={"error": str(e)},
            )

            return jsonify({
                "status": "error",
                "service": "openemr",
                "message": str(e),
            }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)