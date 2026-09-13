# Arquitectura conceptual

## Componentes

1. Input Excel.
2. Agente de interpretación.
3. Mapping.
4. Normalización.
5. Configuración/reglas.
6. Intervención humana.
7. Motor determinístico.
8. Validaciones.
9. Excel final.
10. Registro de corrida.

## Responsabilidades

| Componente | Responsabilidad | No debe hacer |
| ---------- | --------------- | ------------- |
| Input Excel | Recibir archivos de una cartera nueva. | Suponer un formato estándar. |
| Agente de interpretación | Identificar estructura y proponer mapping. | Calcular costos, inventar SITU o decidir homologaciones de planes. |
| Mapping | Llevar campos interpretados al esquema estándar. | Resolver ambigüedades actuariales materiales. |
| Normalización | Aplicar transformaciones determinísticas aprobadas. | Crear reglas nuevas. |
| Configuración/reglas | Declarar reglas estables y versionables. | Ocultar reglas dentro de prompts. |
| Intervención humana | Aprobar decisiones actuariales materiales. | Delegar el criterio actuarial ambiguo al código o LLM. |
| Motor determinístico | Construir escenarios aprobados y calcular resultados. | Interpretar semántica incierta o decidir criterio actuarial. |
| Validaciones | Ejecutar controles reproducibles. | Reemplazar la aprobación humana. |
| Excel final | Presentar un resultado auditable. | Ocultar trazabilidad. |
| Registro de corrida | Conservar metadatos y revisión de la corrida. | Exponer datos confidenciales en Git. |

No se seleccionan todavía detalles de infraestructura más allá de esta arquitectura conceptual.
