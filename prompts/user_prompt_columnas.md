# Tarea — mapear las columnas de una fuente de población

Te paso las hojas de una planilla con sus encabezados de columna. El código ya intentó
reconocerlas por nombre y no pudo: los encabezados varían entre clientes.

Tu tarea es decir **qué hoja contiene la población y qué columna cumple cada rol**.

**No vas a ver filas de datos.** Decidís por los nombres de columna y la cantidad de filas.

## Roles a mapear

- `edad` — edad de la persona en años. Si solo hay fecha de nacimiento, devolvé `null`.
- `grupo` — identificador del grupo familiar: legajo, número de grupo, ID de titular.
  Sirve para propagar a la familia los atributos que vienen solo en la fila del titular.
- `provincia` — provincia o jurisdicción.
- `tipo` — parentesco o vínculo: titular, cónyuge, hijo.
- `capitas` — cantidad de integrantes del grupo, cuando existe como columna.
- `plan` — plan, categoría o nivel de cobertura de la persona.

## Reglas

- Devolvés el **nombre textual exacto** del encabezado, tal como te lo paso. No lo normalices.
- Si un rol no tiene columna, devolvés `null`. **No inventes una columna que no está.**
- Elegí la hoja con una fila por persona. Descartá hojas de resumen, tablas dinámicas y hojas vacías.
- Si ninguna hoja tiene población individual, devolvés `{"hoja": null}`.
- `edad` y `grupo` son los que importan. Sin `edad` la hoja no sirve como población.

## Formato de salida

Únicamente este objeto JSON, sin texto alrededor ni cercos de markdown:

```json
{
  "hoja": "nombre exacto de la hoja",
  "edad": "nombre exacto de la columna o null",
  "grupo": "nombre exacto de la columna o null",
  "provincia": "nombre exacto de la columna o null",
  "tipo": "nombre exacto de la columna o null",
  "capitas": "nombre exacto de la columna o null",
  "plan": "nombre exacto de la columna o null",
  "confianza": "alta | media | baja",
  "motivo": "una oración corta"
}
```

## Planilla

Archivo: `{{ARCHIVO}}`

```json
{{HOJAS}}
```
