# caso_c — salida

Fecha de corrida: `2026-09-13T22:31:06`

## Que produjo

Un Excel de ocho hojas. **El archivo no se publica**: las hojas Informacion recibida, Diagnostico, Supuestos y Coberturas contienen datos personales seudonimizados, nombres de cliente y texto literal del pliego. Existe localmente en `output/` y esta fuera del control de versiones.

Este documento describe la corrida; **no reemplaza a esa salida**.

| Hoja | Filas |
| --- | --- |
| Informacion recibida | 0 |
| Distribuciones recibidas | 179 |
| Diagnostico | 13 |
| Supuestos | 59 |
| Coberturas | 26 |
| Cartera recibida | 0 |
| Cartera optimista | 17766 |
| Cartera pesimista | 17766 |

## Poblacion

- Camino: agregado
- Personas en cartera: [cifra no publicada]
- Combinaciones (grupo etario × provincia × plan): 9810
- Mapeo de columnas resuelto por: codigo (tabla cruzada)
- Subpoblaciones: 2

## Controles

- **optimista**: total de licitacion [cifra no publicada], 18 pares (subpoblacion, alternativa) controlados, tolerancia 1e-6.
- **pesimista**: total de licitacion [cifra no publicada], 18 pares (subpoblacion, alternativa) controlados, tolerancia 1e-6.
- **comparacion entre escenarios**: 8883 combinaciones comparadas sumando situ, maxima diferencia 4.55e-13.

El total de licitacion es la suma de las subpoblaciones **dentro de una alternativa**. Las alternativas de plan no se suman entre si.

## Cruces inferidos

- Condicionados al plan: 78
- Por marginal de subpoblacion: 0
- Segmentos resueltos por la regla 6.9: ['FAMILIARES']

## Limitaciones declaradas de esta corrida

- Ninguna fuente quedo parcialmente leida.
- Ninguna fuente informa situacion terapeutica observada, asi que la hoja Cartera recibida sale vacia con nota.
