# OpenEMR API Notes

Notas verificadas para integración del kiosko Flask con OpenEMR.

---

## Estado actual confirmado

- OpenEMR version: 7.0.2
- Ruta servidor OpenEMR: `/var/www/html/openemr`
- Site OpenEMR: `default`
- OpenEMR base URL confirmada: `https://100.124.189.84`
- Swagger confirmado: `https://100.124.189.84/swagger/`
- API base confirmada: `https://100.124.189.84/apis/default/api`
- Endpoint de pacientes confirmado: `GET /apis/default/api/patient`
- Endpoint de creación de paciente confirmado: `POST /apis/default/api/patient`
- Endpoint de encounters confirmado: `GET /apis/default/api/patient/{puuid}/encounter`
- Endpoint de creación de encounter confirmado: `POST /apis/default/api/patient/{puuid}/encounter`
- OAuth Flask confirmado: `/admin/openemr/oauth/start` y `/admin/openemr/oauth/callback`
- Refresh token confirmado: `refresh_token_present: true`
- Token store confirmado: `data/openemr_tokens.json`

---

## Connectors

Ruta en OpenEMR:

`Admin → Config → Connectors`

Configuración verificada:

- Enable OpenEMR Standard REST API: activo
- Enable OpenEMR Standard FHIR REST API: activo
- Enable OpenEMR Patient Portal REST API: inactivo
- Enable OAuth2 Password Grant: Off
- Site Address Override: `https://100.124.189.84`

Nota importante:

OAuth2 no funcionó correctamente usando HTTP para OpenEMR.  
El flujo empezó a funcionar al usar HTTPS porque OpenEMR usa cookies seguras para el flujo OAuth.

Configuración correcta:

- OpenEMR: `https://100.124.189.84`
- Flask dev server: `http://100.124.189.84:5000`

---

## Swagger

Swagger debe usarse por HTTPS:

`https://100.124.189.84/swagger/`

Servidor seleccionado en Swagger:

`/apis/default`

Redirect URI usado para pruebas Swagger:

`https://100.124.189.84/swagger/oauth2-redirect.html`

Swagger fue útil para:

- revisar endpoints
- revisar payloads reales
- probar scopes
- copiar access token temporal durante desarrollo
- confirmar que la Standard API respondía correctamente

Pero Swagger no debe ser el mecanismo operativo final del kiosko.

---

## Diferencia importante: FHIR API vs Standard API

La UI normal de OpenEMR puede mostrar scopes FHIR con mayúsculas, por ejemplo:

- `user/Patient.read`
- `user/Patient.write`
- `user/Encounter.read`

El kiosko usa la Standard API de OpenEMR, cuyos scopes son en minúscula:

- `user/patient.read`
- `user/patient.write`
- `user/encounter.read`
- `user/encounter.write`

Por eso el cliente funcional para el kiosko se registró mediante Dynamic Client Registration y no mediante la UI normal que mostraba scopes FHIR.

---

## Cliente OAuth2 funcional para Standard API

El cliente funcional para la Standard OpenEMR API fue registrado con:

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

Scopes mínimos actuales del kiosko:

- `openid`
- `offline_access`
- `api:oemr`
- `user/patient.read`
- `user/patient.write`
- `user/encounter.read`
- `user/encounter.write`

`offline_access` es necesario para obtener `refresh_token`.

---

## Registro de cliente Standard API

El cliente funcional para Standard API se registra mediante Dynamic Client Registration:

`POST /oauth2/default/registration`

Campo crítico confirmado:

`"application_type": "private"`

Si no se incluye `application_type: private`, OpenEMR puede responder:

{
  "error": "invalid_client_metadata",
  "error_description": "system and user scopes are only allowed for confidential clients",
  "message": "system and user scopes are only allowed for confidential clients"
}

Documento detallado del procedimiento:

`docs/openemr_api_client_registration.md`

---

## Variables `.env` relevantes

Configuración actual esperada:

OPENEMR_BASE_URL=https://100.124.189.84
OPENEMR_SITE=default

OPENEMR_CLIENT_ID=CLIENT_ID_REAL
OPENEMR_CLIENT_SECRET="CLIENT_SECRET_REAL"

OPENEMR_OAUTH_REDIRECT_URI=http://100.124.189.84:5000/admin/openemr/oauth/callback
OPENEMR_OAUTH_SCOPES="openid offline_access api:oemr user/patient.read user/patient.write user/encounter.read user/encounter.write user/practitioner.read user/facility.read user/user.read"

OPENEMR_TOKEN_FILE=data/openemr_tokens.json
OPENEMR_VERIFY_SSL=false

Notas:

- `OPENEMR_BASE_URL` debe usar `https`.
- `OPENEMR_OAUTH_REDIRECT_URI` queda en `http` porque apunta al Flask dev server.
- El redirect URI debe coincidir exactamente con el cliente registrado en OpenEMR.
- El `client_secret` debe ponerse entre comillas si tiene caracteres especiales.
- `.env` no debe subirse a GitHub.

---

## Flujo OAuth Flask confirmado

Rutas implementadas:

- `/admin/openemr/oauth/start`
- `/admin/openemr/oauth/callback`
- `/admin/openemr/token/status`
- `/admin/openemr/token/save-manual`

Flujo real confirmado:

1. Admin abre `/admin/openemr/oauth/start`.
2. Flask genera `state` y redirige a OpenEMR OAuth.
3. OpenEMR muestra pantalla de autorización de scopes.
4. Admin autoriza.
5. OpenEMR redirige a `/admin/openemr/oauth/callback`.
6. Flask valida `state`.
7. Flask intercambia `authorization code` por tokens.
8. Flask guarda tokens en `data/openemr_tokens.json`.
9. `/admin/openemr/token/status` confirma `refresh_token_present: true`.

Resultado esperado en `/admin/openemr/token/status`:

{
  "access_token_present": true,
  "refresh_token_present": true,
  "source": "authorization_code"
}

---

## Token store

Archivo local de tokens:

`data/openemr_tokens.json`

Este archivo puede contener:

- `access_token`
- `refresh_token`
- `expires_in`
- `expires_at`
- `scope`
- `token_type`
- `source`
- `updated_at`

No debe subirse a GitHub.

`OpenEMRService` usa tokens con esta prioridad:

1. `data/openemr_tokens.json`
2. `.env` como fallback de desarrollo
3. refresh automático si existe `refresh_token`

---

## Endpoints administrativos del kiosko para OpenEMR

Estado del token:

`GET /admin/openemr/token/status`

Guardar token manual temporal:

`POST /admin/openemr/token/save-manual`

Iniciar OAuth:

`GET /admin/openemr/oauth/start`

Callback OAuth:

`GET /admin/openemr/oauth/callback`

Buscar pacientes:

`GET /admin/openemr/patients/search`

Leer encounters de paciente:

`GET /admin/openemr/patients/{uuid}/encounters`

Crear encounter de prueba controlada:

`POST /admin/openemr/patients/{uuid}/encounter/test`

Crear paciente de prueba controlada:

`POST /admin/openemr/patient/test`

---

## Endpoints Standard API usados por el kiosko

Lectura de pacientes:

`GET /apis/default/api/patient`

Crear paciente:

`POST /apis/default/api/patient`

Encuentros de paciente:

`GET /apis/default/api/patient/{puuid}/encounter`

Crear encounter:

`POST /apis/default/api/patient/{puuid}/encounter`

---

## Payload confirmado para crear paciente

Endpoint:

`POST /apis/default/api/patient`

Payload base confirmado desde Swagger:

{
  "title": "Mr",
  "fname": "Foo",
  "mname": "",
  "lname": "Bar",
  "street": "456 Tree Lane",
  "postal_code": "08642",
  "city": "FooTown",
  "state": "FL",
  "country_code": "US",
  "phone_contact": "123-456-7890",
  "DOB": "1992-02-02",
  "sex": "Male",
  "race": "",
  "ethnicity": ""
}

Campo obligatorio confirmado:

- `sex`

Error observado si se omite:

{
  "validationErrors": {
    "sex": {
      "NotEmpty::EMPTY_VALUE": "Gender must not be empty"
    }
  }
}

Resolución:

El formulario `/nuevo` incluye campo `sexo` con valores:

- `Male`
- `Female`
- `Other`

---

---

## Payload confirmado para guardianes de menores

Endpoint:

```text
POST /apis/default/api/patient
```

Se confirmó que OpenEMR acepta y guarda correctamente los siguientes campos de guardian dentro del payload de creación de paciente:

```text
guardiansname
guardianrelationship
guardianphone
```

Estos campos existen en la tabla:

```text
patient_data
```

Consulta usada para verificar columnas:

```bash
sudo mysql openemr -e "
SHOW COLUMNS FROM patient_data
LIKE '%guardian%';
"
```

Columnas relevantes confirmadas:

```text
guardiansname
guardianrelationship
guardiansex
guardianaddress
guardiancity
guardianstate
guardianpostalcode
guardiancountry
guardianphone
guardianworkphone
guardianemail
```

También existe:

```text
mothersname
```

pero no se usa en el flujo actual para evitar duplicar visualmente el dato de la madre cuando se registra dentro del campo `guardiansname`.

### Regla de mapeo del kiosko

El kiosko usa los campos guardian como referencia clínica visible para los doctores.

Regla actual:

```text
Si solo hay padre:
  guardiansname = Padre: NOMBRE_PADRE
  guardianrelationship = Padre
  guardianphone = Padre: TELEFONO_PADRE

Si solo hay madre:
  guardiansname = Madre: NOMBRE_MADRE
  guardianrelationship = Madre
  guardianphone = Madre: TELEFONO_MADRE

Si hay padre y madre:
  guardiansname = Padre: NOMBRE_PADRE / Madre: NOMBRE_MADRE
  guardianrelationship = Padre/Madre
  guardianphone = Padre: TELEFONO_PADRE / Madre: TELEFONO_MADRE
```

### Payload dry-run confirmado

Ruta admin del kiosko usada:

```text
POST /admin/openemr/patient/test
```

Payload recibido por el kiosko:

```json
{
  "nombres": "Tutor",
  "apellidos": "TESTKIOSKO",
  "fecha_nacimiento": "2015-01-01",
  "sexo": "Male",
  "telefono": "70707070",
  "direccion": "Prueba guardian",
  "es_menor": 1,
  "padre_nombre": "Carlos Test Padre",
  "padre_telefono": "71111111",
  "madre_nombre": "Maria Test Madre",
  "madre_telefono": "72222222"
}
```

Payload generado hacia OpenEMR:

```json
{
  "title": "",
  "fname": "Tutor",
  "mname": "",
  "lname": "TESTKIOSKO",
  "street": "Prueba guardian",
  "postal_code": "",
  "city": "",
  "state": "",
  "country_code": "BO",
  "phone_contact": "70707070",
  "DOB": "2015-01-01",
  "sex": "Male",
  "race": "",
  "ethnicity": "",
  "guardiansname": "Padre: Carlos Test Padre / Madre: Maria Test Madre",
  "guardianrelationship": "Padre/Madre",
  "guardianphone": "Padre: 71111111 / Madre: 72222222"
}
```

### Prueba real confirmada por API

Ruta usada:

```text
POST /admin/openemr/patient/test?confirm=CREATE
```

Respuesta confirmada:

```json
{
  "message": "Paciente creado en OpenEMR.",
  "result": {
    "data": {
      "pid": 42,
      "uuid": "a1d770cf-fab2-46fa-85a4-b76b8a33aea2"
    },
    "internalErrors": [],
    "links": [],
    "validationErrors": []
  },
  "service": "openemr",
  "status": "ok"
}
```

Verificación SQL:

```bash
sudo mysql openemr -e "
SELECT
  pid,
  fname,
  lname,
  DOB,
  guardiansname,
  guardianrelationship,
  guardianphone,
  mothersname
FROM patient_data
WHERE lname = 'TESTKIOSKO'
ORDER BY pid DESC
LIMIT 5;
"
```

Resultado confirmado:

```text
pid: 42
fname: Tutor
lname: TESTKIOSKO
DOB: 2015-01-01
guardiansname: Padre: Carlos Test Padre / Madre: Maria Test Madre
guardianrelationship: Padre/Madre
guardianphone: Padre: 71111111 / Madre: 72222222
mothersname: vacío
```

### Prueba real desde flujo del kiosko

También se confirmó desde el flujo real:

```text
/nuevo
/confirmar
```

Paciente creado:

```text
PID: 43
Paciente: Menor Guardiantest
DOB: 2009-02-02
```

Guardianes guardados:

```text
guardiansname: Padre: Roberto Guardian / Madre: Maria Guardian
guardianrelationship: Padre/Madre
guardianphone: Padre: 71112222 / Madre: 72223333
mothersname: vacío
```

Encounter creado:

```text
encounter: 86
reason: Consulta Inicial
provider_id: 5
provider_name: Evelyn Mejia Patiño
pc_catid: 16
pc_catname: Consulta Inicial
```

### Implementación en código

La construcción del payload guardian se realiza en:

```text
services/openemr_service.py
```

Función:

```text
build_kiosk_guardian_payload()
```

El payload principal se arma en:

```text
build_kiosk_patient_payload()
```

y luego agrega los campos guardian mediante:

```text
payload.update(self.build_kiosk_guardian_payload(patient_data))
```

## Payload confirmado para crear encounter

Endpoint:

`POST /apis/default/api/patient/{puuid}/encounter`

Payload base confirmado desde Swagger:

{
  "date": "2020-11-10",
  "onset_date": "",
  "reason": "Pregnancy Test",
  "facility": "Owerri General Hospital",
  "pc_catid": "5",
  "facility_id": "3",
  "billing_facility": "3",
  "sensitivity": "normal",
  "referral_source": "",
  "pos_code": "0",
  "external_id": "",
  "provider_id": "1",
  "class_code": "AMB"
}

Payload usado por el kiosko:

- `date`: fecha actual
- `reason`: motivo de consulta seleccionado
- `facility`: `OPENEMR_DEFAULT_FACILITY`
- `pc_catid`: `OPENEMR_DEFAULT_PC_CATID`
- `facility_id`: `OPENEMR_DEFAULT_FACILITY_ID`
- `billing_facility`: `OPENEMR_DEFAULT_BILLING_FACILITY`
- `provider_id`: `OPENEMR_DEFAULT_PROVIDER_ID`
- `class_code`: `OPENEMR_DEFAULT_CLASS_CODE`
- `sensitivity`: `OPENEMR_DEFAULT_SENSITIVITY`

---

## Motivo de consulta

El campo `motivo_consulta` ya no es texto libre.

Catálogo confirmado:

- Consulta Inicial
- Sesión
- Revisión de resultados
- Test
- Entrevista con los padres

Valor por defecto:

- Sesión

Aplica a:

- `/nuevo`
- `/antiguo`
- Gemini classifier

El backend valida contra catálogo cerrado en `services/validation_service.py`.

---

## Flujo paciente nuevo confirmado

Flujo actual:

1. `/nuevo`
2. Formulario paciente nuevo
3. Validaciones backend
4. Búsqueda de duplicados en OpenEMR
5. `/confirmar`
6. Confirmación final
7. Revalidación de duplicados antes de crear
8. Crear paciente en OpenEMR
9. Crear encounter inicial en OpenEMR
10. Guardar intake local como respaldo/auditoría
11. Registrar evento en `kiosk_events`
12. `/exito`

Confirmado:

- Paciente nuevo se crea en OpenEMR.
- Encounter inicial se crea en OpenEMR.
- Duplicados se bloquean antes de crear.
- No se crean datos sin confirmación final.

---

## Flujo paciente antiguo confirmado

Flujo actual:

1. `/antiguo`
2. Búsqueda por nombre/teléfono
3. Búsqueda real en OpenEMR mediante `OpenEMRService.search_patients()`
4. Si hay un paciente único, pasa a confirmación
5. Si hay múltiples o ninguno, bloquea y pide ayuda en recepción
6. `/confirmar-antiguo`
7. Confirmación de identidad
8. Crear encounter en OpenEMR
9. Registrar evento en `kiosk_events`
10. `/exito`

Confirmado:

- Paciente antiguo se busca en OpenEMR.
- Paciente antiguo confirmado crea encounter real.
- Teléfono incorrecto con nombre común bloquea adecuadamente.
- Nombre único devuelve el paciente correcto.

---

## Problemas encontrados y resolución

### 1. Register New App devolvía Not Authorized

Síntoma:

`Not Authorized`

Causa:

La opción de Connectors no había sido guardada después de modificarla.

Resolución:

Entrar a:

`Admin → Config → Connectors`

Activar las APIs necesarias y presionar `Save`.

---

### 2. OAuth fallaba con HTTP

Síntoma:

`application client_id was missing when it shouldn't have been`

Causa:

El flujo OAuth perdía la sesión entre:

`/oauth2/default/authorize`

y:

`/oauth2/default/provider/login`

Resolución:

Configurar HTTPS en Apache y usar OpenEMR desde:

`https://100.124.189.84`

Luego configurar:

`Site Address Override = https://100.124.189.84`

---

### 3. Cliente OAuth creado pero no habilitado

Síntoma:

`CustomAuthCodeGrant->validateClient() client returned was not enabled`

Causa:

El cliente OAuth2 fue creado, pero no estaba habilitado/aprobado.

Resolución:

Entrar a:

`Admin → System → API Clients`

Editar el cliente y marcarlo como habilitado.

---

### 4. Swagger no enviaba Authorization header

Síntoma:

{
  "hint": "Missing \"Authorization\" header"
}

Causa:

Swagger no había quedado autorizado correctamente o el flujo OAuth no había terminado con access token.

Resolución:

Reautorizar desde Swagger y confirmar que el curl generado incluya:

`Authorization: Bearer ...`

---

### 5. invalid_client

Síntoma:

`Auth error`

`Error: Unauthorized, error: invalid_client, description: Client authentication failed`

Causas confirmadas o probables:

- `client_secret` copiado incompleto.
- `OPENEMR_CLIENT_ID` incorrecto.
- `OPENEMR_CLIENT_SECRET` incorrecto.
- `.env` no recargado.
- Flask no reiniciado.
- `OPENEMR_BASE_URL` en `http` en lugar de `https`.

Resolución:

- Copiar el `client_secret` completo.
- Poner el secret entre comillas en `.env`.
- Confirmar `OPENEMR_BASE_URL=https://100.124.189.84`.
- Reiniciar Flask.

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

### 6. invalid_client_metadata al registrar cliente Standard API

Síntoma:

{
  "error": "invalid_client_metadata",
  "error_description": "system and user scopes are only allowed for confidential clients",
  "message": "system and user scopes are only allowed for confidential clients"
}

Causa:

El cliente no fue registrado como confidencial/privado.

Resolución:

Registrar el cliente mediante Dynamic Client Registration usando:

`"application_type": "private"`

No usar solamente:

`"confidential": true`

porque OpenEMR espera `application_type`.

---

### 7. invalid_scope

Síntoma:

`invalid_scope`

Causa:

Se estaba solicitando un scope no válido para esa instalación, como `site:default`.

Resolución:

No pedir manualmente `site:default`.

Scopes correctos usados:

- `openid`
- `offline_access`
- `api:oemr`
- `user/patient.read`
- `user/patient.write`
- `user/encounter.read`
- `user/encounter.write`

---

### 8. Refresh token inválido

Síntoma:

`The refresh token is invalid`

Causa:

Refresh token mal copiado, no emitido, vencido o no descifrable por OpenEMR.

Resolución:

- No depender de refresh token manual.
- Implementar OAuth Flask start/callback.
- Obtener refresh token real mediante `offline_access`.
- Guardar tokens en `data/openemr_tokens.json`.

Estado actual:

- `refresh_token_present: true` confirmado.

---

## Datos sensibles

No pegar en documentación ni commits:

- `client_id` real
- `client_secret` real
- access tokens Bearer
- refresh tokens
- Gemini API key
- contraseñas reales
- respuestas completas con datos personales de pacientes

Para debug, censurar así:

- `Authorization: Bearer OCULTO`
- `OPENEMR_CLIENT_SECRET=OCULTO`

---

## Estado final de esta fase

La fase de integración API y OAuth queda marcada como completada:

- [x] Swagger localizado.
- [x] Connectors activados.
- [x] HTTPS configurado.
- [x] Site Address Override configurado.
- [x] Cliente OAuth2 Swagger funcional.
- [x] Cliente OAuth2 Flask funcional.
- [x] Cliente Flask registrado mediante Dynamic Client Registration.
- [x] `application_type: private` confirmado como campo crítico.
- [x] `offline_access` confirmado.
- [x] Bearer token obtenido.
- [x] Refresh token obtenido.
- [x] Tokens guardados en `data/openemr_tokens.json`.
- [x] `/admin/openemr/token/status` confirmado.
- [x] `/admin/openemr/token/save-manual` confirmado.
- [x] `/admin/openemr/oauth/start` confirmado.
- [x] `/admin/openemr/oauth/callback` confirmado.
- [x] `GET /api/patient` confirmado con respuesta real.
- [x] `POST /api/patient` confirmado con paciente de prueba.
- [x] `POST /api/patient/{puuid}/encounter` confirmado con encounter de prueba.
- [x] Flask consume OpenEMR API mediante `OpenEMRService`.

---

## Próximos pasos técnicos

Orden recomendado desde el estado actual:

1. Mantener flujo de formularios como MVP operativo.
2. Probar renovación real de token dejando expirar access token o forzando expiración.
3. Completar pruebas pendientes de Fase 9.
4. Preparar despliegue local estable sin Flask debug server.
5. Configurar servicio systemd o Gunicorn.
6. Documentar operación local para personal técnico.
7. Luego continuar con interfaz conversacional Gemini sobre la arquitectura validada.
