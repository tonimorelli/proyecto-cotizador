# Tarea — clasificar las fuentes de esta licitación

Te paso la ficha de cada archivo de una carpeta de licitación. De cada uno vas a ver el nombre,
la fecha, el formato, el tamaño, los nombres de hoja, los encabezados de columna y, cuando es un
mail o un PDF, un recorte del texto.

**No vas a ver filas de datos.** La clasificación se hace por estructura, no por contenido
personal. Si te parece que te falta información para decidir, no adivines: bajá la confianza.

## Catálogo de roles

{{ROLES}}

Guía de uso:

- **padron individual** — una fila por persona, con edad o fecha de nacimiento. Es la población
  que se va a cotizar.
- **distribucion agregada** — filas con cantidades por tramo, plan, provincia o parentesco.
  También es población, pero ya resumida.
- **documento original del cliente** — pliego, condiciones particulares, anexos de la licitación.
- **cotizacion interna posterior** — planillas de precios, comparativos de planes, propuestas
  económicas armadas por el equipo después de recibir la invitación. Aportan contexto, nunca
  población.
- **contexto sin datos de cartera** — mails de coordinación, exports del sistema propio con la
  cartera vigente, cualquier archivo que no aporte ni población ni condiciones.

## Archivos

```json
{{ARCHIVOS}}
```

## Respuesta

Un array JSON, un objeto por archivo, con las claves `id_fuente`, `rol`, `confianza` y `motivo`.
Sin texto fuera del JSON.
