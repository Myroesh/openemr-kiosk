# TODO - OpenEMR Kiosk / Portal de Recepción

Centro Neuropsicológico Saavedra  
Backend Flask + Gemini Flash + API OpenEMR

Última actualización base: 2026-05-22  
Rama de trabajo: `flask-mvp`  
Fuente inicial: `plan_accion_openemr_kiosk.docx`  
Archivo: `docs/todo.md`

---

## Cómo usar este documento

Este archivo es la hoja de ruta viva del proyecto.

Convención de estado:

- `[ ]` pendiente
- `[~]` en curso
- `[x]` completado
- `[!]` bloqueado o requiere decisión

Reglas de trabajo:

- No inventar endpoints de OpenEMR.
- Primero verificar Swagger/API en la instalación real.
- La IA puede conversar, interpretar y normalizar datos.
- La IA no debe escribir directamente en OpenEMR.
- No se crea paciente ni encounter sin resumen y confirmación final.
- OpenEMR sigue siendo la fuente clínica principal.
- Flask maneja el flujo operativo del kiosko y del portal.

---

# 1. Estado actual del MVP

## 1.1 Base técnica confirmada

- [x] Usar Gemini Flash como modelo IA, Flask como backend y VS Code Remote SSH para desarrollo.
- [x] Kiosko anterior encontrado en `/var/www/html/openemr/kiosko`.
- [x] Contenido copiado a `/opt/openemr-kiosk`.
- [x] Servidor autenticado correctamente con GitHub como `Myroesh`.
- [x] Repositorio `Myroesh/openemr-kiosk` creado y accesible.
- [x] Rama `flask-mvp` creada y publicada.
- [x] PHP anterior movido a `legacy_php/` como referencia.
- [x] Base Flask inicial creada: `app.py`, `templates`, `static`, `services`, `requirements.txt`.
- [x] Flask responde por HTTP explícito en puerto `5000`.
- [x] `GEMINI_API_KEY` configurada en `.env` local.
- [x] `/health/gemini` responde OK con `gemini-2.5-flash`.

---

## 1.2 OpenEMR API / OAuth confirmado

- [x] Confirmar versión exacta de OpenEMR.
  - Confirmado: OpenEMR 7.0.2.

- [x] Confirmar API activa en OpenEMR.
  - Confirmado: Standard REST API y FHIR REST API activas.

- [x] Confirmar Site Address correcto.
  - Confirmado: `https://100.124.189.84`.

- [x] Entrar al Swagger correcto de esta instalación.
  - Confirmado: `https://100.124.189.84/swagger/`.

- [x] Identificar endpoint real para buscar paciente.
  - Confirmado: `GET /apis/default/api/patient`.

- [x] Identificar endpoint real para crear paciente.
  - Confirmado: `POST /apis/default/api/patient`.

- [x] Identificar endpoint real para crear encounter.
  - Confirmado: `POST /apis/default/api/patient/{puuid}/encounter`.

- [x] Guardar notas de endpoints verificados en `docs/openemr_api_notes.md`.

- [x] Definir método OAuth2 correcto para la instalación real.
  - Confirmado: OAuth2/OpenID Connect funcional por HTTPS con cliente Standard API.

- [x] Crear cliente API.
  - Confirmado: cliente `OpenEMR Kiosk Flask Standard API` creado y habilitado para Swagger.
  - Confirmado: cliente `OpenEMR Kiosk Flask OAuth` creado y habilitado para Flask OAuth.
  - Método correcto: registro dinámico vía `POST /oauth2/default/registration`.
  - Campo crítico confirmado: `"application_type": "private"`.

- [x] Guardar credenciales solo en `.env` local.
  - No guardar `client_id`, `client_secret`, access tokens, refresh tokens ni claves reales en GitHub.

- [x] Probar llamada simple autenticada sin crear datos.
  - Confirmado: `GET /apis/default/api/patient` respondió correctamente.

- [x] Manejar expiración/renovación de token.
  - Confirmado: tokens se guardan en `data/openemr_tokens.json`.
  - Confirmado: `/admin/openemr/token/status` muestra estado sin exponer tokens completos.
  - Confirmado: `/admin/openemr/token/save-manual` permite cargar access token temporal.
  - Confirmado: `/admin/openemr/oauth/start` y `/admin/openemr/oauth/callback` completan OAuth desde Flask.
  - Confirmado: `refresh_token_present: true`.
  - Confirmado: `OpenEMRService` lee tokens desde JSON y puede renovar usando refresh token.
  - Confirmado: renovación real probada forzando expiración local del token.
  - Confirmado: después de renovar, `data/openemr_tokens.json` quedó con `source: refresh_token`.
  - Confirmado: `/health/openemr` respondió `status: ok` después de renovar.

---

## 1.3 Flujo de paciente nuevo confirmado

- [x] Crear ruta `/nuevo` con formulario inicial de paciente nuevo.
- [x] Validar nombres y apellidos obligatorios.
- [x] Validar fecha de nacimiento y edad coherente.
- [x] Validar CI/documento si se solicita.
- [x] Validar teléfono boliviano o formato aceptado por el centro.
- [x] Validar motivo de consulta no vacío.
- [x] Usar catálogo cerrado para motivo de consulta.
  - Opciones:
    - Consulta Inicial
    - Sesión
    - Revisión de resultados
    - Test
    - Entrevista con los padres
  - Valor por defecto: `Sesión`.

- [x] Automatizar detección de menor de edad.
  - El frontend calcula la edad desde `fecha_nacimiento`.
  - El backend recalcula `es_menor` desde `fecha_nacimiento`.
  - No depende del valor enviado por JavaScript.

- [x] Exigir datos mínimos de guardian para menores de edad.
  - Si el paciente es menor de edad, el backend exige al menos nombre del padre o nombre de la madre.
  - Teléfonos de padre/madre son opcionales, pero si se llenan se validan como celulares bolivianos.
  - CI de padre/madre es opcional, pero se valida si se llena.

- [x] Mapear datos de padre/madre a campos guardian de OpenEMR.
  - OpenEMR acepta `guardiansname`, `guardianrelationship` y `guardianphone`.
  - Los datos aparecen visualmente en Demographics → Guardian.
  - Decisión: no usar `mothersname` por ahora para evitar duplicidad visual.

- [x] Buscar duplicados antes de crear.
  - `/nuevo` consulta OpenEMR con `OpenEMRService.search_patients()` antes de permitir confirmación.

- [x] Mostrar resumen final obligatorio antes de guardar.
  - Implementado en `/confirmar`.

- [x] Crear paciente en OpenEMR solo tras confirmación.
  - `/confirmar` crea paciente real usando `OpenEMRService.create_patient()`.

- [x] Crear encounter inicial después del paciente nuevo.
  - Decisión: el kiosko actúa como recepción, por lo tanto crea encounter inicial después de registrar al paciente nuevo.

- [x] Registrar resultado en logs.
  - Confirmado: eventos `pending_confirmation` y `patient_intake_created`.

- [x] Mostrar pantalla final `/exito`.
  - Mensaje: “Registro completado, espere a ser llamado”.

---

## 1.4 Flujo de paciente antiguo confirmado

- [x] Crear ruta `/antiguo`.
- [x] Pedir CI/documento, teléfono, nombre o dato disponible.
- [x] Buscar paciente en OpenEMR.
  - Confirmado: `/antiguo` busca paciente real mediante `OpenEMRService.search_patients()`.

- [x] Mostrar confirmación básica de identidad.
  - Confirmado: `/confirmar-antiguo` muestra el paciente encontrado en OpenEMR antes de continuar.

- [x] Usar catálogo cerrado para motivo de consulta.
  - Confirmado: `/antiguo` usa dropdown.
  - Valor por defecto: `Sesión`.
  - Backend valida contra catálogo permitido.

- [x] Crear encounter para la fecha actual.
  - Confirmado: `/confirmar-antiguo` crea encounter en OpenEMR después de confirmar paciente antiguo.

- [x] Preparar lectura/escritura controlada de encounters desde Flask.
  - Confirmado: `OpenEMRService.get_patient_encounters()`.
  - Confirmado: `OpenEMRService.create_encounter_for_patient()`.
  - Confirmado: ruta admin protegida para leer encounters por paciente.
  - Confirmado: ruta admin de prueba con dry-run.
  - Confirmado: payload de Swagger validado.
  - Confirmado: encounter de prueba creado correctamente en OpenEMR.

- [x] Registrar resultado en logs.
- [x] Mostrar pantalla final.

---

## 1.5 Logs y base local confirmados

- [x] Definir SQLite local para logs del MVP.
  - Decisión: usar SQLite local para logs y registros temporales del kiosko.

- [x] Crear tabla `kiosk_events`.
  - Confirmado en `services/db_service.py`.
  - Campos confirmados:
    - `created_at`
    - `event_type`
    - `flow_type`
    - `status`
    - `message`
    - `intake_id`
    - `metadata_json`

- [x] Registrar fecha/hora, flujo, estado, mensaje de error y datos mínimos no sensibles.
  - Confirmado en `create_kiosk_event()`.

- [x] Crear panel `/admin/logs` protegido de forma simple para revisión interna.
  - Confirmado en `app.py`.
  - Usa `@admin_auth_required`.

- [ ] Evitar almacenar más datos clínicos de los necesarios en logs.

---

## 1.6 Gemini Flash confirmado

- [x] Definir prompts estrictos para extraer solo el campo actual.
  - Confirmado: `GeminiService.classify_consultation_reason()` usa prompt estricto para clasificar solo `motivo_consulta`.

- [x] Hacer que Gemini devuelva JSON estructurado o resultado controlado.
  - Confirmado: la respuesta se parsea como JSON y se valida contra campos esperados.
  - Si devuelve markdown JSON, el servicio lo limpia antes de parsear.

- [x] Limitar `motivo_consulta` a catálogo cerrado también cuando se use Gemini.
  - Confirmado: Gemini solo puede devolver valores dentro de `ALLOWED_CONSULTATION_REASONS`.

- [x] Evitar que Gemini cree acciones directas en OpenEMR.
  - Confirmado: `GeminiService` no importa ni llama `OpenEMRService`.

- [x] Registrar errores de IA sin exponer datos sensibles.

- [~] Agregar fallback si Gemini falla.
  - Confirmado: `classify_consultation_reason()` usa fallback seguro a `Sesión`.
  - Pendiente: integrar fallback formal al flujo conversacional cuando exista UI conversacional.

---

# 2. Pendientes técnicos inmediatos

## 2.1 Estabilización local

- [ ] No usar Flask debug server para producción.
- [ ] Configurar Gunicorn o servicio systemd.
- [ ] Definir puerto interno o proxy por Apache.
- [ ] Restringir acceso a red local/Tailscale.
- [ ] Definir si se requiere HTTPS en LAN.
- [ ] Crear procedimiento de reinicio y revisión de logs.
- [ ] Verificar comportamiento estable después de reiniciar Flask.
- [ ] Verificar comportamiento estable después de reiniciar servidor.
- [ ] Documentar comandos de arranque y operación local.

---

## 2.2 Documentación operativa

- [x] Documentar cómo iniciar/detener el kiosko.
- [x] Documentar cómo revisar logs.
- [x] Documentar cómo actualizar código desde GitHub.
- [x] Documentar qué hacer si OpenEMR API falla.
- [x] Documentar qué hacer si Gemini falla.
- [x] Documentar observación operativa sobre eliminación de pacientes de prueba y reutilización de `pid` en OpenEMR.
- [ ] Actualizar `docs/OPERACION_LOCAL.md` con el estado actual completo.
- [ ] Crear checklist de uso para el personal del centro.

---

## 2.3 Pruebas pendientes del flujo actual

- [x] Probar paciente nuevo con datos válidos.
  - Confirmado: paciente nuevo se crea en OpenEMR y se crea encounter inicial.

- [ ] Probar paciente nuevo con datos incompletos.

- [x] Probar duplicado por datos similares.
  - Confirmado: el flujo bloquea creación si encuentra paciente registrado con datos similares.

- [x] Probar paciente antiguo no encontrado.
  - Confirmado previamente: muestra mensaje y pide ayuda en recepción.

- [x] Probar error de OpenEMR API.
  - Confirmado previamente con token vencido: el flujo bloquea avance y muestra error seguro.

- [ ] Probar error de Gemini o timeout.

- [x] Confirmar que no se crean datos sin confirmación.
  - Confirmado: creación de paciente y encounters ocurre después de pantalla de confirmación.

- [x] Probar caso de eliminación de paciente de prueba en OpenEMR y reutilización de PID.
  - Confirmado: al eliminar un paciente desde OpenEMR y crear uno nuevo desde el kiosko, OpenEMR puede reutilizar el mismo `pid`.
  - Confirmado: los encounters previos asociados a ese `pid` pueden seguir visibles para el nuevo paciente.
  - Conclusión: este comportamiento pertenece a OpenEMR/operación de pruebas, no al flujo normal del kiosko.
  - Acción: documentado en `docs/OPERACION_LOCAL.md`.

- [x] Probar que el kiosko no duplique `Consulta Inicial` cuando OpenEMR devuelve un paciente con encounter inicial existente.
  - Confirmado: el kiosko registra `new_patient_initial_encounter_already_exists` y no crea otro encounter inicial.

---

# 3. Portal de doctores - MVP

## 3.1 Objetivo

Crear una vista simple para que cada profesional pueda ver:

- su paciente siguiente;
- sus pacientes pendientes del día;
- sus pacientes en atención;
- sus pacientes atendidos de acuerdo a una fecha;
- un acceso rápido al paciente o encounter correspondiente en OpenEMR.

Este portal no reemplaza OpenEMR.  
Solo organiza el flujo operativo de atención.

---

## 3.2 Principio de diseño

OpenEMR mantiene la información clínica principal.

La aplicación Flask mantiene una cola operativa local para recepción y doctores.

La cola local debe registrar cada paciente/encounter creado desde el kiosko para que luego el doctor pueda verlo como pendiente, en atención o atendido.

---

## 3.3 Modelo operativo propuesto

Estados del flujo:

- `pending`: paciente registrado y pendiente de atención.
- `in_progress`: paciente actualmente en atención.
- `completed`: paciente atendido.
- `cancelled`: registro cancelado.
- `no_show`: paciente no se presentó o abandonó el flujo.
- `error`: registro con error operativo.

Regla inicial del MVP:

- El paciente siguiente se calcula por orden de llegada.
- La cola se filtra por fecha.
- Idealmente la cola se filtra por doctor/profesional asignado.
- Si todavía no existe asignación real por agenda, se puede usar selección manual de doctor en el flujo del kiosko.

---

## 3.4 Tabla local propuesta: `patient_queue`

- [x] Crear tabla local `patient_queue` para registrar el flujo operativo de atención.

Campos implementados:

- `id`
- `created_at`
- `queue_date`
- `openemr_pid`
- `openemr_puuid`
- `openemr_encounter_id`
- `patient_name`
- `doctor_id`
- `doctor_name`
- `visit_reason`
- `status`
- `started_at`
- `finished_at`
- `metadata_json`

Notas:

- `openemr_pid`: útil para referencia rápida.
- `openemr_puuid`: útil para API si corresponde.
- `openemr_encounter_id`: necesario para enlazar el encounter creado.
- `patient_name`: nombre visible del paciente en la cola.
- `doctor_id`: por ahora se obtiene desde `OPENEMR_PROVIDER_ID_MAP` cuando existe.
- `doctor_name`: nombre del profesional seleccionado en el formulario.
- `visit_reason`: motivo de consulta usando el catálogo cerrado ya existente.
- `status`: puede ser `pending`, `in_progress`, `completed`, `cancelled`, `no_show` o `error`.
- `queue_date`: fecha operativa para filtros diarios.
- `created_at`: fecha/hora de ingreso a la cola.
- `started_at`: fecha/hora en que el doctor marca “en atención”.
- `finished_at`: fecha/hora en que el doctor marca “atendido”.
- `metadata_json`: solo datos mínimos no sensibles.

Implementado en:

- `services/db_service.py`
- `init_db()`
- `create_patient_queue_entry()`
- `list_patient_queue_by_date()`
- `list_patient_queue_by_status()`
- `get_next_patient_for_doctor()`
- `update_patient_queue_status()`

---

## 3.5 Integración con flujo actual del kiosko

- [x] Guardar en `patient_queue` cada paciente nuevo que complete `/nuevo` → `/confirmar`.
- [x] Guardar en `patient_queue` cada paciente antiguo que complete `/antiguo` → `/confirmar-antiguo`.
- [x] Registrar `openemr_pid`, `openemr_puuid` y `openemr_encounter_id` cuando estén disponibles.
- [x] Registrar `visit_reason` usando el catálogo cerrado ya existente.
- [x] Registrar fecha/hora de llegada.
- [x] Registrar estado inicial como `pending`.
- [x] Evitar duplicar entradas en `patient_queue` si el encounter ya existe.
- [x] Registrar evento en `kiosk_events` cuando se agregue un paciente a la cola.

Implementado en:

- `app.py`
- `get_queue_doctor_identity()`
- `build_new_patient_queue_name()`
- `build_existing_patient_queue_name()`
- evento `patient_queue_entry_created`

Prueba realizada:

- Paciente de prueba `Ramiro Portal Prueba` fue creado desde el flujo del kiosko.
- El encounter generado en OpenEMR fue registrado en `patient_queue`.
- Estado inicial confirmado: `pending`.

---

## 3.6 Asignación de doctor/profesional

MVP recomendado:

- [x] Agregar campo de doctor/profesional asignado al flujo de registro.
- [x] Usar lista cerrada de doctores/profesionales.
- [x] Guardar `doctor_id` y `doctor_name` en `patient_queue`.

Opciones iniciales configuradas:

- Dra. Ana Saavedra
- Dra. Evelyn Mejia Patiño
- Dra. Katherine Oliveira
- Dr. Jose Montaño
- Dr. Hernan Hinojosa

Pendiente:

- [ ] Verificar desde OpenEMR qué endpoint o dato real conviene usar para listar usuarios/profesionales.
- [ ] Confirmar si se usará provider de OpenEMR o una lista local temporal.
- [ ] No inventar IDs de provider sin verificar en OpenEMR.
- [ ] Revisar si el filtro definitivo debe usar `doctor_name`, `doctor_id` o ambos.

---

## 3.7 Rutas Flask propuestas

- [x] Crear vista principal del portal médico: `GET /doctor/dashboard`.
- [x] Crear filtro por fecha: `GET /doctor/dashboard?date=YYYY-MM-DD`.
- [x] Crear filtro por doctor: `GET /doctor/dashboard?doctor=Nombre%20Profesional`.
- [x] Crear acción para marcar paciente como en atención: `POST /doctor/queue/<id>/start`.
- [x] Crear acción para marcar paciente como atendido: `POST /doctor/queue/<id>/complete`.
- [x] Crear acción para cancelar o retirar de cola: `POST /doctor/queue/<id>/cancel`.
- [~] Crear historial por fecha: `GET /doctor/history?date=YYYY-MM-DD`.

Nota:

- El historial por fecha ya existe funcionalmente dentro de `/doctor/dashboard` mediante el filtro de fecha y la sección “Atendidos”.
- Queda pendiente decidir si se necesita una ruta separada `/doctor/history`.

---

## 3.8 Vista `/doctor/dashboard`

La pantalla debe mostrar:

- [x] Nombre del doctor seleccionado.
- [x] Fecha actual.
- [x] Paciente siguiente.
- [x] Lista de pacientes pendientes.
- [x] Lista de pacientes en atención.
- [x] Lista de pacientes atendidos del día.
- [x] Filtro por fecha.
- [x] Filtro por doctor si todavía no hay login.
- [x] Botón “Marcar como en atención”.
- [x] Botón “Marcar como atendido”.
- [x] Botón visible para cancelar o retirar paciente de cola.
- [x] Link para abrir OpenEMR completo desde el portal.
- [x] Mensaje claro si no hay pacientes pendientes.

Implementado en:

- `templates/doctor_dashboard.html`
- `static/css/style.css`

Nota:

- El enlace a OpenEMR abre el entorno principal de OpenEMR.
- No se usa deep link directo al paciente porque OpenEMR maneja `token_main` dinámico y sesión propia.

---

## 3.9 Vista sugerida

Portal médico

Doctor: Dra. Evelyn Mejia Patiño  
Fecha: 2026-05-22

Paciente siguiente:

- María López
- Hora de registro: 09:35
- Motivo: Consulta Inicial
- Estado: Pendiente

Acciones:

- Marcar como en atención
- Abrir en OpenEMR

Pendientes:

- 09:35 - María López - Consulta Inicial
- 10:05 - Juan Vargas - Sesión
- 10:20 - Ana Rojas - Test

En atención:

- 09:10 - Pedro Flores - Revisión de resultados

Atendidos:

- 08:30 - Carla Méndez - Sesión
- 09:00 - Luis Rojas - Entrevista con los padres

Nota:

- La primera versión funcional ya fue implementada en `/doctor/dashboard`.
- Quedan pendientes refinamientos visuales y operativos.

---

## 3.10 Criterios de aceptación del portal médico

- [x] El doctor puede ver pacientes asignados a él mediante filtro por profesional.
- [x] El paciente siguiente se calcula por orden de llegada.
- [x] El portal muestra pacientes pendientes del día.
- [x] El portal muestra pacientes en atención.
- [x] El portal muestra pacientes atendidos del día.
- [x] El historial diario muestra pacientes marcados como atendidos mediante el filtro por fecha.
- [x] El filtro por fecha funciona correctamente.
- [x] El sistema no reemplaza las notas clínicas de OpenEMR.
- [x] OpenEMR sigue siendo la fuente principal para información clínica.
- [x] El portal no permite editar datos clínicos.
- [x] El portal no expone tokens, secretos ni datos innecesarios.
- [x] El portal debe quedar protegido con autenticación básica o mecanismo equivalente.
- [x] El portal debe mostrar horas en formato más legible para usuarios finales.
- [x] El portal debe incluir link seguro hacia OpenEMR si se confirma URL útil.

Nota:

- La autenticación del portal médico usa credenciales separadas de `/admin/logs`.
- El enlace abre OpenEMR completo, no un paciente específico.

---

## 3.11 Pruebas necesarias del portal médico

- [x] Paciente nuevo desde kiosko aparece en portal doctor.
- [ ] Paciente antiguo desde kiosko aparece en portal doctor.
- [x] Paciente aparece con estado `pending`.
- [x] Doctor marca paciente como `in_progress`.
- [x] Doctor marca paciente como `completed`.
- [x] Paciente completado desaparece de pendientes.
- [x] Paciente completado aparece en historial por fecha.
- [x] Filtro por fecha funciona correctamente.
- [x] Filtro por doctor funciona correctamente.
- [x] Reiniciar Flask no borra la cola.
- [ ] Reiniciar servidor no borra la cola.
- [ ] Error de OpenEMR no rompe la vista del portal.
- [ ] Paciente sin doctor asignado se muestra en una sección clara: “Sin asignar”.
- [x] Se confirmó persistencia en SQLite usando `list_patient_queue_by_date()`.

Prueba funcional realizada:

- `Ramiro Portal Prueba` apareció en cola con estado `pending`.
- Se marcó como `in_progress`.
- Se registró `started_at`.
- Se marcó como `completed`.
- Se registró `finished_at`.

---

## 3.12 Refinamientos pendientes del portal médico

- [ ] Limpiar formato de `static/css/style.css` y asegurar newline final.
- [x] Proteger `/doctor/dashboard` y rutas `/doctor/queue/...` con autenticación básica o mecanismo equivalente.
- [x] Agregar botón visible “Cancelar” en pacientes pendientes y/o en atención.
- [x] Agregar enlace seguro para abrir OpenEMR completo.
- [x] Mejorar formato visual de fechas y horas.
- [ ] Eliminar registros de prueba de `patient_queue`, por ejemplo `Paciente Test`.
- [ ] Revisar si el filtro debe ser por `doctor_name`, `doctor_id` o ambos.
- [ ] Evaluar si se necesita ruta separada `/doctor/history`.

Nota:

- Se intentó usar enlace directo al dashboard del paciente, pero OpenEMR abre esa ruta fuera del shell principal.
- Se decidió usar enlace al OpenEMR completo para evitar dependencia de `token_main` dinámico.
- La persistencia de sesión se manejará con el timeout oficial de OpenEMR y configuración PHP, no con tokens o sesión permanente desde Flask.

## 3.13 Resumen de atenciones por profesional

Objetivo:

- Crear una vista operativa para revisar cuántos pacientes atendió cada profesional y cuánto tiempo tomó cada atención.
- Esta vista no reemplaza reportes clínicos de OpenEMR.
- La fuente de datos inicial será la tabla local `patient_queue`.

Vista propuesta:

- [ ] Crear ruta `GET /doctor/summary`.
- [ ] Proteger `/doctor/summary` con la misma autenticación del portal médico.
- [ ] Agregar filtros por fecha desde, fecha hasta y profesional.
- [ ] Mostrar resumen agrupado por profesional.
- [ ] Mostrar cantidad de pacientes atendidos por profesional.
- [ ] Mostrar tiempo promedio de atención por profesional.
- [ ] Mostrar tiempo total de atención por profesional.
- [ ] Mostrar primera atención y última atención del rango.
- [ ] Mostrar detalle de pacientes atendidos por profesional.
- [ ] Permitir volver desde `/doctor/summary` a `/doctor/dashboard`.

Datos necesarios:

- `doctor_id`
- `doctor_name`
- `patient_name`
- `visit_reason`
- `status`
- `started_at`
- `finished_at`
- `queue_date`

Reglas de cálculo:

- Solo cuentan como atenciones realizadas los registros con `status = completed`.
- La duración se calcula como `finished_at - started_at`.
- Si falta `started_at` o `finished_at`, el paciente cuenta como atendido, pero no entra al promedio de duración.
- Los registros `cancelled`, `no_show` y `error` no cuentan como atenciones realizadas.
- La vista debe mostrar claramente si existen registros completados sin tiempo calculable.

Métricas iniciales:

- Pacientes atendidos.
- Atenciones con duración válida.
- Tiempo promedio de atención.
- Tiempo total de atención.
- Primera atención.
- Última atención.

Implementación propuesta:

- Agregar helper en `services/db_service.py` para consultar pacientes completados por rango de fechas.
- Agregar helper en `app.py` para agrupar por profesional y calcular duración.
- Crear template `templates/doctor_summary.html`.
- Agregar enlace desde `/doctor/dashboard` hacia `/doctor/summary`.

---

# 4. Fases históricas del proyecto

## Fase 0 - Base del repositorio y entorno

- [x] Crear `/opt/openemr-kiosk` y copiar kiosko anterior.
- [x] Configurar Git/GitHub SSH en el servidor OpenEMR.
- [x] Crear repo `Myroesh/openemr-kiosk`.
- [x] Crear rama `flask-mvp`.
- [x] Mover PHP anterior a `legacy_php/`.
- [x] Crear estructura Flask base.
- [x] Probar `/health` por HTTP en puerto `5000`.
- [x] Actualizar `requirements.txt` en GitHub.
  - Evidencia base: `requirements.txt` confirmado con Flask, python-dotenv, requests, google-genai.
- [x] Confirmar `git status` limpio después del último push.
  - `.env` y `.htpasswd` fuera de Git.

---

## Fase 1 - Pantallas base del MVP sin OpenEMR ni IA

- [x] Actualizar pantalla inicial con botones reales: `/nuevo` y `/antiguo`.
- [x] Crear ruta `/nuevo` con formulario inicial de paciente nuevo.
- [x] Crear ruta `/antiguo` con búsqueda por CI/documento o teléfono.
- [x] Crear ruta `/confirmar` para mostrar resumen antes de guardar.
- [x] Crear ruta `/exito` con mensaje final.
- [~] Crear diseño responsive para tablet.
  - CSS responsive creado.
  - Falta ajustar/probar específicamente en tablet.
- [ ] Agregar logo y datos del centro sin depender de rutas internas de OpenEMR.

---

## Fase 2 - Base de datos local y logs del kiosko

- [x] Definir SQLite local para logs del MVP.
- [x] Crear tabla `kiosk_events`.
- [x] Registrar fecha/hora, flujo, estado, mensaje de error y datos mínimos no sensibles.
- [x] Crear panel `/admin/logs` protegido de forma simple para revisión interna.
- [ ] Evitar almacenar más datos clínicos de los necesarios en logs.

---

## Fase 3 - Descubrimiento real de API OpenEMR

- [x] Confirmar versión exacta de OpenEMR.
- [x] Confirmar API activa.
- [x] Confirmar Site Address correcto.
- [x] Confirmar si el servidor OpenEMR usa HTTP local o HTTPS.
- [x] Entrar al Swagger correcto.
- [x] Identificar endpoints reales para buscar paciente.
- [x] Identificar endpoint real para crear paciente.
- [x] Identificar endpoint real para crear encounter.
- [x] Identificar si necesitamos consultar usuarios/profesionales/facility.
- [x] Guardar notas de endpoints verificados en `docs/openemr_api_notes.md`.

---

## Fase 4 - Autenticación OpenEMR desde Flask

- [x] Definir método OAuth2 correcto.
- [x] Crear cliente API.
- [x] Guardar credenciales solo en `.env` local.
- [x] Probar llamada simple autenticada sin crear datos.
- [x] Manejar expiración/renovación de token.

---

## Fase 5 - Validaciones antes de OpenEMR

- [x] Validar nombres y apellidos obligatorios.
- [x] Validar fecha de nacimiento y edad coherente.
- [x] Validar CI/documento si se solicita.
- [x] Validar teléfono boliviano o formato aceptado por el centro.
- [x] Validar motivo de consulta no vacío.
- [x] Validar datos de tutor si es menor de edad.
- [~] Implementar normalización sin sobrescribir la respuesta original del paciente.
  - Hay normalización implementada.
  - Falta decidir si se conservará también la respuesta original cruda.
- [x] Crear resumen final obligatorio antes de guardar.

---

## Fase 6 - Integración Gemini Flash controlada

- [x] Definir prompts estrictos para extraer solo el campo actual.
- [x] Hacer que Gemini devuelva JSON estructurado o resultado controlado.
- [x] Limitar `motivo_consulta` a catálogo cerrado también cuando se use Gemini.
- [~] Agregar fallback si Gemini falla: formulario manual.
- [x] Evitar que Gemini cree acciones directas en OpenEMR.
- [x] Registrar errores de IA sin exponer datos sensibles.

---

## Fase 7 - Flujo paciente nuevo

- [x] Pedir datos mediante formulario guiado.
- [x] Automatizar detección de menor de edad en formulario de paciente nuevo.
- [x] Exigir datos mínimos de guardian para menores de edad.
- [x] Mapear datos de padre/madre a campos guardian de OpenEMR.
- [x] Probar guardianes con ruta admin controlada.
- [x] Probar guardianes desde flujo real del kiosko.
- [x] Buscar duplicados antes de crear.
- [x] Mostrar resumen final.
- [x] Crear paciente en OpenEMR solo tras confirmación.
- [x] Registrar resultado en logs.
- [x] Mostrar pantalla final.
- [x] Definir si también se crea encounter luego del paciente nuevo.
- [x] Usar catálogo cerrado para motivo de consulta.

---

## Fase 8 - Flujo paciente antiguo

- [x] Pedir CI/documento, teléfono, nombre o dato disponible.
- [x] Buscar paciente en OpenEMR.
- [x] Mostrar confirmación básica de identidad.
- [x] Usar catálogo cerrado para motivo de consulta.
- [x] Crear encounter para la fecha actual.
- [x] Preparar lectura/escritura controlada de encounters desde Flask.
- [x] Registrar resultado en logs.
- [x] Mostrar pantalla final.

---

## Fase 9 - Pruebas y control de errores

- [x] Probar paciente nuevo con datos válidos.
- [ ] Probar paciente nuevo con datos incompletos.
- [x] Probar duplicado por datos similares.
- [x] Probar paciente antiguo no encontrado.
- [x] Probar error de OpenEMR API.
- [ ] Probar error de Gemini o timeout.
- [x] Confirmar que no se crean datos sin confirmación.
- [x] Probar caso de eliminación de paciente de prueba en OpenEMR y reutilización de PID.
- [x] Probar que el kiosko no duplique `Consulta Inicial` cuando OpenEMR devuelve un paciente con encounter inicial existente.

---

## Fase 10 - Despliegue local estable

- [x] Probar comportamiento después de reiniciar el servidor.
  - Confirmado: servidor reinició correctamente.
  - Confirmado: OpenEMR siguió accesible después del reboot.
  - Confirmado: `data/openemr_tokens.json` persistió correctamente.
  - Confirmado: `/health/openemr` respondió `status: ok` después de levantar Flask manualmente.
  - Confirmado: token store conserva `source: refresh_token`.

- [ ] No usar Flask debug server para producción.
- [ ] Configurar Gunicorn o servicio systemd.
- [ ] Definir puerto interno o proxy por Apache.
- [ ] Restringir acceso a red local/Tailscale.
- [ ] Definir si se requiere HTTPS en LAN.
- [ ] Crear procedimiento de reinicio y revisión de logs.

---

## Fase 11 - Documentación operativa

- [x] Documentar cómo iniciar/detener el kiosko.
- [x] Documentar cómo revisar logs.
- [x] Documentar cómo actualizar código desde GitHub.
- [x] Documentar qué hacer si OpenEMR API falla.
- [x] Documentar qué hacer si Gemini falla.
- [x] Documentar observación operativa sobre eliminación de pacientes de prueba y reutilización de `pid` en OpenEMR.
- [ ] Crear checklist de uso para el personal del centro.

---

## Fase 12 - Portal de doctores


- [x] Crear tabla local `patient_queue`.
- [x] Conectar flujo de paciente nuevo con `patient_queue`.
- [x] Conectar flujo de paciente antiguo con `patient_queue`.
- [x] Agregar selección o asignación de doctor/profesional.
- [x] Crear ruta `/doctor/dashboard`.
- [x] Crear template `templates/doctor_dashboard.html`.
- [x] Mostrar paciente siguiente.
- [x] Mostrar pacientes pendientes.
- [x] Mostrar pacientes en atención.
- [x] Mostrar pacientes atendidos.
- [x] Agregar filtro por fecha.
- [x] Agregar filtro por doctor si todavía no hay login.
- [x] Agregar botón “Marcar como en atención”.
- [x] Agregar botón “Marcar como atendido”.
- [x] Agregar botón visible “Cancelar”.
- [x] Agregar link seguro hacia OpenEMR completo.
- [x] Registrar cambios de estado en `kiosk_events`.
- [x] Probar flujo completo kiosko → cola médico → atendido.
- [x] Crear vista de resumen de atenciones por profesional.
- [x] Calcular pacientes atendidos por profesional.
- [x] Calcular tiempo promedio y total de atención.
- [x] Mostrar detalle de pacientes atendidos por fecha.
- [x] Agregar enlace desde `/doctor/dashboard` hacia `/doctor/summary`.
- [x] Proteger `/doctor/summary` con la misma autenticación del portal médico.
- [x] Configurar arranque automático del kiosko con Gunicorn y `systemd`.

UX/UI del portal médico:

- [x] Primera pasada visual del portal médico.
- [x] Convertir links superiores en botones tipo navegación.
- [x] Mejorar apariencia de filtros.
- [x] Mejorar jerarquía visual de “Paciente siguiente”.
- [x] Mejorar cards de pacientes pendientes, en atención y atendidos.
- [x] Mejorar KPIs y tablas del resumen de atenciones.
- [ ] Probar visualmente `/doctor/dashboard` con datos reales de varios pacientes.
- [ ] Probar visualmente `/doctor/summary` con varios profesionales y rangos de fechas.
- [ ] Ajustar contraste, tamaños y espaciado si los doctores reportan dificultad de lectura.
- [ ] Revisar experiencia en tablet o pantalla chica.
- [ ] Evaluar separar CSS del portal médico en `static/css/doctor.css`.
- [ ] Asegurar newline final y limpieza de formato en `static/css/style.css`.
- [ ] Revisar si los botones “Cancelar” deben pedir confirmación antes de ejecutar.
- [ ] Evaluar indicador visual de actualización automática cada 5 segundos.
- [ ] Evaluar si conviene mostrar “última actualización” en el dashboard.
- [ ] Recoger feedback de doctores sobre nombres de botones: “En atención”, “Atendido”, “Cancelar”, “OpenEMR”.

Pendientes inmediatos:

- [ ] Probar paciente antiguo desde kiosko aparece en portal doctor.
- [ ] Probar reinicio completo del servidor y persistencia de cola.
- [ ] Probar comportamiento cuando OpenEMR tiene sesión expirada.
- [ ] Probar que el servicio `openemr-kiosk` levanta automáticamente al encender el servidor.
- [ ] Revisar logs de `systemd` con `journalctl -u openemr-kiosk -f` después de reinicio.
- [ ] Recoger feedback inicial de doctores usando el portal en operación real.

Nota:

- El objetivo inmediato del portal médico no es perfección visual, sino permitir uso real temprano para detectar requerimientos operativos.
- OpenEMR sigue siendo la fuente clínica principal.
- El portal médico solo maneja flujo operativo: cola, estado de atención y resumen local.
- Los cambios UX/UI deben hacerse en commits pequeños, sin mezclar con lógica crítica de OpenEMR.
---

# 5. Futuras mejoras

## 5.1 Portal médico

- [ ] Integrar agenda real de OpenEMR.
- [ ] Asignar doctor automáticamente según cita.
- [ ] Agregar login por doctor.
- [ ] Crear panel de recepción.
- [ ] Exportar historial diario a Excel o PDF.
- [ ] Mostrar tiempos de espera.
- [ ] Mostrar conteo diario por profesional.
- [ ] Agregar vista general para administración.

---

## 5.2 Kiosko / IA

- [ ] Integrar UI conversacional real sobre el flujo de formularios ya validado.
- [ ] Permitir fallback manual completo si Gemini falla.
- [ ] Evaluar voz más adelante.
- [ ] Mejorar experiencia en tablet.
- [ ] Agregar modo pantalla completa.
- [ ] Agregar mensajes más claros para pacientes.

---

## 5.3 Integraciones

- [ ] Revisar integración futura con agenda de OpenEMR.
- [ ] Revisar integración futura con recordatorios.
- [ ] Revisar integración futura con WhatsApp solo si el canal queda desbloqueado y estable.
- [ ] Evaluar reportes operativos por fecha/profesional.

---

# 6. Comandos útiles actuales

Comandos para iniciar la app:

- `cd /opt/openemr-kiosk`
- `source .venv/bin/activate`
- `python app.py`

Comandos Git habituales:

- `git status`
- `git add .`
- `git commit -m "mensaje"`
- `git push origin flask-mvp`

URLs de desarrollo:

- `http://100.124.189.84:5000`
- `http://100.124.189.84:5000/health`
- `http://100.124.189.84:5000/health/openemr`
- `http://100.124.189.84:5000/health/gemini`

Swagger OpenEMR:

- `https://100.124.189.84/swagger/`

---

# 7. Registro de decisiones

- 2026-05-15: Usar Gemini Flash como IA del kiosko.
- 2026-05-15: Usar Flask como backend.
- 2026-05-15: Desarrollar vía VS Code Remote SSH.
- 2026-05-15: No conectar tablet directamente a OpenEMR.
- 2026-05-15: Separar PHP anterior en `legacy_php/` y empezar Flask limpio.
- 2026-05-15: Usar HTTP en puerto `5000` solo para desarrollo; HTTPS se definirá después.
- 2026-05-15: Configurar `GEMINI_API_KEY` solo en `.env` local; no subir secretos al repositorio.
- 2026-05-15: Usar SQLite local para logs/registros temporales del MVP antes de integrar OpenEMR.
- 2026-05-15: Crear rutas base `/nuevo`, `/antiguo`, `/exito` y `/admin/logs` antes de conectar OpenEMR.
- 2026-05-22: Considerar concluida la versión inicial de formulario para uso de pacientes.
- 2026-05-22: Agregar como siguiente módulo el portal de doctores.
- 2026-05-22: El portal de doctores debe funcionar como vista operativa, no como reemplazo de OpenEMR.
- 2026-05-22: La cola médica se manejará inicialmente con tabla local `patient_queue`.
- 2026-06-01: Se implementó la tabla local `patient_queue` para manejar la cola operativa del portal médico.
- 2026-06-01: Se conectaron los flujos de paciente nuevo y paciente antiguo con `patient_queue`.
- 2026-06-01: Se creó el primer dashboard médico en `/doctor/dashboard`.
- 2026-06-01: Se validó el cambio de estado `pending → in_progress → completed` con persistencia en SQLite.

---

# 8. Nota de mantenimiento

Este `todo.md` debe mantenerse sincronizado con:

- `docs/openemr_api_notes.md`
- `docs/openemr_api_client_registration.md`
- `docs/OPERACION_LOCAL.md`
- estado real de la rama `flask-mvp`

Antes de implementar funciones nuevas:

1. Revisar `git status`.
2. Confirmar rama `flask-mvp`.
3. Actualizar desde GitHub si corresponde.
4. Hacer cambios pequeños.
5. Probar localmente.
6. Confirmar que no se suben secretos.
7. Hacer commit con mensaje claro.