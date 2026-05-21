import re
from datetime import date
from urllib.parse import quote

import requests

from config import Config
from services.token_store import (
    calculate_expires_at,
    get_access_token,
    get_refresh_token,
    is_access_token_expired,
    public_token_status,
    save_openemr_tokens,
)


class OpenEMRServiceError(Exception):
    """Error controlado para fallos de comunicación con OpenEMR."""


class OpenEMRConfigError(OpenEMRServiceError):
    """Error de configuración local del servicio OpenEMR."""


class OpenEMRService:
    """
    Servicio mínimo para consumir la Standard API de OpenEMR desde Flask.

    Bloque actual:
    - Obtener/usar Bearer token.
    - Probar lectura segura de pacientes.
    - Buscar pacientes de forma segura.
    - Leer encounters de pacientes.
    - Crear encounters para pacientes confirmados.
    - No crear pacientes todavía.
    """

    def __init__(self):
        self.base_url = self._clean_base_url(Config.OPENEMR_BASE_URL)
        self.site = Config.OPENEMR_SITE or "default"
        self.client_id = self._clean_optional_secret(Config.OPENEMR_CLIENT_ID)
        self.client_secret = self._clean_optional_secret(Config.OPENEMR_CLIENT_SECRET)
        stored_access_token = get_access_token()
        stored_refresh_token = get_refresh_token()

        self.access_token = self._clean_optional_secret(
            stored_access_token or Config.OPENEMR_ACCESS_TOKEN
        )
        self.refresh_token = self._clean_optional_secret(
            stored_refresh_token or Config.OPENEMR_REFRESH_TOKEN
        )
        self.verify_ssl = Config.OPENEMR_VERIFY_SSL

        self.session = requests.Session()

        if not self.base_url:
            raise OpenEMRConfigError("OPENEMR_BASE_URL no está configurado.")

    @staticmethod
    def _clean_base_url(value):
        if not value:
            return ""

        return str(value).strip().rstrip("/")

    @staticmethod
    def _clean_optional_secret(value):
        if not value:
            return ""

        value = str(value).strip()

        placeholders = {
            "TU_CLIENT_ID_REAL",
            "TU_CLIENT_SECRET_REAL",
            "TU_ACCESS_TOKEN_REAL",
            "TU_REFRESH_TOKEN_REAL",
            "PEGAR_TOKEN_DE_SWAGGER",
            "TOKEN_TEMPORAL_COPIADO_DE_SWAGGER",
        }

        if value in placeholders:
            return ""

        return value

    @staticmethod
    def _normalize_search_text(value):
        if value is None:
            return ""

        value = str(value).lower().strip()
        value = re.sub(r"\s+", " ", value)
        return value

    @staticmethod
    def _digits_only(value):
        if value is None:
            return ""

        return re.sub(r"\D+", "", str(value))

    @staticmethod
    def _first_existing(patient, keys):
        for key in keys:
            value = patient.get(key)
            if value not in (None, ""):
                return value

        return ""

    @property
    def api_base_url(self):
        return f"{self.base_url}/apis/{self.site}/api"

    @property
    def token_url(self):
        return f"{self.base_url}/oauth2/{self.site}/token"

    def _get_access_token(self):
        """
        Devuelve un access token usable.

        Prioridad:
        1. Token guardado en data/openemr_tokens.json.
        2. OPENEMR_ACCESS_TOKEN desde .env.
        3. Renovar usando refresh_token si existe.

        El .env queda como fallback de desarrollo.
        """

        stored_access_token = get_access_token()
        stored_refresh_token = get_refresh_token()

        if stored_access_token:
            self.access_token = self._clean_optional_secret(stored_access_token)

        if stored_refresh_token:
            self.refresh_token = self._clean_optional_secret(stored_refresh_token)

        if self.refresh_token and is_access_token_expired():
            return self._refresh_access_token()

        if self.access_token:
            return self.access_token

        if self.refresh_token:
            return self._refresh_access_token()

        raise OpenEMRConfigError(
            "No hay access_token ni refresh_token configurado para OpenEMR."
        )

    def _refresh_access_token(self):
        if not self.client_id:
            raise OpenEMRConfigError("OPENEMR_CLIENT_ID no está configurado.")

        if not self.client_secret:
            raise OpenEMRConfigError("OPENEMR_CLIENT_SECRET no está configurado.")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = self.session.post(
                self.token_url,
                data=data,
                timeout=20,
                verify=self.verify_ssl,
            )
        except requests.RequestException as exc:
            raise OpenEMRServiceError(
                f"No se pudo conectar al token endpoint de OpenEMR: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise OpenEMRServiceError(
                f"OpenEMR rechazó la renovación del token. "
                f"HTTP {response.status_code}: {response.text[:300]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise OpenEMRServiceError(
                "OpenEMR respondió al token endpoint, pero no devolvió JSON válido."
            ) from exc

        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token") or self.refresh_token

        if not access_token:
            raise OpenEMRServiceError(
                "OpenEMR no devolvió access_token al renovar el token."
            )

        self.access_token = access_token
        self.refresh_token = refresh_token

        save_openemr_tokens({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": payload.get("expires_in"),
            "expires_at": calculate_expires_at(payload.get("expires_in")),
            "scope": payload.get("scope"),
            "token_type": payload.get("token_type"),
            "source": "refresh_token",
        })

        return self.access_token

    def _request(self, method, path, params=None, json=None, retry_on_unauthorized=True):
        access_token = self._get_access_token()

        url = f"{self.api_base_url}{path}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=20,
                verify=self.verify_ssl,
            )
        except requests.RequestException as exc:
            raise OpenEMRServiceError(
                f"No se pudo conectar a OpenEMR API: {exc}"
            ) from exc

        if (
            response.status_code == 401
            and retry_on_unauthorized
            and self.refresh_token
        ):
            self.access_token = ""
            self._refresh_access_token()
            return self._request(
                method=method,
                path=path,
                params=params,
                json=json,
                retry_on_unauthorized=False,
            )

        if response.status_code >= 400:
            raise OpenEMRServiceError(
                f"OpenEMR API respondió con error. "
                f"HTTP {response.status_code}: {response.text[:300]}"
            )

        if not response.text:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise OpenEMRServiceError(
                "OpenEMR API respondió, pero no devolvió JSON válido."
            ) from exc

    def get_patients(self):
        """
        Lectura segura inicial.

        Endpoint confirmado:
        GET /apis/default/api/patient
        """

        return self._request("GET", "/patient")

    def _patient_search_blob(self, patient):
        fields = [
            "fname",
            "mname",
            "lname",
            "name",
            "pubpid",
            "pid",
            "uuid",
            "puuid",
            "phone_cell",
            "phone_contact",
            "phone_home",
            "phone_biz",
            "phone",
            "email",
        ]

        parts = []

        for field in fields:
            value = patient.get(field)
            if value not in (None, ""):
                parts.append(str(value))

        return self._normalize_search_text(" ".join(parts))

    def _patient_phone_blob(self, patient):
        fields = [
            "phone_cell",
            "phone_contact",
            "phone_home",
            "phone_biz",
            "phone",
        ]

        parts = []

        for field in fields:
            value = patient.get(field)
            if value not in (None, ""):
                parts.append(str(value))

        return self._digits_only(" ".join(parts))

    def _public_patient_summary(self, patient):
        """
        Resumen limitado para pruebas internas.

        No devuelve el objeto completo de OpenEMR para evitar exponer más datos
        de los necesarios en la ruta de diagnóstico.
        """

        return {
            "pid": self._first_existing(patient, ["pid", "id"]),
            "uuid": self._first_existing(patient, ["uuid", "puuid"]),
            "pubpid": self._first_existing(patient, ["pubpid"]),
            "fname": self._first_existing(patient, ["fname"]),
            "lname": self._first_existing(patient, ["lname"]),
            "DOB": self._first_existing(patient, ["DOB", "dob", "date_of_birth"]),
            "phone_cell": self._first_existing(patient, ["phone_cell"]),
            "phone_contact": self._first_existing(patient, ["phone_contact"]),
        }

    def search_patients(self, query=None, phone=None, limit=10):
        """
        Búsqueda segura inicial de pacientes.

        Por ahora no inventamos filtros remotos de OpenEMR.
        Se usa GET /patient confirmado y se filtra localmente en Flask.

        Esto es suficiente para el MVP actual porque la base tiene pocos pacientes.
        Luego, si confirmamos filtros reales en Swagger/OpenEMR, se puede optimizar.
        """

        payload = self.get_patients()
        patients = payload.get("data", [])

        if not isinstance(patients, list):
            return {
                "status": "ok",
                "source": "openemr",
                "filter_mode": "local",
                "total_loaded": 0,
                "matched_count": 0,
                "patients": [],
            }

        query = self._normalize_search_text(query)
        phone = self._digits_only(phone)

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10

        limit = max(1, min(limit, 25))

        matches = []

        for patient in patients:
            text_blob = self._patient_search_blob(patient)
            phone_blob = self._patient_phone_blob(patient)

            query_match = True
            phone_match = True

            if query:
                query_terms = query.split(" ")
                query_match = all(term in text_blob for term in query_terms)

            if phone:
                phone_match = phone in phone_blob

            if query_match and phone_match:
                matches.append(self._public_patient_summary(patient))

            if len(matches) >= limit:
                break

        return {
            "status": "ok",
            "source": "openemr",
            "filter_mode": "local",
            "total_loaded": len(patients),
            "matched_count": len(matches),
            "patients": matches,
        }

    def build_kiosk_encounter_payload(self, motivo_consulta, encounter_date=None):
        """
        Construye el payload validado para crear encounter desde el kiosko.

        Basado en el payload confirmado desde Swagger y probado exitosamente
        contra OpenEMR.
        """

        reason = str(motivo_consulta or "").strip()

        if not reason:
            raise OpenEMRConfigError("motivo_consulta es obligatorio para crear encounter.")

        encounter_date = encounter_date or date.today().isoformat()

        return {
            "date": encounter_date,
            "onset_date": "",
            "reason": reason,
            "facility": Config.OPENEMR_DEFAULT_FACILITY,
            "pc_catid": Config.OPENEMR_DEFAULT_PC_CATID,
            "facility_id": Config.OPENEMR_DEFAULT_FACILITY_ID,
            "billing_facility": Config.OPENEMR_DEFAULT_BILLING_FACILITY,
            "sensitivity": Config.OPENEMR_DEFAULT_SENSITIVITY,
            "referral_source": "",
            "pos_code": Config.OPENEMR_DEFAULT_POS_CODE,
            "external_id": "",
            "provider_id": Config.OPENEMR_DEFAULT_PROVIDER_ID,
            "class_code": Config.OPENEMR_DEFAULT_CLASS_CODE,
        }

    def get_patient_encounters(self, patient_uuid):
        """
        Lectura segura de encounters de un paciente.

        Endpoint confirmado:
        GET /apis/default/api/patient/{puuid}/encounter
        """

        patient_uuid = self._clean_optional_secret(patient_uuid)

        if not patient_uuid:
            raise OpenEMRConfigError("patient_uuid/puuid es obligatorio.")

        safe_patient_uuid = quote(patient_uuid, safe="")

        return self._request(
            "GET",
            f"/patient/{safe_patient_uuid}/encounter",
        )

    def create_encounter_for_patient(self, patient_uuid, encounter_data):
        """
        Crea encounter para un paciente existente.

        Importante:
        - Este método usa el payload confirmado por Swagger/OpenEMR.
        - Usar con paciente previamente confirmado.
        """

        patient_uuid = self._clean_optional_secret(patient_uuid)

        if not patient_uuid:
            raise OpenEMRConfigError("patient_uuid/puuid es obligatorio.")

        if not isinstance(encounter_data, dict):
            raise OpenEMRConfigError("encounter_data debe ser un objeto JSON.")

        if not encounter_data:
            raise OpenEMRConfigError("encounter_data no puede estar vacío.")

        safe_patient_uuid = quote(patient_uuid, safe="")

        return self._request(
            "POST",
            f"/patient/{safe_patient_uuid}/encounter",
            json=encounter_data,
        )

    def build_kiosk_patient_payload(self, patient_data):
        """
        Construye el payload para crear paciente en OpenEMR.

        Basado en el Example Value confirmado desde Swagger para:
        POST /apis/default/api/patient
        """

        if not isinstance(patient_data, dict):
            raise OpenEMRConfigError("patient_data debe ser un objeto.")

        nombres = str(patient_data.get("nombres") or "").strip()
        apellidos = str(patient_data.get("apellidos") or "").strip()
        fecha_nacimiento = str(patient_data.get("fecha_nacimiento") or "").strip()
        telefono = str(patient_data.get("telefono") or "").strip()
        direccion = str(patient_data.get("direccion") or "").strip()
        sexo = str(patient_data.get("sexo") or "").strip()

        if not nombres:
            raise OpenEMRConfigError("nombres es obligatorio para crear paciente.")

        if not apellidos:
            raise OpenEMRConfigError("apellidos es obligatorio para crear paciente.")

        if not fecha_nacimiento:
            raise OpenEMRConfigError("fecha_nacimiento es obligatoria para crear paciente.")

        if not telefono:
            raise OpenEMRConfigError("telefono es obligatorio para crear paciente.")
        
        if not sexo:
            raise OpenEMRConfigError("sexo es obligatorio para crear paciente.")
            
        return {
            "title": "",
            "fname": nombres,
            "mname": "",
            "lname": apellidos,
            "street": direccion,
            "postal_code": "",
            "city": "",
            "state": "",
            "country_code": "BO",
            "phone_contact": telefono,
            "DOB": fecha_nacimiento,
            "sex": sexo,
            "race": "",
            "ethnicity": "",
        }

    def create_patient(self, patient_data):
        """
        Crea paciente en OpenEMR.

        Importante:
        - Usar primero mediante ruta admin protegida.
        - No llamar desde /confirmar hasta validar con paciente controlado.
        """

        if not isinstance(patient_data, dict):
            raise OpenEMRConfigError("patient_data debe ser un objeto JSON.")

        if not patient_data:
            raise OpenEMRConfigError("patient_data no puede estar vacío.")

        return self._request(
            "POST",
            "/patient",
            json=patient_data,
        )

    def token_status(self):
        return public_token_status()

    def health_check(self):
        """
        Prueba segura para verificar conectividad sin exponer datos personales.

        Devuelve solo conteo y estado, no devuelve registros de pacientes.
        """

        payload = self.get_patients()

        data = payload.get("data", [])

        return {
            "status": "ok",
            "api_base_url": self.api_base_url,
            "patients_count": len(data) if isinstance(data, list) else None,
        }