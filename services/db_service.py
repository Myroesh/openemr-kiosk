import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from config import Config


QUEUE_STATUSES = {
    "pending",
    "in_progress",
    "completed",
    "cancelled",
    "no_show",
    "error",
}


def get_db_path():
    db_path = Path(Config.KIOSK_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_intake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                flow_type TEXT NOT NULL,
                nombres TEXT,
                apellidos TEXT,
                fecha_nacimiento TEXT,
                ci_documento TEXT,
                telefono TEXT,
                direccion TEXT,
                motivo_consulta TEXT,
                profesional_area TEXT,
                es_menor INTEGER DEFAULT 0,
                padre_nombre TEXT,
                padre_ci TEXT,
                padre_telefono TEXT,
                madre_nombre TEXT,
                madre_ci TEXT,
                madre_telefono TEXT,
                status TEXT NOT NULL DEFAULT 'local_saved',
                openemr_patient_id TEXT,
                openemr_encounter_id TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kiosk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                flow_type TEXT,
                status TEXT NOT NULL,
                message TEXT,
                intake_id INTEGER,
                metadata_json TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kiosk_submission_locks (
                token TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                flow_type TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                queue_date TEXT NOT NULL,
                openemr_pid TEXT,
                openemr_puuid TEXT,
                openemr_encounter_id TEXT,
                patient_name TEXT,
                doctor_id TEXT,
                doctor_name TEXT,
                visit_reason TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                started_at TEXT,
                finished_at TEXT,
                metadata_json TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_patient_queue_encounter_id
            ON patient_queue(openemr_encounter_id)
            WHERE openemr_encounter_id IS NOT NULL
              AND openemr_encounter_id != ''
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_patient_queue_date_doctor_status
            ON patient_queue(queue_date, doctor_id, status, created_at)
            """
        )

        conn.commit()


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _today_iso():
    return date.today().isoformat()


def _validate_queue_status(status):
    if status not in QUEUE_STATUSES:
        raise ValueError(f"Estado de cola no permitido: {status}")


def _json_dumps(data):
    return json.dumps(data or {}, ensure_ascii=False)


def create_kiosk_event(
    event_type,
    status,
    message=None,
    flow_type=None,
    intake_id=None,
    metadata=None,
):
    metadata_json = _json_dumps(metadata)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO kiosk_events (
                created_at,
                event_type,
                flow_type,
                status,
                message,
                intake_id,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                event_type,
                flow_type,
                status,
                message,
                intake_id,
                metadata_json,
            ),
        )

        conn.commit()
        return cursor.lastrowid


def create_patient_intake(data):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO patient_intake (
                created_at,
                flow_type,
                nombres,
                apellidos,
                fecha_nacimiento,
                ci_documento,
                telefono,
                direccion,
                motivo_consulta,
                profesional_area,
                es_menor,
                padre_nombre,
                padre_ci,
                padre_telefono,
                madre_nombre,
                madre_ci,
                madre_telefono,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                data.get("flow_type", "nuevo"),
                data.get("nombres"),
                data.get("apellidos"),
                data.get("fecha_nacimiento"),
                data.get("ci_documento"),
                data.get("telefono"),
                data.get("direccion"),
                data.get("motivo_consulta"),
                data.get("profesional_area"),
                int(data.get("es_menor", 0)),
                data.get("padre_nombre"),
                data.get("padre_ci"),
                data.get("padre_telefono"),
                data.get("madre_nombre"),
                data.get("madre_ci"),
                data.get("madre_telefono"),
                "local_saved",
            ),
        )

        intake_id = cursor.lastrowid
        conn.commit()

    create_kiosk_event(
        event_type="patient_intake_created",
        flow_type="nuevo",
        status="ok",
        message="Registro local de paciente nuevo guardado",
        intake_id=intake_id,
        metadata={
            "ci_documento_present": bool(data.get("ci_documento")),
            "telefono_present": bool(data.get("telefono")),
            "es_menor": bool(data.get("es_menor")),
            "padre_present": bool(data.get("padre_nombre")),
            "madre_present": bool(data.get("madre_nombre")),
        },
    )

    return intake_id


def create_patient_queue_entry(
    *,
    openemr_pid=None,
    openemr_puuid=None,
    openemr_encounter_id=None,
    patient_name=None,
    doctor_id=None,
    doctor_name=None,
    visit_reason=None,
    status="pending",
    queue_date=None,
    metadata=None,
):
    """
    Registra un paciente/encounter en la cola operativa del portal médico.

    Si `openemr_encounter_id` ya existe, devuelve el registro existente para
    evitar duplicados por reintentos o doble submit.
    """

    _validate_queue_status(status)

    normalized_encounter_id = str(openemr_encounter_id or "").strip()
    normalized_queue_date = queue_date or _today_iso()
    metadata_json = _json_dumps(metadata)

    with get_connection() as conn:
        if normalized_encounter_id:
            existing = conn.execute(
                """
                SELECT id
                FROM patient_queue
                WHERE openemr_encounter_id = ?
                LIMIT 1
                """,
                (normalized_encounter_id,),
            ).fetchone()

            if existing:
                return int(existing["id"])

        cursor = conn.execute(
            """
            INSERT INTO patient_queue (
                created_at,
                queue_date,
                openemr_pid,
                openemr_puuid,
                openemr_encounter_id,
                patient_name,
                doctor_id,
                doctor_name,
                visit_reason,
                status,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                normalized_queue_date,
                openemr_pid,
                openemr_puuid,
                normalized_encounter_id or None,
                patient_name,
                doctor_id,
                doctor_name,
                visit_reason,
                status,
                metadata_json,
            ),
        )

        queue_id = cursor.lastrowid
        conn.commit()

    return queue_id


def list_patient_queue_by_date(queue_date=None, doctor_id=None):
    normalized_queue_date = queue_date or _today_iso()

    query = """
        SELECT *
        FROM patient_queue
        WHERE queue_date = ?
    """
    params = [normalized_queue_date]

    if doctor_id:
        query += " AND doctor_id = ?"
        params.append(doctor_id)

    query += " ORDER BY created_at ASC, id ASC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]

def list_completed_patient_queue_by_date_range(
    date_from=None,
    date_to=None,
    doctor_name=None,
):
    normalized_date_from = date_from or _today_iso()
    normalized_date_to = date_to or normalized_date_from
    normalized_doctor_name = str(doctor_name or "").strip()

    query = """
        SELECT *
        FROM patient_queue
        WHERE queue_date >= ?
          AND queue_date <= ?
          AND status = 'completed'
    """
    params = [normalized_date_from, normalized_date_to]

    if normalized_doctor_name:
        query += " AND doctor_name = ?"
        params.append(normalized_doctor_name)

    query += " ORDER BY doctor_name ASC, started_at ASC, finished_at ASC, id ASC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]

def list_patient_queue_by_status(status, queue_date=None, doctor_id=None):
    _validate_queue_status(status)
    normalized_queue_date = queue_date or _today_iso()

    query = """
        SELECT *
        FROM patient_queue
        WHERE queue_date = ?
          AND status = ?
    """
    params = [normalized_queue_date, status]

    if doctor_id:
        query += " AND doctor_id = ?"
        params.append(doctor_id)

    query += " ORDER BY created_at ASC, id ASC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_next_patient_for_doctor(queue_date=None, doctor_id=None):
    pending = list_patient_queue_by_status(
        "pending",
        queue_date=queue_date,
        doctor_id=doctor_id,
    )

    return pending[0] if pending else None


def update_patient_queue_status(queue_id, status):
    _validate_queue_status(status)

    started_at = None
    finished_at = None

    if status == "in_progress":
        started_at = _now_iso()
    elif status in {"completed", "cancelled", "no_show"}:
        finished_at = _now_iso()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM patient_queue
            WHERE id = ?
            """,
            (queue_id,),
        ).fetchone()

        if not row:
            return None

        current_started_at = row["started_at"]
        current_finished_at = row["finished_at"]

        conn.execute(
            """
            UPDATE patient_queue
            SET status = ?,
                started_at = COALESCE(?, started_at),
                finished_at = COALESCE(?, finished_at)
            WHERE id = ?
            """,
            (
                status,
                started_at or current_started_at,
                finished_at or current_finished_at,
                queue_id,
            ),
        )
        conn.commit()

    create_kiosk_event(
        event_type="patient_queue_status_updated",
        flow_type="doctor_portal",
        status="ok",
        message="Estado de cola de paciente actualizado",
        metadata={
            "queue_id": queue_id,
            "new_status": status,
        },
    )

    with get_connection() as conn:
        updated_row = conn.execute(
            """
            SELECT *
            FROM patient_queue
            WHERE id = ?
            """,
            (queue_id,),
        ).fetchone()

    return dict(updated_row) if updated_row else None


def list_recent_events(limit=100):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM kiosk_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def list_recent_intakes(limit=100):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM patient_intake
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def claim_submission_token(token, flow_type):
    """
    Reclama un token de confirmación de forma atómica.

    Devuelve True si este proceso logró reclamar el token.
    Devuelve False si el token ya había sido usado.
    """

    if not token:
        return False

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO kiosk_submission_locks (
                    token,
                    created_at,
                    flow_type,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    token,
                    _now_iso(),
                    flow_type,
                    "processing",
                ),
            )
            conn.commit()
            return True

    except sqlite3.IntegrityError:
        return False