# OpenEMR API Notes

Notas verificadas para integración del kiosko Flask con OpenEMR.

## Instalación

- OpenEMR version: 7.0.2
- Ruta servidor: /var/www/html/openemr
- URL tentativa OpenEMR: http://100.124.189.84/openemr
- Site: default

## Connectors

Estado verificado en Admin → Config → Connectors:

- Enable OpenEMR Standard FHIR REST API: activo
- Enable OpenEMR FHIR System Scopes: inactivo
- Enable OpenEMR Standard REST API: activo
- Enable OpenEMR Patient Portal REST API: inactivo
- Enable OAuth2 Password Grant: Off
- Site Address Override: vacío

## Swagger

Pendiente confirmar URL correcta.

URLs a probar:

- http://100.124.189.84/openemr/swagger
- http://100.124.189.84/openemr/swagger/
- http://100.124.189.84/swagger
- http://100.124.189.84/swagger/

## API Clients

Pendiente revisar en:

Admin → System → API Clients

## Endpoints pendientes de verificar

No implementar hasta confirmar en Swagger:

- Buscar paciente
- Crear paciente
- Crear encounter
- Consultar usuarios/profesionales
- Consultar facility