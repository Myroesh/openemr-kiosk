# OpenEMR API Notes

Notas verificadas para integración del kiosko Flask con OpenEMR.

## Estado actual confirmado

- OpenEMR version: 7.0.2
- Ruta servidor OpenEMR: `/var/www/html/openemr`
- Site OpenEMR: `default`
- OpenEMR base URL confirmada: `https://100.124.189.84`
- Swagger confirmado: `https://100.124.189.84/swagger/`
- API base confirmada: `https://100.124.189.84/apis/default/api`
- Endpoint de pacientes confirmado: `GET /api/patient`

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

OAuth2 no funcionó correctamente usando HTTP. El flujo empezó a funcionar al usar HTTPS, porque OpenEMR usa cookies seguras para el flujo OAuth.

## Swagger

Swagger debe usarse por HTTPS:

```text
https://100.124.189.84/swagger/
```

Servidor seleccionado en Swagger:

```text
/apis/default
```

Redirect URI usado para pruebas Swagger:

```text
https://100.124.189.84/swagger/oauth2-redirect.html
```

## Cliente OAuth2 funcional para Standard API

El cliente funcional para la Standard OpenEMR API fue registrado para uso con:

```text
api:oemr
```

El cliente anterior creado desde la pantalla SMART/FHIR no fue suficiente para el flujo Standard API porque ofrecía scopes tipo FHIR como:

```text
user/Patient.read
user/Encounter.read
```

Para Standard API, los scopes relevantes usan nombres tipo:

```text
user/patient.read
user/patient.write
user/encounter.read
user/encounter.write
```

## Registro de cliente Standard API

El cliente funcional fue creado para acceso a la Standard API.

Configuración usada conceptualmente:

- Application Type: private/confidential
- Redirect URI: `https://100.124.189.84/swagger/oauth2-redirect.html`
- Client name: `OpenEMR Kiosk Flask Standard API`
- API principal: `api:oemr`

Scopes objetivo para el kiosko:

```text
openid
offline_access
api:oemr
user/patient.read
user/patient.write
user/encounter.read
user/encounter.write
user/practitioner.read
user/facility.read
user/user.read
```

Nota:

No guardar `client_id` ni `client_secret` reales en GitHub. Deben ir solamente en `.env` local.

## Problemas encontrados y resolución

### 1. Register New App devolvía Not Authorized

Síntoma:

```text
Not Authorized
```

Causa:

La opción de Connectors no había sido guardada después de modificarla.

Resolución:

Entrar a:

```text
Admin → Config → Connectors
```

Activar las APIs necesarias y presionar `Save`.

### 2. OAuth fallaba con HTTP

Síntoma:

```text
application client_id was missing when it shouldn't have been
```

Causa:

El flujo OAuth perdía la sesión entre:

```text
/oauth2/default/authorize
/oauth2/default/provider/login
```

Resolución:

Configurar HTTPS en Apache y usar OpenEMR desde:

```text
https://100.124.189.84
```

Luego configurar:

```text
Site Address Override = https://100.124.189.84
```

### 3. Cliente OAuth creado pero no habilitado

Síntoma:

```text
CustomAuthCodeGrant->validateClient() client returned was not enabled
```

Causa:

El cliente OAuth2 fue creado, pero no estaba habilitado/aprobado.

Resolución:

Entrar a:

```text
Admin → System → API Clients
```

Editar el cliente y marcarlo como habilitado.

### 4. Swagger no enviaba Authorization header

Síntoma:

```json
{
  "hint": "Missing \"Authorization\" header"
}
```

Causa:

Swagger no había quedado autorizado correctamente o el flujo OAuth no había terminado con access token.

Resolución:

Reautorizar desde Swagger y confirmar que el curl generado incluya:

```text
Authorization: Bearer ...
```

### 5. invalid_client

Síntoma:

```text
Auth error
Error: Unauthorized, error: invalid_client, description: Client authentication failed
```

Causa confirmada:

El `client_secret` fue copiado incompleto porque la terminal lo recortó visualmente.

Resolución:

Copiar nuevamente el `client_secret` completo y reautorizar desde Swagger.

## Standard API - GET /api/patient confirmado

Se confirmó acceso exitoso a la Standard OpenEMR API usando HTTPS + OAuth2.

Endpoint probado:

```text
GET https://100.124.189.84/apis/default/api/patient
```

Resultado esperado confirmado:

```json
{
  "validationErrors": [],
  "internalErrors": [],
  "data": []
}
```

En la prueba real, `data` devolvió registros de pacientes existentes.

Conclusión:

- HTTPS funciona.
- OAuth2 funciona.
- El cliente Standard API funciona.
- Swagger obtiene access token.
- Swagger envía Bearer token.
- OpenEMR responde correctamente a `GET /api/patient`.

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

```text
Authorization: Bearer OCULTO
OPENEMR_CLIENT_SECRET=OCULTO
```

## Próximos pasos técnicos

Orden recomendado:

1. Probar búsqueda filtrada de paciente por nombre.
2. Probar búsqueda filtrada por teléfono.
3. Determinar campos mínimos confiables para identificar paciente existente.
4. Probar `POST /api/patient` con paciente de prueba controlado.
5. Probar creación de encounter para paciente existente.
6. Implementar servicio `openemr_service.py` en Flask.
7. Conectar flujo de paciente antiguo a búsqueda real en OpenEMR.
8. Conectar flujo de paciente nuevo a creación real en OpenEMR.
9. Mantener guardado local SQLite como respaldo/auditoría.

## Endpoints relevantes para el kiosko

Lectura de pacientes:

```text
GET /apis/default/api/patient
```

Paciente específico:

```text
GET /apis/default/api/patient/{puuid}
```

Crear paciente:

```text
POST /apis/default/api/patient
```

Encuentros de paciente:

```text
GET /apis/default/api/patient/{puuid}/encounter
```

Crear encounter:

```text
POST /apis/default/api/patient/{puuid}/encounter
```

## Estado final de esta fase

La fase de validación API queda marcada como completada:

- [x] Swagger localizado
- [x] Connectors activados
- [x] HTTPS configurado
- [x] Site Address Override configurado
- [x] Cliente OAuth2 funcional
- [x] Cliente habilitado
- [x] Bearer token obtenido
- [x] `GET /api/patient` confirmado con respuesta real
- [x] Se identificó que el error `invalid_client` fue por secret incompleto
- [x] Pendiente implementar consumo API desde Flask