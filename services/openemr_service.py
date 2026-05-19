import requests

from config import Config


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
    - No crear pacientes.
    - No crear encounters.
    """

    def __init__(self):
        self.base_url = self._clean_base_url(Config.OPENEMR_BASE_URL)
        self.site = Config.OPENEMR_SITE or "default"
        self.client_id = Config.OPENEMR_CLIENT_ID
        self.client_secret = Config.OPENEMR_CLIENT_SECRET
        self.access_token = Config.OPENEMR_ACCESS_TOKEN
        self.refresh_token = Config.OPENEMR_REFRESH_TOKEN
        self.verify_ssl = Config.OPENEMR_VERIFY_SSL

        self.session = requests.Session()

        if not self.base_url:
            raise OpenEMRConfigError("OPENEMR_BASE_URL no está configurado.")

    @staticmethod
    def _clean_base_url(value):
        if not value:
            return ""

        return value.rstrip("/")

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
        1. OPENEMR_ACCESS_TOKEN si está definido.
        2. Renovar usando OPENEMR_REFRESH_TOKEN si está definido.

        No usamos Password Grant porque en la instalación confirmada está apagado.
        """

        if self.access_token:
            return self.access_token

        if self.refresh_token:
            return self._refresh_access_token()

        raise OpenEMRConfigError(
            "No hay OPENEMR_ACCESS_TOKEN ni OPENEMR_REFRESH_TOKEN configurado en .env."
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

        if not access_token:
            raise OpenEMRServiceError(
                "OpenEMR no devolvió access_token al renovar el token."
            )

        self.access_token = access_token
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
            self.access_token = None
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