# Operación local - OpenEMR Kiosk

Kiosko de recepción para el Centro Neuropsicológico Saavedra.

Este documento describe cómo iniciar, detener, probar, revisar logs, validar OAuth/OpenEMR y operar el kiosko durante el desarrollo local.

---

## 1. Estado actual del proyecto

Estado confirmado en la rama `flask-mvp`:

- El kiosko corre con Flask.
- La tablet no se conecta directamente a OpenEMR.
- La tablet habla con Flask.
- Flask valida datos, registra logs y luego consume la API de OpenEMR.
- El flujo de paciente nuevo crea:
  - paciente nuevo en OpenEMR
  - encounter inicial en OpenEMR
- El flujo de paciente antiguo:
  - busca paciente en OpenEMR
  - confirma identidad
  - crea encounter en OpenEMR
- OAuth Flask ya funciona con:
  - Dynamic Client Registration
  - `offline_access`
  - `refresh_token`
  - token store local en `data/openemr_tokens.json`
- Gemini Flash está integrado de forma controlada para clasificación de motivo de consulta, pero no escribe directamente en OpenEMR.

---

## 2. Ubicación del proyecto

El proyecto está ubicado en:

```bash
/opt/openemr-kiosk
```

Entrar al proyecto:

```bash
cd /opt/openemr-kiosk
```

---

## 3. Repositorio y rama de trabajo

Repositorio:

```text
Myroesh/openemr-kiosk
```

Rama activa de desarrollo:

```text
flask-mvp
```

Verificar rama actual:

```bash
git branch
```

La rama correcta debe aparecer marcada con `*`:

```bash
* flask-mvp
```

Si no estás en la rama correcta:

```bash
git checkout flask-mvp
```

---

## 4. Archivos clave

Archivos principales del proyecto:

```text
app.py
config.py
requirements.txt
.env
data/kiosk.db
data/openemr_tokens.json
services/openemr_service.py
services/token_store.py
services/db_service.py
services/validation_service.py
services/gemini_service.py
docs/OPERACION_LOCAL.md
docs/openemr_api_notes.md
docs/openemr_api_client_registration.md
docs/todo.md
```

Archivos sensibles que existen solo localmente:

```text
.env
data/openemr_tokens.json
data/kiosk.db
```

Estos archivos no deben subirse a GitHub.

---

## 5. Activar entorno virtual

Antes de correr Flask, activar el entorno virtual:

```bash
cd /opt/openemr-kiosk
source .venv/bin/activate
```

Si se activó correctamente, la terminal debe mostrar algo parecido a:

```bash
(.venv) openemr@openemr:/opt/openemr-kiosk$
```

---

## 6. Instalar dependencias

Si falta alguna dependencia o se está preparando una instalación nueva:

```bash
cd /opt/openemr-kiosk
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias actuales:

```text
Flask
python-dotenv
requests
google-genai
```

---

## 7. Variables de entorno locales

El archivo local de configuración es:

```bash
.env
```

Debe estar en la raíz del proyecto:

```bash
/opt/openemr-kiosk/.env
```

Ejemplo de estructura esperada:

```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=CAMBIAR_CLAVE_LOCAL

GEMINI_API_KEY=PEGAR_API_KEY_REAL
GEMINI_MODEL=gemini-2.5-flash

ADMIN_USERNAME=admin
ADMIN_PASSWORD=CLAVE_LOCAL_ADMIN

KIOSK_DB_PATH=data/kiosk.db

OPENEMR_BASE_URL=https://100.124.189.84
OPENEMR_SITE=default

OPENEMR_CLIENT_ID=PEGAR_CLIENT_ID_REAL
OPENEMR_CLIENT_SECRET="PEGAR_CLIENT_SECRET_REAL"

OPENEMR_VERIFY_SSL=false

OPENEMR_DEFAULT_FACILITY=Centro Neuropsicologico Saavedra
OPENEMR_DEFAULT_PC_CATID=5
OPENEMR_DEFAULT_FACILITY_ID=3
OPENEMR_DEFAULT_BILLING_FACILITY=3
OPENEMR_DEFAULT_PROVIDER_ID=1
OPENEMR_DEFAULT_POS_CODE=0
OPENEMR_DEFAULT_CLASS_CODE=AMB
OPENEMR_DEFAULT_SENSITIVITY=normal

OPENEMR_TOKEN_FILE=data/openemr_tokens.json

OPENEMR_OAUTH_REDIRECT_URI=http://100.124.189.84:5000/admin/openemr/oauth/callback
OPENEMR_OAUTH_SCOPES="openid offline_access api:oemr user/patient.read user/patient.write user/encounter.read user/encounter.write user/practitioner.read user/facility.read user/user.read"
```

Notas importantes:

- `OPENEMR_BASE_URL` debe usar `https`.
- Flask local corre por `http` en puerto `5000`.
- `OPENEMR_OAUTH_REDIRECT_URI` debe coincidir exactamente con el redirect URI registrado en OpenEMR.
- Si el `client_secret` tiene caracteres especiales, ponerlo entre comillas.
- No subir `.env` a GitHub.

Verificar que `.env` no aparezca en Git:

```bash
git status
```

No debe aparecer:

```text
.env
```

---

## 8. Iniciar servidor Flask de desarrollo

Con el entorno virtual activo:

```bash
cd /opt/openemr-kiosk
source .venv/bin/activate
python app.py
```

El kiosko queda disponible en:

```text
http://100.124.189.84:5000
```

Endpoint de salud:

```text
http://100.124.189.84:5000/health
```

Importante:

Durante desarrollo, Flask se usa por HTTP.

Correcto:

```text
http://100.124.189.84:5000
```

Incorrecto:

```text
https://100.124.189.84:5000
```

Si se usa HTTPS por error contra Flask, el navegador puede mostrar error SSL y Flask puede mostrar errores tipo `Bad request version`.

---

## 9. Detener servidor Flask

En la terminal donde está corriendo Flask:

```text
Ctrl + C
```

---

## 10. Si el puerto 5000 queda ocupado

Error típico:

```text
Address already in use
Port 5000 is in use by another program
```

Ver qué proceso usa el puerto:

```bash
sudo ss -ltnp | grep :5000
```

Alternativa:

```bash
sudo lsof -i :5000
```

Matar el proceso usando el PID:

```bash
sudo kill PID
```

Si no se detiene:

```bash
sudo kill -9 PID
```

Alternativa rápida:

```bash
sudo fuser -k 5000/tcp
```

Luego volver a iniciar:

```bash
python app.py
```

---

## 11. Rutas públicas principales

Pantalla inicial:

```text
http://100.124.189.84:5000/
```

Paciente nuevo:

```text
http://100.124.189.84:5000/nuevo
```

Paciente antiguo:

```text
http://100.124.189.84:5000/antiguo
```

Confirmación de paciente nuevo:

```text
http://100.124.189.84:5000/confirmar
```

Confirmación de paciente antiguo:

```text
http://100.124.189.84:5000/confirmar-antiguo
```

Pantalla final:

```text
http://100.124.189.84:5000/exito
```

---

## 12. Rutas de salud

Salud básica del kiosko:

```text
http://100.124.189.84:5000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "openemr-kiosk",
  "version": "flask-mvp"
}
```

Prueba Gemini:

```text
http://100.124.189.84:5000/health/gemini
```

Prueba OpenEMR:

```text
http://100.124.189.84:5000/health/openemr
```

La ruta `/health/openemr` está protegida con Basic Auth.

---

## 13. Panel administrativo

Panel de logs:

```text
http://100.124.189.84:5000/admin/logs
```

Estado del token OpenEMR:

```text
http://100.124.189.84:5000/admin/openemr/token/status
```

Inicio OAuth OpenEMR:

```text
http://100.124.189.84:5000/admin/openemr/oauth/start
```

Búsqueda admin de pacientes:

```text
http://100.124.189.84:5000/admin/openemr/patients/search?q=juan
```

Prueba Gemini de motivo de consulta:

```text
http://100.124.189.84:5000/admin/gemini/consultation-reason/test
```

Estas rutas están protegidas con Basic Auth, excepto el callback OAuth.

Credenciales locales:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=CLAVE_LOCAL_ADMIN
```

No subir estas credenciales a GitHub.

---

## 14. Base de datos local SQLite

La base local del kiosko se guarda en:

```bash
data/kiosk.db
```

Uso actual:

- logs del kiosko
- eventos técnicos
- registros temporales/auditoría del MVP
- respaldo local mínimo de intakes

La base local no reemplaza a OpenEMR.

Si en desarrollo se necesita resetear datos locales de prueba:

```bash
rm -f data/kiosk.db
```

Luego reiniciar Flask:

```bash
python app.py
```

La base se recreará automáticamente.

---

## 15. Token store OpenEMR

Los tokens OAuth de OpenEMR se guardan localmente en:

```bash
data/openemr_tokens.json
```

Este archivo puede contener:

```text
access_token
refresh_token
expires_in
expires_at
scope
token_type
source
updated_at
```

No subir este archivo a GitHub.

Verificar estado del token desde navegador:

```text
http://100.124.189.84:5000/admin/openemr/token/status
```

Resultado esperado:

```json
{
  "status": "ok",
  "service": "openemr",
  "token": {
    "access_token_present": true,
    "refresh_token_present": true,
    "source": "authorization_code"
  }
}
```

No pegar tokens completos en chats, commits ni documentación.

---

## 16. Flujo OAuth Flask confirmado

Rutas implementadas:

```text
/admin/openemr/oauth/start
/admin/openemr/oauth/callback
/admin/openemr/token/status
/admin/openemr/token/save-manual
```

Flujo:

1. Admin abre:

```text
http://100.124.189.84:5000/admin/openemr/oauth/start
```

2. Flask genera `state`.
3. Flask redirige a OpenEMR OAuth.
4. OpenEMR muestra pantalla de autorización.
5. Admin autoriza los scopes.
6. OpenEMR redirige a:

```text
http://100.124.189.84:5000/admin/openemr/oauth/callback
```

7. Flask valida `state`.
8. Flask intercambia authorization code por tokens.
9. Flask guarda tokens en:

```text
data/openemr_tokens.json
```

10. Verificar:

```text
http://100.124.189.84:5000/admin/openemr/token/status
```

Debe confirmar:

```text
refresh_token_present: true
```

---

## 17. Registro del cliente OAuth OpenEMR

El cliente funcional se registra mediante Dynamic Client Registration:

```text
POST /oauth2/default/registration
```

Campo crítico:

```json
"application_type": "private"
```

Este campo es obligatorio para que OpenEMR acepte scopes `user/*` y `api:oemr`.

Scopes usados:

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

`offline_access` es necesario para obtener `refresh_token`.

Documento detallado:

```text
docs/openemr_api_client_registration.md
```

---

## 18. OpenEMR API confirmada

Configuración confirmada:

```text
OpenEMR version: 7.0.2
OpenEMR site: default
OpenEMR base URL: https://100.124.189.84
Swagger: https://100.124.189.84/swagger/
API base: https://100.124.189.84/apis/default/api
```

Endpoints confirmados:

```text
GET  /apis/default/api/patient
POST /apis/default/api/patient
GET  /apis/default/api/patient/{puuid}/encounter
POST /apis/default/api/patient/{puuid}/encounter
```

Documento de notas API:

```text
docs/openemr_api_notes.md
```

No inventar endpoints. Si se necesita un endpoint nuevo, primero verificar en Swagger de la instalación real.

---

## 19. Flujo actual: paciente nuevo

Flujo real:

```text
/nuevo
↓
formulario paciente nuevo
↓
validaciones backend
↓
búsqueda de duplicados en OpenEMR
↓
/confirmar
↓
confirmación final
↓
revalidación de duplicados
↓
crear paciente en OpenEMR
↓
crear encounter inicial en OpenEMR
↓
guardar respaldo/auditoría local en SQLite
↓
registrar evento en kiosk_events
↓
/exito
```


Confirmado:

- No se crea paciente sin confirmación final.
- Se busca posible duplicado antes de crear.
- Se vuelve a validar antes de crear.
- Si OpenEMR crea paciente pero no devuelve UUID, se bloquea la creación del encounter y se registra error.
- Si la creación falla, se muestra mensaje seguro al usuario.

---

## Registro de menores de edad y datos de guardianes

El formulario de paciente nuevo detecta automáticamente si el paciente es menor de edad usando la fecha de nacimiento.

Regla actual:

```text
Si edad < 18:
  es_menor = 1
  se despliega automáticamente la sección de padre/madre/tutor
  se exige al menos nombre del padre o nombre de la madre

Si edad >= 18:
  es_menor = 0
  no se muestra la sección de padre/madre/tutor
```

La detección visual ocurre en:

```text
templates/nuevo.html
```

La validación real ocurre en backend, no en JavaScript:

```text
services/validation_service.py
```

Esto es importante porque el frontend solo ayuda a la experiencia de usuario. La decisión final de si el paciente es menor de edad se recalcula en backend a partir de `fecha_nacimiento`.

### Datos obligatorios para menores

Para pacientes menores de edad:

```text
Debe registrarse al menos:
- nombre del padre
  o
- nombre de la madre
```

Los siguientes datos son opcionales, pero si se llenan deben ser válidos:

```text
CI del padre
Teléfono del padre
CI de la madre
Teléfono de la madre
```

Los teléfonos se validan como celulares bolivianos de 8 dígitos, comenzando en 6 o 7.

### Mapeo de guardianes hacia OpenEMR

Los datos de padre/madre se envían a OpenEMR usando los campos estándar de guardian en `patient_data`.

Campos usados:

```text
guardiansname
guardianrelationship
guardianphone
```

No se usa `mothersname` en este flujo para evitar duplicidad visual cuando ya se registra la madre dentro de `guardiansname`.

Regla de mapeo:

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

Ejemplo confirmado:

```text
guardiansname = Padre: Roberto Guardian / Madre: Maria Guardian
guardianrelationship = Padre/Madre
guardianphone = Padre: 71112222 / Madre: 72223333
mothersname = vacío
```

### Prueba real confirmada

Se probó desde el flujo real del kiosko:

```text
/nuevo
↓
detección automática de menor de edad
↓
registro de padre y madre
↓
/confirmar
↓
creación de paciente en OpenEMR
↓
creación de Consulta Inicial
```

Resultado confirmado en OpenEMR:

```text
PID: 43
Paciente: Menor Guardiantest
DOB: 2009-02-02
Edad mostrada en OpenEMR: 17
```

Datos guardian guardados:

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

### Verificación SQL

Ver datos guardian de un paciente:

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
WHERE pid = PID_AQUI;
"
```

Ver encounter del paciente:

```bash
sudo mysql openemr -e "
SELECT
  fe.pid,
  fe.encounter,
  fe.date,
  fe.reason,
  fe.provider_id,
  CONCAT(u.fname, ' ', u.lname) AS provider_name,
  fe.pc_catid,
  c.pc_catname
FROM form_encounter fe
LEFT JOIN users u
  ON u.id = fe.provider_id
LEFT JOIN openemr_postcalendar_categories c
  ON c.pc_catid = fe.pc_catid
WHERE fe.pid = PID_AQUI
ORDER BY fe.encounter ASC;
"
```

Reemplazar:

```text
PID_AQUI
```

por el número real del paciente.

### Archivos relacionados

```text
templates/nuevo.html
services/validation_service.py
services/openemr_service.py
templates/confirmar.html
```

---

## 20. Flujo actual: paciente antiguo

Flujo real:

```text
/antiguo
↓
búsqueda por nombre/teléfono
↓
validaciones backend
↓
búsqueda real en OpenEMR
↓
si hay un paciente único: /confirmar-antiguo
↓
confirmación de identidad
↓
crear encounter en OpenEMR
↓
registrar evento en kiosk_events
↓
/exito
```

Reglas actuales:

- Si no hay coincidencias, se bloquea y pide ayuda en recepción.
- Si hay múltiples coincidencias, se bloquea y pide ayuda en recepción.
- Solo si hay un paciente único se permite confirmar.
- No se crea encounter sin confirmación final.

---

## 21. Motivos de consulta permitidos

El motivo de consulta usa catálogo cerrado.

Opciones:

```text
Consulta Inicial
Sesión
Revisión de resultados
Test
Entrevista con los padres
```

Valor por defecto:

```text
Sesión
```

Aplica a:

```text
/nuevo
/antiguo
Gemini classifier
```

El backend valida contra catálogo cerrado en:

```text
services/validation_service.py
```

---

## 22. Validaciones actuales

El servicio de validación está en:

```bash
services/validation_service.py
```

Actualmente valida:

- nombres y apellidos obligatorios para paciente nuevo
- fecha de nacimiento obligatoria
- fecha de nacimiento no futura
- edad coherente con menor/adulto
- CI/documento opcional, pero validado si se llena
- teléfono celular boliviano o formato aceptado
- sexo obligatorio para crear paciente en OpenEMR
- motivo de consulta obligatorio
- motivo de consulta dentro de catálogo cerrado
- profesional obligatorio
- padre o madre obligatorio si el paciente es menor de edad
- normalización básica de textos

---

## 23. Profesionales

La lista de profesionales está en:

```bash
config.py
```

Dentro de:

```python
PROFESSIONALS = [
    "Dra. Ana Maria Saavedra",
    "Dra. Evelyn vidal",
    "Dra. Katherine",
    "Dr. Luis",
]
```

Para modificar los profesionales:

1. Editar `config.py`.
2. Guardar cambios.
3. Probar sintaxis:

```bash
python -m py_compile config.py app.py
```

4. Reiniciar Flask:

```bash
python app.py
```

---

## 24. Gemini

Gemini está integrado como servicio controlado.

Modelo configurado:

```text
gemini-2.5-flash
```

Endpoint de prueba:

```text
http://100.124.189.84:5000/health/gemini
```

Endpoint admin para clasificación de motivo:

```text
http://100.124.189.84:5000/admin/gemini/consultation-reason/test
```

Gemini puede:

- clasificar motivo de consulta
- devolver resultado estructurado
- usar fallback seguro

Gemini no puede:

- crear pacientes directamente
- crear encounters directamente
- decidir acciones clínicas
- saltarse confirmaciones

Si Gemini falla:

1. Verificar que `.env` tenga `GEMINI_API_KEY`.
2. Verificar que `GEMINI_MODEL=gemini-2.5-flash`.
3. Reiniciar Flask.
4. Probar `/health/gemini`.
5. Revisar `/admin/logs`.

---

## 25. Prueba rápida de sintaxis

Antes de correr o después de modificar código:

```bash
cd /opt/openemr-kiosk
source .venv/bin/activate

python -m py_compile \
  app.py \
  config.py \
  services/validation_service.py \
  services/db_service.py \
  services/gemini_service.py \
  services/openemr_service.py \
  services/token_store.py
```

Si no devuelve nada, la sintaxis está bien.

---

## 26. Prueba rápida del sistema

Con Flask corriendo:

```text
http://100.124.189.84:5000/health
```

Resultado esperado:

```json
{
  "status": "ok",
  "service": "openemr-kiosk",
  "version": "flask-mvp"
}
```

Probar Gemini:

```text
http://100.124.189.84:5000/health/gemini
```

Probar OpenEMR:

```text
http://100.124.189.84:5000/health/openemr
```

Si `/health/openemr` falla:

1. Revisar `.env`.
2. Revisar `OPENEMR_BASE_URL`.
3. Revisar `OPENEMR_VERIFY_SSL`.
4. Revisar `data/openemr_tokens.json`.
5. Revisar `/admin/openemr/token/status`.
6. Si el token expiró, probar OAuth nuevamente desde `/admin/openemr/oauth/start`.

---

## 27. Prueba operativa: paciente nuevo

Usar:

```text
Ruta: /nuevo
```

Datos de prueba sugeridos:

```text
Nombres: Juan Carlos
Apellidos: Pérez López
Fecha nacimiento: 2015-05-10
CI/documento: vacío o dato de prueba
Celular: 70707070
Sexo: Male
Profesional: cualquiera de la lista
Menor de edad: Sí
Madre: Ana María
Motivo de consulta: Consulta Inicial
```

Resultado esperado:

```text
/nuevo
↓
/confirmar
↓
confirmar
↓
paciente creado en OpenEMR
↓
encounter creado en OpenEMR
↓
/exito
```

Luego revisar:

```text
/admin/logs
```

Debe existir evento parecido a:

```text
new_patient_created_with_encounter
```

---

## 28. Prueba operativa: paciente antiguo

Usar:

```text
Ruta: /antiguo
```

Datos de prueba:

```text
Nombre: nombre existente en OpenEMR
Teléfono: teléfono correcto si se conoce
Profesional: cualquiera de la lista
Motivo de consulta: Sesión
```

Resultado esperado si hay un único paciente coincidente:

```text
/antiguo
↓
/confirmar-antiguo
↓
confirmar
↓
encounter creado en OpenEMR
↓
/exito
```

Luego revisar:

```text
/admin/logs
```

Debe existir evento parecido a:

```text
existing_patient_encounter_created
```

Si hay cero o múltiples coincidencias, el sistema debe bloquear el flujo y pedir ayuda en recepción.


## 29. Observación crítica: no eliminar pacientes de prueba durante validaciones

Durante las pruebas del kiosko se observó un comportamiento importante de OpenEMR:

Si se elimina un paciente desde la interfaz de OpenEMR y luego se registra un nuevo paciente desde el kiosko, OpenEMR puede reutilizar el mismo `pid`.

En la prueba realizada:

```text
PID original: 41
Paciente original: Jheremy Valencia
Encounter asociado: 84 - Consulta Inicial
```

Luego de eliminar ese paciente desde OpenEMR y registrar un nuevo paciente desde el kiosko:

```text
Nuevo paciente: James Jameson
PID asignado: 41
```

OpenEMR reutilizó el mismo `pid = 41`.

El encounter anterior permaneció asociado a ese `pid` en `form_encounter`, por lo que el nuevo paciente puede heredar visualmente encounters del paciente eliminado.

Conclusión operativa:

```text
No eliminar pacientes de prueba desde OpenEMR durante validaciones del kiosko.
```

Para pruebas funcionales, usar una convención de nombres/apellidos identificables y conservar esos registros hasta terminar la validación.

Ejemplo recomendado:

```text
Nombre: Prueba Uno
Apellido: TESTKIOSKO
```

o:

```text
Apellido: KIOSKO_TEST
```

Esto permite filtrar fácilmente los pacientes de prueba sin contaminar relaciones internas por reutilización de `pid`.

### Comportamiento actual del kiosko ante este caso

El kiosko tiene una protección para no duplicar `Consulta Inicial` si detecta que el paciente devuelto por OpenEMR ya tiene una consulta inicial creada el mismo día.

Evento esperado en logs si se detecta esa condición:

```text
new_patient_initial_encounter_already_exists
```

Esto significa:

```text
El kiosko no creó un nuevo encounter inicial porque OpenEMR ya mostraba una Consulta Inicial para ese pid en la fecha actual.
```

También puede aparecer:

```text
new_patient_initial_encounter_precheck_error
```

Esto significa:

```text
OpenEMR respondió error al consultar encounters existentes, normalmente HTTP 404 con data vacía cuando el paciente todavía no tiene encounters.
```

Este evento no es fatal. En ese caso, el kiosko continúa y crea el encounter inicial.

### Verificación SQL útil

Ver últimos pacientes creados:

```bash
sudo mysql openemr -e "
SELECT pid, pubpid, fname, lname, DOB, date, regdate
FROM patient_data
ORDER BY pid DESC
LIMIT 5;
"
```

Ver encounters de un paciente:

```bash
sudo mysql openemr -e "
SELECT
  fe.pid,
  fe.encounter,
  fe.date,
  fe.reason,
  fe.provider_id,
  CONCAT(u.fname, ' ', u.lname) AS provider_name,
  fe.pc_catid,
  c.pc_catname
FROM form_encounter fe
LEFT JOIN users u
  ON u.id = fe.provider_id
LEFT JOIN openemr_postcalendar_categories c
  ON c.pc_catid = fe.pc_catid
WHERE fe.pid = PID_AQUI
ORDER BY fe.encounter ASC;
"
```

Reemplazar:

```text
PID_AQUI
```

por el número real del paciente.

### Regla de pruebas

Para validar el kiosko:

```text
Crear pacientes nuevos únicos.
No eliminarlos durante la tanda de pruebas.
Usar apellido TESTKIOSKO o KIOSKO_TEST.
Revisar encounters por SQL o desde Visit History.
```

---

## 29. Probar renovación real de token

Pendiente inmediato recomendado.

Objetivo:

Confirmar que `OpenEMRService` puede renovar el `access_token` usando el `refresh_token` guardado en:

```text
data/openemr_tokens.json
```

Validación mínima:

1. Confirmar que existe token store:

```bash
ls -lah data/openemr_tokens.json
```

2. Ver estado público del token:

```text
http://100.124.189.84:5000/admin/openemr/token/status
```

3. Confirmar que muestra:

```text
refresh_token_present: true
```

4. Esperar a que expire el access token o forzar expiración en desarrollo.

5. Ejecutar una acción que consuma la API de OpenEMR, por ejemplo:

```text
http://100.124.189.84:5000/health/openemr
```

6. Resultado esperado:

```text
- Flask detecta access token vencido
- usa refresh token
- obtiene nuevo access token
- actualiza data/openemr_tokens.json
- la llamada a OpenEMR funciona
```

Si falla, registrar:

```text
HTTP status
response body
endpoint usado
client_id presente o no
refresh_token_present
scope
```

No pegar tokens reales.

---

## 30. Reset controlado de OAuth local

Usar solo si el token store quedó corrupto, vencido o inconsistente.

1. Detener Flask:

```text
Ctrl + C
```

2. Respaldar token actual:

```bash
cp data/openemr_tokens.json data/openemr_tokens.backup.json
```

3. Borrar token store activo:

```bash
rm -f data/openemr_tokens.json
```

4. Iniciar Flask:

```bash
python app.py
```

5. Abrir:

```text
http://100.124.189.84:5000/admin/openemr/oauth/start
```

6. Autorizar en OpenEMR.

7. Verificar:

```text
http://100.124.189.84:5000/admin/openemr/token/status
```

Debe mostrar:

```text
refresh_token_present: true
```

---

## 31. Revisión de logs

Panel web:

```text
http://100.124.189.84:5000/admin/logs
```

Base SQLite:

```bash
sqlite3 data/kiosk.db
```

Ejemplo para listar eventos recientes:

```sql
SELECT id, created_at, event_type, flow_type, status, message
FROM kiosk_events
ORDER BY id DESC
LIMIT 20;
```

Salir de SQLite:

```sql
.quit
```

---

## 32. Git - revisar cambios

Ver estado:

```bash
git status
```

Ver diferencias:

```bash
git diff
```

Agregar cambios:

```bash
git add .
```

Commit:

```bash
git commit -m "Actualizar documentacion de operacion local"
```

Subir a GitHub:

```bash
git push origin flask-mvp
```

---

## 33. Actualizar código desde GitHub

Entrar al proyecto:

```bash
cd /opt/openemr-kiosk
```

Verificar rama:

```bash
git branch
```

Actualizar:

```bash
git pull origin flask-mvp
```

Si hay conflictos, no resolver a ciegas. Revisar archivo por archivo.

---

## 34. Archivos que no deben subirse

No subir nunca:

```text
.env
data/openemr_tokens.json
data/kiosk.db
*.db
*.sqlite
*.sqlite3
.venv/
__pycache__/
legacy_php/admin/.htpasswd
```

También evitar subir:

```text
access_token
refresh_token
client_secret
Gemini API key
contraseñas reales
datos personales completos de pacientes
```

Verificar siempre con:

```bash
git status
```

---

## 35. Errores comunes

### Error: Flask no inicia por puerto ocupado

Ver proceso:

```bash
sudo ss -ltnp | grep :5000
```

Liberar puerto:

```bash
sudo fuser -k 5000/tcp
```

Reiniciar:

```bash
python app.py
```

---

### Error: `invalid_client`

Causas comunes:

- `OPENEMR_CLIENT_ID` incorrecto.
- `OPENEMR_CLIENT_SECRET` incorrecto.
- `client_secret` copiado incompleto.
- `.env` no fue recargado.
- Flask no fue reiniciado.
- `OPENEMR_BASE_URL` usa `http` en vez de `https`.

Verificar configuración sin imprimir secretos completos:

```bash
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
print("TOKEN_FILE:", Config.OPENEMR_TOKEN_FILE)
print("VERIFY_SSL:", Config.OPENEMR_VERIFY_SSL)
PY
```

---

### Error: `redirect_uri mismatch`

Causas comunes:

- El redirect URI del `.env` no coincide con el registrado.
- Diferencia entre `http` y `https`.
- Diferencia de puerto.
- IP distinta.
- Slash final extra.

Verificar que `.env` tenga exactamente:

```env
OPENEMR_OAUTH_REDIRECT_URI=http://100.124.189.84:5000/admin/openemr/oauth/callback
```

Y que el cliente OAuth en OpenEMR tenga exactamente el mismo redirect URI.

---

### Error: `invalid_scope`

Causas comunes:

- Se pidió un scope no válido.
- Se mezclaron scopes FHIR con Standard API.
- Se agregó manualmente `site:default`.

Scopes correctos actuales:

```text
openid offline_access api:oemr user/patient.read user/patient.write user/encounter.read user/encounter.write user/practitioner.read user/facility.read user/user.read
```

No agregar `site:default`.

---

### Error: `system and user scopes are only allowed for confidential clients`

Causa:

El cliente no fue registrado como privado/confidencial.

Solución:

Registrar mediante Dynamic Client Registration usando:

```json
"application_type": "private"
```

---

### Error: OpenEMR OAuth falla usando HTTP

OpenEMR debe usarse por HTTPS:

```text
https://100.124.189.84
```

Flask dev server sí usa HTTP:

```text
http://100.124.189.84:5000
```

Configuración correcta:

```env
OPENEMR_BASE_URL=https://100.124.189.84
OPENEMR_OAUTH_REDIRECT_URI=http://100.124.189.84:5000/admin/openemr/oauth/callback
```

---

### Error: no se pudo crear encounter

Revisar variables:

```env
OPENEMR_DEFAULT_FACILITY
OPENEMR_DEFAULT_PC_CATID
OPENEMR_DEFAULT_FACILITY_ID
OPENEMR_DEFAULT_BILLING_FACILITY
OPENEMR_DEFAULT_PROVIDER_ID
OPENEMR_DEFAULT_POS_CODE
OPENEMR_DEFAULT_CLASS_CODE
OPENEMR_DEFAULT_SENSITIVITY
```

También revisar:

```text
docs/openemr_api_notes.md
```

y probar lectura de encounters:

```text
/admin/openemr/patients/{uuid}/encounters
```

---

## 36. Pendientes inmediatos

Pendientes actuales recomendados:

```text
1. Probar renovación real de token con refresh_token.
2. Confirmar comportamiento después de reiniciar Flask.
3. Confirmar comportamiento después de reiniciar el servidor.
4. Completar pruebas pendientes de paciente nuevo con datos incompletos.
5. Completar prueba de error/timeout de Gemini.
6. Preparar despliegue local estable sin Flask debug server.
7. Configurar Gunicorn o systemd.
8. Definir acceso final desde tablet en LAN.
9. Documentar procedimiento de recuperación.
```

---

## 37. Despliegue local estable pendiente

Todavía no usar Flask debug server como operación final.

Opciones futuras:

```text
Gunicorn
systemd
Apache reverse proxy
restricción por LAN/Tailscale
HTTPS local si corresponde
```

Orden recomendado:

```text
1. Validar refresh token real.
2. Congelar variables `.env`.
3. Crear servicio systemd o Gunicorn.
4. Probar reinicio automático.
5. Probar acceso desde tablet.
6. Revisar logs.
7. Documentar recuperación.
```

---

## 38. Regla de oro del proyecto

No inventar endpoints, scopes ni payloads de OpenEMR.

Antes de cambiar integración API:

1. Verificar Swagger real:

```text
https://100.124.189.84/swagger/
```

2. Documentar hallazgo en:

```text
docs/openemr_api_notes.md
```

3. Probar con ruta admin o dry-run cuando sea posible.
4. Recién después conectar al flujo del kiosko.

---

## 39. Resumen operativo corto

Para levantar el kiosko:

```bash
cd /opt/openemr-kiosk
source .venv/bin/activate
git checkout flask-mvp
python app.py
```

Abrir:

```text
http://100.124.189.84:5000
```

Ver salud:

```text
http://100.124.189.84:5000/health
```

Ver logs:

```text
http://100.124.189.84:5000/admin/logs
```

Ver token:

```text
http://100.124.189.84:5000/admin/openemr/token/status
```

Renovar OAuth manualmente si hace falta:

```text
http://100.124.189.84:5000/admin/openemr/oauth/start
```