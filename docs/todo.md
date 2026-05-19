# TODO - OpenEMR Kiosk / Bot de Recepción

Centro Neuropsicológico Saavedra  
Backend Flask + Gemini Flash + API OpenEMR

Última actualización base: 2026-05-15  
Fuente: documento base original `plan_accion_openemr_kiosk.docx`

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

---

## Estado actual confirmado según documento base

- [x] Usar Gemini Flash como modelo IA, Flask como backend y VS Code Remote SSH para desarrollo.
- [x] Kiosko anterior encontrado en `/var/www/html/openemr/kiosko`.
- [x] Contenido copiado a `/opt/openemr-kiosk`.
- [x] Servidor autenticado correctamente con GitHub como `Myroesh`.
- [x] Repositorio `Myroesh/openemr-kiosk` creado y accesible.
- [x] Rama `flask-mvp` creada y publicada.
- [x] PHP anterior movido a `legacy_php/` como referencia.
- [x] Base Flask inicial creada: `app.py`, `templates`, `static`, `services`, `requirements.txt`.
- [x] Flask responde por HTTP explícito en puerto `5000`.
- [x] `GEMINI_API_KEY` configurada en `.env` local y `/health/gemini` responde OK con `gemini-2.5-flash`.

---

## Principios de diseño que no debemos perder

### Seguridad del flujo

La tablet nunca debe tener credenciales de OpenEMR, Gemini ni base de datos.

### Backend intermedio

La tablet habla con Flask. Flask valida, registra logs y recién después habla con OpenEMR.

### IA controlada

Gemini Flash solo interpreta, conversa, normaliza y ayuda. No decide libremente acciones clínicas.

### Confirmación final

No se crea paciente ni encounter sin mostrar resumen y recibir confirmación.

### Evitar duplicados

Antes de crear paciente nuevo, buscar por CI/documento, teléfono y/o datos disponibles.

### Documentación oficial

Para API, Swagger, OAuth2, FHIR y Standard API se prioriza documentación oficial OpenEMR.

### MVP primero

Primero resolver recepción básica. Luego mejorar IA, voz, agenda, reportes o integraciones extra.

---

# Checklist maestro por fases

## Fase 0 - Base del repositorio y entorno

- [x] Crear `/opt/openemr-kiosk` y copiar kiosko anterior.
- [x] Configurar Git/GitHub SSH en el servidor OpenEMR.
- [x] Crear repo `Myroesh/openemr-kiosk`.
- [x] Crear rama `flask-mvp`.
- [x] Mover PHP anterior a `legacy_php/`.
- [x] Crear estructura Flask base.
- [x] Probar `/health` por HTTP en puerto `5000`.
- [x] Actualizar `requirements.txt` en GitHub si quedó vacío o incompleto.
  - Evidencia base: `requirements.txt` confirmado en GitHub con Flask, python-dotenv, requests, google-genai.
- [x] Confirmar `git status` limpio después del último push.
  - Evidencia base: últimos cambios empujados a rama `flask-mvp`; `.env` y `.htpasswd` fuera de Git.

---

## Fase 1 - Pantallas base del MVP sin OpenEMR ni IA

- [x] Actualizar pantalla inicial con botones reales: `/nuevo` y `/antiguo`.
- [x] Crear ruta `/nuevo` con formulario inicial de paciente nuevo.
- [x] Crear ruta `/antiguo` con búsqueda por CI/documento o teléfono.
- [x] Crear ruta `/confirmar` para mostrar resumen antes de guardar.
- [x] Crear ruta `/exito` con mensaje final: “Registro completado, espere a ser llamado”.
- [~] Crear diseño responsive para tablet.
  - Nota base: CSS responsive creado; falta ajustar/probar específicamente en tablet.
- [ ] Agregar logo y datos del centro sin depender de rutas internas de OpenEMR.

---

## Fase 2 - Base de datos local y logs del kiosko

- [x] Definir si usaremos SQLite local para logs del MVP.
  - Decisión base: usar SQLite local para logs y registros temporales del kiosko.
- [x] Crear tabla `kiosk_events` o `registros_kiosko`.
  - Confirmado en `services/db_service.py`: tabla `kiosk_events` creada con `created_at`, `event_type`, `flow_type`, `status`, `message`, `intake_id` y `metadata_json`.

- [x] Registrar fecha/hora, flujo, estado, mensaje de error y datos mínimos no sensibles.
  - Confirmado en `create_kiosk_event()`: registra eventos con fecha/hora, tipo de flujo, estado, mensaje y metadata controlada.

- [x] Crear panel `/admin/logs` protegido de forma simple para revisión interna.
  - Confirmado en `app.py`: `/admin/logs` usa `@admin_auth_required` y muestra eventos/intakes desde SQLite.
- [ ] Evitar almacenar más datos clínicos de los necesarios en logs.

---

## Fase 3 - Descubrimiento real de API OpenEMR

- [x] Confirmar versión exacta de OpenEMR en `Administration -> System -> About`.
  - Confirmado: OpenEMR 7.0.2.

- [x] Confirmar API activa en `Administration -> Config/Globals -> Connectors`.
  - Confirmado: Standard REST API y FHIR REST API activas.

- [x] Confirmar Site Address correcto.
  - Confirmado: `https://100.124.189.84`.

- [x] Confirmar si el servidor OpenEMR usa HTTP local o HTTPS.
  - Confirmado: Swagger/API funcional por HTTPS.

- [x] Entrar al Swagger correcto de esta instalación.
  - Confirmado: `https://100.124.189.84/swagger/`.

- [x] Identificar endpoints reales para buscar paciente.
  - Confirmado: `GET /apis/default/api/patient`.

- [x] Identificar endpoint real para crear paciente.
  - Identificado: `POST /apis/default/api/patient`.

- [x] Identificar endpoint real para crear encounter.
  - Identificado: `POST /apis/default/api/patient/{puuid}/encounter`.

- [x] Identificar si necesitamos consultar usuarios/profesionales/facility.
  - Scopes objetivo documentados: `user/practitioner.read`, `user/facility.read`, `user/user.read`.

- [x] Guardar notas de endpoints verificados en `docs/openemr_api_notes.md`.

---

## Fase 4 - Autenticación OpenEMR desde Flask

- [x] Definir método OAuth2 correcto para la instalación real.
  - Confirmado: OAuth2 funcional por HTTPS con cliente Standard API.

- [x] Crear cliente API si corresponde.
  - Confirmado: cliente `OpenEMR Kiosk Flask Standard API` creado y habilitado.

- [x] Guardar credenciales solo en `.env` local.
  - Criterio definido: no guardar `client_id`, `client_secret`, tokens ni claves reales en GitHub.

- [x] Probar llamada simple autenticada sin crear datos.
  - Confirmado: `GET /apis/default/api/patient` respondió correctamente.

- [~] Manejar expiración/renovación de token.
  - Pendiente solución estable. Por ahora se usa `OPENEMR_ACCESS_TOKEN` manual desde Swagger; no usar placeholder en `OPENEMR_REFRESH_TOKEN`.
---

## Fase 5 - Validaciones antes de OpenEMR

- [x] Validar nombres y apellidos obligatorios.
- [x] Validar fecha de nacimiento y edad coherente.
- [x] Validar CI/documento si se solicita.
- [x] Validar teléfono boliviano o formato aceptado por el centro.
- [x] Validar motivo de consulta no vacío.
- [x] Validar datos de tutor si es menor de edad.
- [~] Implementar normalización sin sobrescribir la respuesta original del paciente.
  - Hay normalización implementada, pero falta decidir si se conservará también la respuesta original cruda.
- [x] Crear resumen final obligatorio antes de guardar.

---

## Fase 6 - Integración Gemini Flash controlada

- [x] Configurar `GEMINI_API_KEY` en `.env` local.
  - Nota base: `.env` ignorado por Git.
- [x] Implementar `services/gemini_service.py`.
  - Nota base: implementado con `google-genai` y prueba de conexión.
- [ ] Definir prompts estrictos para extraer solo el campo actual.
- [ ] Hacer que Gemini devuelva JSON estructurado o resultado controlado.
- [ ] Agregar fallback si Gemini falla: formulario manual.
- [~] Evitar que Gemini cree acciones directas en OpenEMR.
  - Nota base: por arquitectura Gemini no tiene acceso a OpenEMR; falta reforzarlo en prompts/servicios.
- [ ] Registrar errores de IA sin exponer datos sensibles.

---

## Fase 7 - Flujo paciente nuevo

- [x] Pedir datos uno por uno o mediante formulario guiado.
  - Implementado por formulario `/nuevo`.

- [ ] Buscar duplicados antes de crear.

- [x] Mostrar resumen final.
  - Implementado en `/confirmar`.

- [ ] Crear paciente en OpenEMR solo tras confirmación.
  - Todavía no implementado; actualmente guarda intake local.

- [x] Registrar resultado en logs.
  - Confirmado: eventos `pending_confirmation` y `patient_intake_created`.

- [x] Mostrar pantalla final.
  - Implementado en `/exito`.

- [ ] Definir si también se crea encounter luego del paciente nuevo.

---

## Fase 8 - Flujo paciente antiguo

- [x] Pedir CI/documento o teléfono.
  - Implementado como búsqueda por nombre o teléfono en `/antiguo`.

- [x] Buscar paciente en OpenEMR.
  - Confirmado: `/antiguo` busca paciente real mediante `OpenEMRService.search_patients()`.

- [x] Mostrar confirmación básica de identidad.
  - Confirmado: `/confirmar-antiguo` muestra el paciente encontrado en OpenEMR antes de continuar.

- [x] Pedir motivo/tipo de consulta.

- [ ] Crear encounter para la fecha actual.

- [x] Registrar resultado en logs.
  - Confirmado: eventos de validación y confirmación local.

- [x] Mostrar pantalla final.

---

## Fase 9 - Pruebas y control de errores

- [ ] Probar paciente nuevo con datos válidos.
- [ ] Probar paciente nuevo con datos incompletos.
- [ ] Probar duplicado por CI/documento.
- [ ] Probar paciente antiguo no encontrado.
- [ ] Probar error de OpenEMR API.
- [ ] Probar error de Gemini o timeout.
- [ ] Confirmar que no se crean datos sin confirmación.

---

## Fase 10 - Despliegue local estable

- [ ] No usar Flask debug server para producción.
- [ ] Configurar Gunicorn o servicio systemd.
- [ ] Definir puerto interno o proxy por Apache.
- [ ] Restringir acceso a red local/Tailscale.
- [ ] Definir si se requiere HTTPS en LAN.
- [ ] Crear procedimiento de reinicio y revisión de logs.

---

## Fase 11 - Documentación operativa

- [ ] Documentar cómo iniciar/detener el kiosko.
- [ ] Documentar cómo revisar logs.
- [ ] Documentar cómo actualizar código desde GitHub.
- [ ] Documentar qué hacer si OpenEMR API falla.
- [ ] Documentar qué hacer si Gemini falla.
- [ ] Crear checklist de uso para el personal del centro.

---

# Siguiente bloque de trabajo recomendado según documento base

1. [x] Confirmar `requirements.txt`.
   - Confirmado en GitHub: Flask, python-dotenv, requests, google-genai.
2. [x] Crear rutas `/nuevo` y `/antiguo`.
   - Rutas y templates base creados; falta POST/validación.
3. [x] Crear pantalla `/confirmar`.
   - Confirmado: `/confirmar` y `/confirmar-antiguo` implementados.

4. [x] Crear logs locales simples.
   - Confirmado: SQLite con `patient_intake` y `kiosk_events`.

5. [x] Luego Swagger/OpenEMR API.
   - Confirmado: Swagger, HTTPS, OAuth2 y `GET /api/patient`.

6. [x] Implementar `services/openemr_service.py`.
   - Confirmado: `/health/openemr` conectado a OpenEMR y devuelve conteo de pacientes.

7. [x] Conectar flujo de paciente antiguo a búsqueda real en OpenEMR.

8. [ ] Conectar flujo de paciente nuevo a creación real en OpenEMR.

9. [ ] Crear encounter para paciente antiguo confirmado.

---

# Comandos útiles actuales

```bash
cd /opt/openemr-kiosk
source .venv/bin/activate
python app.py
```

```bash
git status
git add .
git commit -m "mensaje"
git push origin flask-mvp
```

URLs de desarrollo según documento base:

```text
http://100.124.189.84:5000
http://100.124.189.84:5000/health
```

---

# Registro de decisiones

- 2026-05-15: Usar Gemini Flash como IA del kiosko.
- 2026-05-15: Usar Flask como backend.
- 2026-05-15: Desarrollar vía VS Code Remote SSH.
- 2026-05-15: No conectar tablet directamente a OpenEMR.
- 2026-05-15: Separar PHP anterior en `legacy_php/` y empezar Flask limpio.
- 2026-05-15: Usar HTTP en puerto `5000` solo para desarrollo; HTTPS se definirá después.
- 2026-05-15: Configurar `GEMINI_API_KEY` solo en `.env` local; no subir secretos al repositorio.
- 2026-05-15: Usar SQLite local para logs/registros temporales del MVP antes de integrar OpenEMR.
- 2026-05-15: Crear rutas base `/nuevo`, `/antiguo`, `/exito` y `/admin/logs` antes de conectar OpenEMR.

---

# Nota de mantenimiento

Este `todo.md` fue creado a partir del documento base original.

Después debe actualizarse contra el estado real del repo y contra `docs/openemr_api_notes.md`, pero esa actualización debe hacerse como una segunda pasada para no mezclar fuente base con avance posterior.