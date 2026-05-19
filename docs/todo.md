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
- [ ] Crear ruta `/confirmar` para mostrar resumen antes de guardar.
- [x] Crear ruta `/exito` con mensaje final: “Registro completado, espere a ser llamado”.
- [~] Crear diseño responsive para tablet.
  - Nota base: CSS responsive creado; falta ajustar/probar específicamente en tablet.
- [ ] Agregar logo y datos del centro sin depender de rutas internas de OpenEMR.

---

## Fase 2 - Base de datos local y logs del kiosko

- [x] Definir si usaremos SQLite local para logs del MVP.
  - Decisión base: usar SQLite local para logs y registros temporales del kiosko.
- [ ] Crear tabla `kiosk_events` o `registros_kiosko`.
- [ ] Registrar fecha/hora, flujo, estado, mensaje de error y datos mínimos no sensibles.
- [~] Crear panel `/admin/logs` protegido de forma simple para revisión interna.
  - Nota base: ruta `/admin/logs` y template creados como base; falta conectar a BD y proteger acceso.
- [ ] Evitar almacenar más datos clínicos de los necesarios en logs.

---

## Fase 3 - Descubrimiento real de API OpenEMR

- [ ] Confirmar versión exacta de OpenEMR en `Administration -> System -> About`.
- [ ] Confirmar API activa en `Administration -> Config/Globals -> Connectors`.
- [ ] Confirmar Site Address correcto.
- [ ] Confirmar si el servidor OpenEMR usa HTTP local o HTTPS.
- [ ] Entrar al Swagger correcto de esta instalación.
- [ ] Identificar endpoints reales para buscar paciente.
- [ ] Identificar endpoint real para crear paciente.
- [ ] Identificar endpoint real para crear encounter.
- [ ] Identificar si necesitamos consultar usuarios/profesionales/facility.
- [ ] Guardar notas de endpoints verificados en `docs/openemr_api_notes.md`.

---

## Fase 4 - Autenticación OpenEMR desde Flask

- [ ] Definir método OAuth2 correcto para la instalación real.
- [ ] Crear cliente API si corresponde.
- [ ] Guardar credenciales solo en `.env` local.
- [ ] Implementar `services/openemr_service.py` con token Bearer.
- [ ] Probar llamada simple autenticada sin crear datos.
- [ ] Manejar expiración/renovación de token.

---

## Fase 5 - Validaciones antes de OpenEMR

- [ ] Validar nombres y apellidos obligatorios.
- [ ] Validar fecha de nacimiento y edad coherente.
- [ ] Validar CI/documento si se solicita.
- [ ] Validar teléfono boliviano o formato aceptado por el centro.
- [ ] Validar motivo de consulta no vacío.
- [ ] Validar datos de tutor si es menor de edad.
- [ ] Implementar normalización sin sobrescribir la respuesta original del paciente.
- [ ] Crear resumen final obligatorio antes de guardar.

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

- [ ] Pedir datos uno por uno o mediante formulario guiado.
- [ ] Buscar duplicados antes de crear.
- [ ] Mostrar resumen final.
- [ ] Crear paciente en OpenEMR solo tras confirmación.
- [ ] Registrar resultado en logs.
- [ ] Mostrar pantalla final.
- [ ] Definir si también se crea encounter luego del paciente nuevo.

---

## Fase 8 - Flujo paciente antiguo

- [ ] Pedir CI/documento o teléfono.
- [ ] Buscar paciente en OpenEMR.
- [ ] Mostrar confirmación básica de identidad.
- [ ] Pedir motivo/tipo de consulta.
- [ ] Crear encounter para la fecha actual.
- [ ] Registrar resultado en logs.
- [ ] Mostrar pantalla final.

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
3. [ ] Crear pantalla `/confirmar`.
   - Resumen antes de cualquier acción.
4. [ ] Crear logs locales simples.
   - SQLite o archivo log, según decisión.
5. [ ] Luego Swagger/OpenEMR API.
   - Recién después se implementa `services/openemr_service.py`.

---

# Comandos útiles actuales

```bash
cd /opt/openemr-kiosk
source .venv/bin/activate
python app.py