# Instrucciones operativas para agentes

## Propósito y alcance

Este proyecto automatiza la estimación de costo médico esperado para cotizaciones corporativas de carteras nuevas: interpretación de Excel heterogéneos, normalización, reglas aprobadas, controles y Excel auditable. No incluye cartera conocida, pricing comercial, Outlook, Data Warehouse directo, UI, base de datos ni multiagentes.

## Reglas obligatorias

- Antes de cambiar arquitectura, leer en este orden: `README.md`, `DECISIONES.md`, `docs/ESTADO_PROYECTO.md` y `docs/ARQUITECTURA.md`.
- `DECISIONES.md` es fuente obligatoria de contexto.
- No inventar reglas actuariales ni homologaciones materiales.
- No usar LLM para cálculos o transformaciones determinísticas.
- No incorporar datos sensibles, secretos o credenciales en archivos versionados.
- Actualizar `DECISIONES.md` ante una decisión real y `docs/ESTADO_PROYECTO.md` al cerrar una etapa.
- No avanzar automáticamente de etapa: la decisión corresponde al responsable humano.
