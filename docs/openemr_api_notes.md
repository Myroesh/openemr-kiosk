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
- OAuth Flask confirmado: `/admin/openemr/oauth/start` y `/admin/openemr/oauth/callback`.
- Refresh token confirmado: `refresh_token_present: true`.
- Token store confirmado: `data/openemr_tokens.json`.

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

El cliente funcional para Standard API se registra mediante Dynamic Client Registration:

```text
POST /oauth2/default/registration

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

Orden recomendado desde el estado actual:

1. Mantener flujo de formularios como MVP operativo.
2. Probar renovación real de token dejando expirar access token o forzando expiración.
3. Completar pruebas pendientes de Fase 9.
4. Preparar despliegue local estable sin Flask debug server.
5. Configurar servicio systemd o Gunicorn.
6. Documentar operación local para personal técnico.
7. Luego continuar con interfaz conversacional Gemini sobre la arquitectura validada.

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