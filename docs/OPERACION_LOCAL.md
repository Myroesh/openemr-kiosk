# Operación local - OpenEMR Kiosk

Kiosko de recepción para el Centro Neuropsicológico Saavedra.

Este documento describe cómo iniciar, detener, probar, revisar logs y actualizar el kiosko durante el desarrollo local.

---

## 1. Ubicación del proyecto

El proyecto está ubicado en:

```bash
/opt/openemr-kiosk
```

Entrar al proyecto:

```bash
cd /opt/openemr-kiosk
```

---

## 2. Rama de trabajo

La rama actual de desarrollo es:

```bash
flask-mvp
```

Ver rama actual:

```bash
git branch
```

La rama correcta debería aparecer marcada con `*`:

```bash
* flask-mvp
```

---

## 3. Activar entorno virtual

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

## 4. Iniciar servidor Flask de desarrollo

Con el entorno virtual activo:

```bash
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

Endpoint de prueba Gemini:

```text
http://100.124.189.84:5000/health/gemini
```

Importante: durante desarrollo se usa HTTP, no HTTPS.

Correcto:

```text
http://100.124.189.84:5000
```

Incorrecto:

```text
https://100.124.189.84:5000
```

Si se usa HTTPS por error, el navegador puede mostrar error SSL y Flask puede mostrar errores tipo `Bad request version`.

---

## 5. Detener servidor Flask

En la terminal donde está corriendo Flask:

```text
Ctrl + C
```

---

## 6. Si el puerto 5000 queda ocupado

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

## 7. Rutas principales del kiosko

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

Panel de logs:

```text
http://100.124.189.84:5000/admin/logs
```

---

## 8. Panel de logs

URL:

```text
http://100.124.189.84:5000/admin/logs
```

Este panel está protegido con usuario y contraseña mediante Basic Auth.

Las credenciales se configuran en el archivo local:

```bash
.env
```

Variables necesarias:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=clave-local
```

No subir `.env` a GitHub.

---

## 9. Variables de entorno locales

El archivo real local es:

```bash
.env
```

Debe contener, como mínimo:

```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-change-me

GEMINI_API_KEY=api-key-real
GEMINI_MODEL=gemini-2.5-flash

ADMIN_USERNAME=admin
ADMIN_PASSWORD=clave-local

KIOSK_DB_PATH=data/kiosk.db

OPENEMR_BASE_URL=http://100.124.189.84/openemr
OPENEMR_SITE=default
OPENEMR_CLIENT_ID=
OPENEMR_CLIENT_SECRET=
OPENEMR_USERNAME=
OPENEMR_PASSWORD=
```

El archivo `.env` está ignorado por Git.

Verificar que no aparezca en Git:

```bash
git status
```

No debe aparecer:

```text
.env
```

---

## 10. Base de datos local SQLite

La base local del kiosko se guarda en:

```bash
data/kiosk.db
```

Esta base es para registros temporales/logs del MVP.

No contiene todavía integración real con OpenEMR.

Si en desarrollo se necesita resetear datos de prueba:

```bash
rm -f data/kiosk.db
```

Luego reiniciar Flask:

```bash
python app.py
```

La base se recreará automáticamente.

---

## 11. Flujo actual del kiosko

### Paciente nuevo

```text
/nuevo
↓
formulario paciente nuevo
↓
validaciones backend
↓
/confirmar
↓
confirmación final
↓
guardar localmente en SQLite
↓
/exito
```

### Paciente antiguo

```text
/antiguo
↓
nombre y/o teléfono + profesional + motivo
↓
validaciones backend
↓
/confirmar-antiguo
↓
confirmación final
↓
registrar evento local
↓
/exito
```

---

## 12. Validaciones actuales

El servicio de validación está en:

```bash
services/validation_service.py
```

Actualmente valida:

- Nombre y apellido obligatorios para paciente nuevo.
- Fecha de nacimiento obligatoria.
- Fecha de nacimiento no futura.
- Edad coherente con menor/adulto.
- CI/documento opcional, pero validado si se llena.
- Teléfono celular boliviano.
- Motivo de consulta obligatorio.
- Profesional obligatorio.
- Padre o madre obligatorio si el paciente es menor de edad.
- Normalización básica de textos.

---

## 13. Profesionales

La lista de profesionales está hardcodeada en:

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

Para modificar los profesionales, editar esa lista y reiniciar Flask.

Luego probar:

```bash
python -m py_compile config.py app.py
python app.py
```

---

## 14. Gemini

Gemini está configurado como servicio, pero todavía no controla el flujo del paciente.

Endpoint de prueba:

```text
http://100.124.189.84:5000/health/gemini
```

Resultado esperado:

```json
{
  "model": "gemini-2.5-flash",
  "response": "Gemini conectado correctamente",
  "service": "gemini",
  "status": "ok"
}
```

Si Gemini falla:

1. Verificar que `.env` tenga `GEMINI_API_KEY`.
2. Verificar que el modelo sea `gemini-2.5-flash`.
3. Reiniciar Flask.
4. Probar `/health/gemini`.

---

## 15. Git - revisar cambios

Ver estado:

```bash
git status
```

Ver archivos modificados:

```bash
git diff
```

Agregar cambios:

```bash
git add .
```

Commit:

```bash
git commit -m "mensaje"
```

Subir a GitHub:

```bash
git push
```

---

## 16. Actualizar código desde GitHub

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
git pull
```

Si hay conflictos, no resolver a ciegas. Revisar archivo por archivo.

---

## 17. Archivos que no deben subirse

No subir:

```text
.env
data/kiosk.db
*.db
*.sqlite
*.sqlite3
.venv/
__pycache__/
legacy_php/admin/.htpasswd
```

Verificar siempre con:

```bash
git status
```

---

## 18. Pruebas rápidas recomendadas

### Probar sintaxis Python

```bash
python -m py_compile app.py config.py services/validation_service.py services/db_service.py services/gemini_service.py
```

### Probar salud del sistema

```text
http://100.124.189.84:5000/health
```

### Probar Gemini

```text
http://100.124.189.84:5000/health/gemini
```

### Probar paciente nuevo válido

Usar:

```text
Nombre: Juan Carlos
Apellido: Pérez López
Fecha nacimiento: 2015-05-10
CI: vacío
Celular: 70707070
Profesional: cualquiera de la lista
Menor: Sí
Madre: Ana María
Motivo: Evaluación por dificultades de atención
```

Debe pasar a:

```text
/confirmar
```

Luego confirmar y revisar:

```text
/admin/logs
```

### Probar paciente antiguo válido

Usar:

```text
Nombre: Juan Pérez
Teléfono: vacío
Profesional: cualquiera de la lista
Motivo: seguimiento
```

Debe pasar a:

```text
/confirmar-antiguo
```

Luego confirmar y revisar:

```text
/admin/logs
```

---

## 19. Estado actual de integración OpenEMR

Todavía no se está escribiendo ni leyendo desde OpenEMR.

Antes de crear o buscar pacientes reales en OpenEMR, se debe verificar:

1. Versión exacta de OpenEMR.
2. APIs activas en configuración.
3. Site Address correcto.
4. URL correcta de Swagger.
5. Método de autenticación OAuth2.
6. Endpoints reales para:
   - buscar paciente
   - crear paciente
   - crear encounter
   - consultar profesional/facility si hace falta

No inventar endpoints.

Las notas de esta fase deben guardarse en:

```bash
docs/openemr_api_notes.md
```