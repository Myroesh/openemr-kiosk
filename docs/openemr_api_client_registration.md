# Registro de API Client OpenEMR para Kiosko Flask

## Objetivo

Registrar un cliente OAuth/OpenID Connect para que el kiosko Flask pueda autenticarse contra la Standard API de OpenEMR.

Este cliente permite:

- leer pacientes
- crear pacientes
- leer encounters
- crear encounters
- obtener `access_token`
- obtener `refresh_token` mediante `offline_access`

---

## Fuente oficial

El registro se basa en la documentación oficial de OpenEMR para OAuth2 / OpenID Connect y Dynamic Client Registration.

Endpoint usado:

```text
POST /oauth2/default/registration