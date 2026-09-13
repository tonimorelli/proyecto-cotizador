# Bitácora de decisiones

Este archivo registra las decisiones reales tomadas durante el desarrollo. No debe reescribirse posteriormente para que el proceso parezca más prolijo.

## 2026-09-03 — Alcance de la v1

**Versión / etapa:** v1 / Etapa 0

**Contexto:** Se definió el primer entregable del sistema de automatización actuarial.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** El tiempo disponible es de dos semanas de atención parcial.

**Decisión:** Automatizar interpretación de Excel heterogéneos, normalización, aplicación de reglas, estimación de costo médico esperado, controles y generación de Excel. Dejar fuera cartera conocida, pricing comercial, Outlook, conexión directa al DW, UI y multiagentes.

**Alternativas descartadas:** Incluir cartera conocida, pricing comercial, integraciones externas, interfaz y multiagentes en la v1.

**Motivo:** Prioridad por un flujo completo, probado y documentado dentro de dos semanas de atención parcial.

**Impacto en el sistema:** La v1 se concentra en una cartera nueva y en un resultado auditable de costo médico esperado.

**Tema abierto:** N/A

## 2026-09-03 — Arquitectura mínima

**Versión / etapa:** v1 / Etapa 0

**Contexto:** Se definió la separación de responsabilidades para la v1.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** N/A

**Decisión:** Usar un solo agente para interpretación, herramientas determinísticas para transformaciones y cálculos, y revisión humana para criterio actuarial material.

**Alternativas descartadas:** Arquitectura multiagente y LLM realizando cálculos.

**Motivo:** Simplicidad, reproducibilidad, trazabilidad y fácil debugging.

**Impacto en el sistema:** El LLM no implementará cálculos, reglas determinísticas ni decisiones actuariales materiales.

**Tema abierto:** N/A

## 2026-09-03 — Tratamiento de SITU

**Versión / etapa:** v1 / Etapa 0

**Contexto:** SITU requiere una definición para escenarios mínimo y máximo.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** Actualmente no existe una regla estándar defendible para mínimo/máximo.

**Decisión:** La v1 no debe inventar una regla para SITU; su definición requiere revisión actuarial hasta que exista una regla formal.

**Alternativas descartadas:** Inferir o asignar SITU de forma automática sin regla formal.

**Motivo:** Evitar decisiones actuariales no defendibles.

**Impacto en el sistema:** Los casos ambiguos de SITU deberán detenerse para revisión humana.

**Tema abierto:** Formalizar una regla actuarial aprobada para SITU.

## 2026-09-03 — Estrategia de implementación

**Versión / etapa:** v1 / Etapa 0

**Contexto:** Se estableció el orden de construcción de la v1.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** N/A

**Decisión:** Primero se construirá y validará el motor determinístico; después se incorporará el componente agéntico para interpretar inputs.

**Alternativas descartadas:** Construir primero el componente agéntico.

**Motivo:** Validar la base reproducible y auditable antes de incorporar interpretación semántica.

**Impacto en el sistema:** La implementación posterior empezará por casos de referencia y comportamiento determinístico.

**Tema abierto:** N/A
