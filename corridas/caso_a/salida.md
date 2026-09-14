# caso_a — salida

Fecha de corrida: `2026-09-13T22:27:58`

## Que produjo

Un Excel de ocho hojas. **El archivo no se publica**: las hojas Informacion recibida, Diagnostico, Supuestos y Coberturas contienen datos personales seudonimizados, nombres de cliente y texto literal del pliego. Existe localmente en `output/` y esta fuera del control de versiones.

Este documento describe la corrida; **no reemplaza a esa salida**.

| Hoja | Filas |
| --- | --- |
| Informacion recibida | [cifra no publicada] |
| Distribuciones recibidas | 0 |
| Diagnostico | 11 |
| Supuestos | 17 |
| Coberturas | 124 |
| Cartera recibida | 0 |
| Cartera optimista | 5760 |
| Cartera pesimista | 5760 |

## Poblacion

- Camino: padron individual
- Personas en cartera: [cifra no publicada]
- Combinaciones (grupo etario × provincia × plan): 1153
- Mapeo de columnas resuelto por: codigo

## Controles

- **optimista**: total de licitacion [cifra no publicada], 9 pares (subpoblacion, alternativa) controlados, tolerancia 1e-6.
- **pesimista**: total de licitacion [cifra no publicada], 9 pares (subpoblacion, alternativa) controlados, tolerancia 1e-6.
- **comparacion entre escenarios**: 2880 combinaciones comparadas sumando situ, maxima diferencia 1.14e-13.

El total de licitacion es la suma de las subpoblaciones **dentro de una alternativa**. Las alternativas de plan no se suman entre si.

## Limitaciones declaradas de esta corrida

- Ninguna fuente quedo parcialmente leida.
- Ninguna fuente informa situacion terapeutica observada, asi que la hoja Cartera recibida sale vacia con nota.
