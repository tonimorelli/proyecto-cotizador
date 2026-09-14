# caso_c — entrada

Corrida: `20260913_222945`  ·  Version de codigo: `v2`

Los archivos originales no se publican. Se listan con su rol, su formato y el sha256 del archivo real, que permite verificar que la corrida uso exactamente esos insumos si alguien tiene acceso autorizado a ellos.

De la fecha se publica el ano y el mes, y del tamano un tramo de magnitud: el dia exacto y el tamano exacto son huellas que, cruzadas con el buzon del equipo, identifican la licitacion.

**El sha256 no anonimiza.** Es un identificador univoco del archivo original. Sirve para que quien tenga acceso autorizado al archivo verifique que la corrida uso exactamente ese archivo, y tambien permite a un tercero que sospeche de un archivo concreto confirmar o descartar la sospecha comparando el hash. Expone menos que el nombre, la fecha exacta y el tamano exacto; no es anonimato.

| id | archivo (seudonimo) | formato | tamano | rol | confianza | origen | lectura | sha256 del original |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F01 | `F01_2026-08_cotizacion_interna_posterior.xlsx` | xlsx | < 100 KB | cotizacion interna posterior | alta | agente | completa | `e40b0ee84a74e03f…` |
| F02 | `F02_2026-08_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | media | agente | completa | `05ed8f4c3ca6f663…` |
| F03 | `F03_2026-08_distribucion_agregada.eml` | eml | < 100 KB | distribucion agregada | media | agente | completa | `e8420acd1868c0c1…` |
| F04 | `F04_2026-08_distribucion_agregada.xlsx` | xlsx | < 100 KB | distribucion agregada | alta | agente | completa | `9fac37219762c918…` |
| F05 | `F05_2026-08_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | media | agente | completa | `6072254cb086fe2c…` |
| F06 | `F06_2026-08_contexto_sin_datos_de_cartera.xls` | xls | > 10 MB | contexto sin datos de cartera | alta | reconocedor | completa | `3912e117acf5105b…` |
| F07 | `F07_2026-08_contexto_sin_datos_de_cartera.xls` | xls | 1 - 10 MB | contexto sin datos de cartera | alta | reconocedor | completa | `b61c55445e6bc72d…` |
| F08 | `F08_2026-08_contexto_sin_datos_de_cartera.xls` | xls | 100 KB - 1 MB | contexto sin datos de cartera | alta | agente | completa | `925a48edf5454fec…` |
| F09 | `F09_2026-08_contexto_sin_datos_de_cartera.xls` | xls | 1 - 10 MB | contexto sin datos de cartera | alta | agente | completa | `cd825343aadb2df5…` |
| F10 | `F10_2026-08_cotizacion_interna_posterior.xlsx` | xlsx | < 100 KB | cotizacion interna posterior | alta | agente | completa | `c088866c0118b24d…` |
| F11 | `F11_2026-08_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `6474d45aaea1c90a…` |
| F12 | `F12_2026-09_cotizacion_interna_posterior.xlsx` | xlsx | < 100 KB | cotizacion interna posterior | media | agente | completa | `b6e8a4acd02d296b…` |
| F13 | `F13_2026-09_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `deba97b6931196a8…` |

## Insumos de referencia

- Tabla de escenarios de situacion terapeutica (no publicable: insumo interno del area).
- Distribucion etaria precomputada desde la referencia corporativa (no publicable: deriva de la cartera real).
