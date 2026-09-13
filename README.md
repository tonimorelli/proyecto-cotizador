# Automatización de estimación de costo médico

## Proyecto

Automatización de estimación de costo médico para cotizaciones corporativas.

## Problema

Los archivos de entrada llegan en formatos Excel heterogéneos y actualmente requieren interpretación, estructuración y procesamiento manual.

## Objetivo de la v1

Recibir uno o más Excel de una cartera nueva, interpretar su estructura, mapear su información al esquema `edad | provincia | plan | SITU | cantidad`, detectar faltantes, aplicar reglas determinísticas aprobadas, requerir revisión humana ante decisiones actuariales materiales, construir escenarios aprobados, estimar un rango de costo médico esperado por plan, ejecutar controles y generar un Excel final auditable.

## Alcance incluido

- Interpretación de Excel heterogéneos de carteras nuevas.
- Mapping y normalización al esquema estándar.
- Detección de información faltante y aplicación de reglas determinísticas definidas.
- Revisión humana ante decisiones actuariales materiales.
- Construcción de escenarios aprobados.
- Cruce con tabla de costo médico esperado y cálculo de rango por plan.
- Controles y generación de Excel final auditable.

## Fuera de alcance

- Empresas con cartera actualmente afiliada, PMPM observado y resta de cartera existente.
- Dashboard de rentabilidad, margen comercial y precio final.
- Automatización de mails, Outlook y conexión directa al Data Warehouse.
- Interfaz web, dashboard, base de datos, Power Query y arquitectura multiagente.

## Arquitectura conceptual

```text
Excel no estandarizado
        ↓
Agente interpreta estructura
        ↓
Mapping
        ↓
Transformaciones determinísticas
        ↓
Revisión humana cuando corresponda
        ↓
Motor actuarial determinístico
        ↓
Controles
        ↓
Excel final
```

## Principios de diseño

- El LLM se usa para interpretar heterogeneidad semántica y estructura, no para cálculos ni reglas determinísticas.
- Python/código determinístico realiza transformaciones, cálculos y controles reproducibles.
- El criterio actuarial y las aprobaciones materiales permanecen en manos humanas.
- No se usa arquitectura multiagente por defecto; se priorizan simplicidad, trazabilidad y fácil debugging.

## Estado actual

Etapa actual: Etapa 0 — Inicialización y gobierno  
Estado: completada  
Próxima etapa: Etapa 1 — Casos de referencia

## Cómo continuar

Antes de programar lógica, preparar ejemplos sanitizados y sus resultados esperados para los casos de referencia.
