# caso_a — entrada

Corrida: `20260913_222439`  ·  Version de codigo: `v2`

Los archivos originales no se publican. Se listan con su rol, su formato y el sha256 del archivo real, que permite verificar que la corrida uso exactamente esos insumos si alguien tiene acceso autorizado a ellos.

De la fecha se publica el ano y el mes, y del tamano un tramo de magnitud: el dia exacto y el tamano exacto son huellas que, cruzadas con el buzon del equipo, identifican la licitacion.

**El sha256 no anonimiza.** Es un identificador univoco del archivo original. Sirve para que quien tenga acceso autorizado al archivo verifique que la corrida uso exactamente ese archivo, y tambien permite a un tercero que sospeche de un archivo concreto confirmar o descartar la sospecha comparando el hash. Expone menos que el nombre, la fecha exacta y el tamano exacto; no es anonimato.

| id | archivo (seudonimo) | formato | tamano | rol | confianza | origen | lectura | sha256 del original |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F01 | `F01_2026-07_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `05e5d206cba0689a…` |
| F02 | `F02_2026-07_documento_original_del_cliente.pdf` | pdf | 100 KB - 1 MB | documento original del cliente | alta | agente | completa | `8380d9f8ba50e081…` |
| F03 | `F03_2026-07_padron_individual.xlsx` | xlsx | 1 - 10 MB | padron individual | alta | agente | completa | `4733d00bbdf0a48a…` |
| F04 | `F04_2026-07_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `24fbbd0988f5f979…` |
| F05 | `F05_2026-07_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `c803567259a7d015…` |
| F06 | `F06_2026-07_contexto_sin_datos_de_cartera.xls` | xls | 1 - 10 MB | contexto sin datos de cartera | alta | reconocedor | completa | `f677ba7379bb583b…` |
| F07 | `F07_2026-07_cotizacion_interna_posterior.xls` | xls | 1 - 10 MB | cotizacion interna posterior | alta | agente | completa | `7b74bd116c8bf17e…` |
| F08 | `F08_2026-07_cotizacion_interna_posterior.xlsx` | xlsx | < 100 KB | cotizacion interna posterior | alta | agente | completa | `c7da90c6196ae3e4…` |
| F09 | `F09_2026-07_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `02caa8d6a55f5bc1…` |
| F10 | `F10_2026-08_cotizacion_interna_posterior.xlsx` | xlsx | 1 - 10 MB | cotizacion interna posterior | alta | agente | completa | `9fd5589330d55b36…` |
| F11 | `F11_2026-08_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `efecc6fb5691c60a…` |

## Insumos de referencia

- Tabla de escenarios de situacion terapeutica (no publicable: insumo interno del area).
- Distribucion etaria precomputada desde la referencia corporativa (no publicable: deriva de la cartera real).
