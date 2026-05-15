# OpenEMR Kiosk

Kiosko de recepción para Centro Neuropsicológico Saavedra.

## Objetivo

Crear una app tipo kiosko para tablet que permita:

- Registrar paciente nuevo.
- Buscar paciente existente.
- Crear encuentro en OpenEMR.
- Usar Gemini Flash como agente conversacional controlado.
- Validar datos antes de enviarlos a OpenEMR.

## Stack definido

- Backend: Flask
- IA: Gemini Flash
- Integración clínica: OpenEMR API
- Desarrollo: VS Code Remote SSH

## Estado

La carpeta `legacy_php/` contiene el kiosko PHP anterior usado como referencia.

La nueva implementación Flask empieza desde la raíz del proyecto.