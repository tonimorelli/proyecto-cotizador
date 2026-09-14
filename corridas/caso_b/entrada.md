# caso_b — entrada

Corrida: `20260913_222800`  ·  Version de codigo: `v2`

Los archivos originales no se publican. Se listan con su rol, su formato y el sha256 del archivo real, que permite verificar que la corrida uso exactamente esos insumos si alguien tiene acceso autorizado a ellos.

De la fecha se publica el ano y el mes, y del tamano un tramo de magnitud: el dia exacto y el tamano exacto son huellas que, cruzadas con el buzon del equipo, identifican la licitacion.

**El sha256 no anonimiza.** Es un identificador univoco del archivo original. Sirve para que quien tenga acceso autorizado al archivo verifique que la corrida uso exactamente ese archivo, y tambien permite a un tercero que sospeche de un archivo concreto confirmar o descartar la sospecha comparando el hash. Expone menos que el nombre, la fecha exacta y el tamano exacto; no es anonimato.

| id | archivo (seudonimo) | formato | tamano | rol | confianza | origen | lectura | sha256 del original |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F01 | `F01_2025-05_contexto_sin_datos_de_cartera.xls` | xls | > 10 MB | contexto sin datos de cartera | alta | reconocedor | completa | `5d41796a9a03aa49…` |
| F02 | `F02_2025-05_cotizacion_interna_posterior.eml` | eml | < 100 KB | cotizacion interna posterior | alta | agente | completa | `52e2966dd86c16ef…` |
| F03 | `F03_2025-08_cotizacion_interna_posterior.eml` | eml | < 100 KB | cotizacion interna posterior | media | agente | completa | `04d0cc360c642a66…` |
| F04 | `F04_2025-08_contexto_sin_datos_de_cartera.pdf` | pdf | < 100 KB | contexto sin datos de cartera | media | agente | completa | `ec668648932bf8eb…` |
| F05 | `F05_2025-08_cotizacion_interna_posterior.xlsx` | xlsx | < 100 KB | cotizacion interna posterior | media | agente | completa | `b7e1b93a17a68467…` |
| F06 | `F06_2025-11_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | baja | agente | completa | `a508babe15c608df…` |
| F07 | `F07_2025-11_contexto_sin_datos_de_cartera.xlsx` | xlsx | < 100 KB | contexto sin datos de cartera | media | agente | completa | `ad85827d0fae46a5…` |
| F08 | `F08_2025-11_padron_individual.xlsx` | xlsx | 100 KB - 1 MB | padron individual | alta | agente | completa | `3a85ca7ea009b598…` |
| F09 | `F09_2025-11_contexto_sin_datos_de_cartera.eml` | eml | < 100 KB | contexto sin datos de cartera | alta | agente | completa | `9bfd5c508c3cba50…` |
| F10 | `F10_2025-11_documento_original_del_cliente.pdf` | pdf | 1 - 10 MB | documento original del cliente | alta | agente | **PARCIAL** | `70a0d6d3596b62f6…` |
| F11 | `F11_2025-11_distribucion_agregada.xlsx` | xlsx | < 100 KB | distribucion agregada | media | agente | completa | `61d8aea9608be229…` |

## Insumos de referencia

- Tabla de escenarios de situacion terapeutica (no publicable: insumo interno del area).
- Distribucion etaria precomputada desde la referencia corporativa (no publicable: deriva de la cartera real).
