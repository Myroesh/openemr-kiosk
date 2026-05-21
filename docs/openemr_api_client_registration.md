# Registro de API Client OpenEMR para Kiosko Flask

## Objetivo

Registrar un cliente OAuth/OpenID Connect para que el kiosko Flask pueda autenticarse contra la Standard API de OpenEMR.

Este cliente permite:

- leer pacientes
- crear pacientes
- leer encounters
- crear encounters
- obtener `access_token`
- obtener `refresh_token` mediante `offline_access`

---

## Fuente oficial

El registro se basa en la documentación oficial de OpenEMR para OAuth2 / OpenID Connect y Dynamic Client Registration.

Endpoint usado:

`POST /oauth2/default/registration`

Documento oficial de referencia:

`Documentation/api/AUTHENTICATION.md`

del repositorio oficial de OpenEMR.

---

## Importante: no usar la UI normal para este cliente

La UI normal de OpenEMR puede mostrar scopes FHIR con mayúsculas, por ejemplo:

`user/Patient.read`
`user/Patient.write`
`user/Encounter.read`

El kiosko usa la Standard API de OpenEMR, cuyos scopes son en minúscula:

`user/patient.read`
`user/patient.write`
`user/encounter.read`
`user/encounter.write`

Por eso este cliente debe registrarse mediante Dynamic Client Registration.

---

## Campo crítico

Para que OpenEMR acepte scopes `user/*` y `api:oemr`, el cliente debe registrarse como privado/confidencial:

`"application_type": "private"`

Si no se incluye, OpenEMR puede responder:

{
  "error": "invalid_client_metadata",
  "error_description": "system and user scopes are only allowed for confidential clients",
  "message": "system and user scopes are only allowed for confidential clients"
}

No basta con usar solamente campos como:

`"confidential": true`

OpenEMR espera `application_type`.

---

## Comando funcional usado en Tailscale

Este comando registra el cliente OAuth para Flask usando la IP actual de Tailscale.

curl -k -X POST 'https://100.124.189.84/oauth2/default/registration' \
  -H 'Content-Type: application/json' \
  --data '{
    "application_type": "private",
    "client_name": "OpenEMR Kiosk Flask OAuth",
    "redirect_uris": [
      "http://100.124.189.84:5000/admin/openemr/oauth/callback"
    ],
    "token_endpoint_auth_method": "client_secret_post",
    "contacts": [
      "dreamkatcher234@gmail.com"
    ],
    "scope": "openid offline_access api:oemr user/patient.read user/patient.write user/encounter.read user/encounter.write user/practitioner.read user/facility.read user/user.read"
  }'

---

## Resultado esperado

OpenEMR debe devolver un JSON que incluye, entre otros:

- `client_id`
- `client_secret`
- `client_name`
- `redirect_uris`
- `application_type`
- `token_endpoint_auth_method`
- `scope`

El `client_secret` se muestra al registrar el cliente. Guardarlo inmediatamente.

No commitear el `client_secret`.

---

## Variables `.env` requeridas

En:

`/opt/openemr-kiosk/.env`

configurar:

OPENEMR_BASE_URL=https://100.124.189.84
OPENEMR_SITE=default

OPENEMR_CLIENT_ID=PEGAR_CLIENT_ID
OPENEMR_CLIENT_SECRET="PEGAR_CLIENT_SECRET_COMPLETO"

OPENEMR_OAUTH_REDIRECT_URI=http://100.124.189.84:5000/admin/openemr/oauth/callback
OPENEMR_OAUTH_SCOPES="openid offline_access api:oemr user/patient.read user/patient.write user/encounter.read user/encounter.write user/practitioner.read user/facility.read user/user.read"

OPENEMR_TOKEN_FILE=data/openemr_tokens.json

Notas:

- `OPENEMR_BASE_URL` debe usar `https`.
- `OPENEMR_OAUTH_REDIRECT_URI` queda en `http` porque apunta al Flask dev server en puerto `5000`.
- El `redirect_uri` debe coincidir exactamente con el registrado en OpenEMR.
- Si el `client_secret` tiene caracteres especiales, ponerlo entre comillas.

---

## Flujo OAuth Flask

Rutas del kiosko:

- `/admin/openemr/oauth/start`
- `/admin/openemr/oauth/callback`
- `/admin/openemr/token/status`
- `/admin/openemr/token/save-manual`

Flujo:

1. `/admin/openemr/oauth/start`
2. Flask redirige a OpenEMR OAuth.
3. El admin autoriza scopes.
4. OpenEMR redirige a `/admin/openemr/oauth/callback`.
5. Flask intercambia code por tokens.
6. Los tokens se guardan en `data/openemr_tokens.json`.

Resultado esperado en `/admin/openemr/token/status`:

{
  "access_token_present": true,
  "refresh_token_present": true,
  "source": "authorization_code"
}

---

## Comando para red local del centro

Cuando se migre desde Tailscale a la red local del centro, registrar un nuevo cliente cambiando las IPs.

Ejemplo:

curl -k -X POST 'https://IP_OPENEMR_LOCAL/oauth2/default/registration' \
  -H 'Content-Type: application/json' \
  --data '{
    "application_type": "private",
    "client_name": "OpenEMR Kiosk Flask OAuth LAN",
    "redirect_uris": [
      "http://IP_KIOSKO_LOCAL:5000/admin/openemr/oauth/callback"
    ],
    "token_endpoint_auth_method": "client_secret_post",
    "contacts": [
      "dreamkatcher234@gmail.com"
    ],
    "scope": "openid offline_access api:oemr user/patient.read user/patient.write user/encounter.read user/encounter.write user/practitioner.read user/facility.read user/user.read"
  }'

Luego actualizar `.env` con:

OPENEMR_BASE_URL=https://IP_OPENEMR_LOCAL
OPENEMR_CLIENT_ID=
OPENEMR_CLIENT_SECRET=
OPENEMR_OAUTH_REDIRECT_URI=http://IP_KIOSKO_LOCAL:5000/admin/openemr/oauth/callback

---

## Scopes usados

- `openid`
- `offline_access`
- `api:oemr`
- `user/patient.read`
- `user/patient.write`
- `user/encounter.read`
- `user/encounter.write`
- `user/practitioner.read`
- `user/facility.read`
- `user/user.read`

Scopes mínimos actuales:

- `openid`
- `offline_access`
- `api:oemr`
- `user/patient.read`
- `user/patient.write`
- `user/encounter.read`
- `user/encounter.write`

`offline_access` es necesario para obtener `refresh_token`.

---

## Problemas encontrados

### Error: system and user scopes are only allowed for confidential clients

Causa:

El cliente no fue registrado como privado/confidencial.

Solución:

Agregar:

`"application_type": "private"`

---

### Error: invalid_client / Client authentication failed

Causas comunes:

- `OPENEMR_CLIENT_ID` incorrecto.
- `OPENEMR_CLIENT_SECRET` incorrecto.
- `client_secret` copiado incompleto.
- `.env` no fue recargado.
- Flask no fue reiniciado.
- `OPENEMR_BASE_URL` está en `http` en vez de `https`.

Verificación local:

cd /opt/openemr-kiosk
source .venv/bin/activate

python - <<'PY'
from config import Config

print("BASE_URL:", Config.OPENEMR_BASE_URL)
print("CLIENT_ID_PRESENT:", bool(Config.OPENEMR_CLIENT_ID))
print("CLIENT_ID_LENGTH:", len(Config.OPENEMR_CLIENT_ID or ""))
print("SECRET_PRESENT:", bool(Config.OPENEMR_CLIENT_SECRET))
print("SECRET_LENGTH:", len(Config.OPENEMR_CLIENT_SECRET or ""))
print("REDIRECT_URI:", Config.OPENEMR_OAUTH_REDIRECT_URI)
print("SCOPES:", Config.OPENEMR_OAUTH_SCOPES)
PY

---

### Error: redirect_uri mismatch

Causas comunes:

- El redirect URI del `.env` no coincide exactamente con el registrado.
- Diferencia entre `http` y `https`.
- Diferencia de puerto.
- Slash final extra.
- IP distinta.

Verificar que el cliente OpenEMR tenga exactamente:

`http://100.124.189.84:5000/admin/openemr/oauth/callback`

y que `.env` tenga exactamente:

OPENEMR_OAUTH_REDIRECT_URI=http://100.124.189.84:5000/admin/openemr/oauth/callback

---

## Seguridad

No commitear nunca:

- `.env`
- `data/openemr_tokens.json`
- `client_secret`
- `access_token`
- `refresh_token`
- Gemini API key
- contraseñas reales

Verificar antes de cada commit:

git status

---

## Estado confirmado

- Cliente OAuth Flask registrado correctamente.
- Cliente habilitado en `Admin → System → API Clients`.
- `application_type: private` confirmado como campo crítico.
- `offline_access` confirmado.
- `/admin/openemr/oauth/start` redirige correctamente a OpenEMR.
- OpenEMR muestra pantalla de autorización.
- `/admin/openemr/oauth/callback` recibe el código y guarda tokens.
- `/admin/openemr/token/status` confirma `refresh_token_present: true`.
