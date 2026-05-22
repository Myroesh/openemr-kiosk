import json
import sqlite3
from datetime import datetime
from pathlib import Path

from config import Config


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

        conn.commit()


def create_kiosk_event(
    event_type,
    status,
    message=None,
    flow_type=None,
    intake_id=None,
    metadata=None,
):
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

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
                datetime.now().isoformat(timespec="seconds"),
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
                datetime.now().isoformat(timespec="seconds"),
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
                    datetime.now().isoformat(timespec="seconds"),
                    flow_type,
                    "processing",
                ),
            )
            conn.commit()
            return True

    except sqlite3.IntegrityError:
        return False