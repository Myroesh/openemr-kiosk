# OpenEMR API Notes

Notas verificadas para integración del kiosko Flask con OpenEMR.

## Instalación

- OpenEMR version: 7.0.2
- Ruta servidor: `/var/www/html/openemr`
- URL OpenEMR tentativa: `http://100.124.189.84/openemr`
- URL Swagger confirmada: `http://100.124.189.84/swagger/`
- Server seleccionado en Swagger: `/apis/default`
- Site: `default`

## Connectors

Estado verificado en:

`Admin → Config → Connectors`

- Enable OpenEMR Standard FHIR REST API: activo
- Enable OpenEMR FHIR System Scopes: inactivo
- Enable OpenEMR Standard REST API: activo
- Enable OpenEMR Patient Portal REST API: inactivo
- Enable OAuth2 Password Grant: Off
- Site Address Override: vacío

## Swagger

Swagger confirmado en:

```text 
http://100.124.189.84/swagger/
```

## API Clients

Verificado en:

`Admin → System → API Clients`

Estado actual:

- No hay clientes registrados.
- Mensaje visible: `There are no clients registered in the system`.
- Será necesario registrar un nuevo cliente para que Flask pueda autenticarse contra la API de OpenEMR.

Pendiente:

- Definir tipo de cliente.
- Definir scopes mínimos.
- Obtener Client ID.
- Ver si OpenEMR entrega Client Secret.
- Probar autorización desde Swagger antes de implementar en Flask.

## OAuth2 Client - OpenEMR Kiosk Flask Dev

Cliente registrado para pruebas del kiosko Flask.

Configuración:

- Application Type: Confidential
- Application Context: Multipurpose Application
- App Name: OpenEMR Kiosk Flask Dev
- Redirect URI: http://100.124.189.84/swagger/oauth2-redirect.html
- Launch URI: http://100.124.189.84:5000/
- Logout URI: http://100.124.189.84:5000/

Scopes solicitados:

- openid
- fhirUser
- offline_access
- api:oemr
- api:fhir
- site:default
- user/Patient.read
- user/Patient.write
- user/Encounter.read
- user/Practitioner.read
- user/Organization.read

Nota:

No se seleccionaron scopes `patient/*` porque el kiosko es multipaciente y backend.
No se seleccionó `launch/patient` porque no se está lanzando desde el contexto de un paciente específico.