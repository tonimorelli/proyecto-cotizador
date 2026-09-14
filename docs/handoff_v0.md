# Handoff V0 — Agente de normalización para cotización corporativa

Documento de implementación. Cierra la etapa de planificación.

Reemplaza el alcance descrito en las entradas de bitácora del 2026-09-03 donde haya contradicción.

Fecha de cierre de planificación: 2026-09-13.

## 1. Propósito

Normalizar información heterogénea de una licitación corporativa y construir carteras documentadas para evaluación actuarial posterior.

El agente no cotiza. Prepara información auditable.

La salida debe distinguir siempre tres cosas: lo recibido, lo faltante y lo inferido.

## 2. Alcance de V0

Incluye:

- Procesar una carpeta mixta por licitación.
- Leer mails, Excel y PDF.
- Clasificar el rol de cada archivo.
- Extraer características de cartera y detalles de cobertura.
- Normalizar, homologar y diagnosticar faltantes.
- Construir cruces inferidos desde distribuciones separadas.
- Completar la cartera con reglas y con la referencia corporativa.
- Asignar situación terapéutica mediante la tabla de escenarios aprobada.
- Entregar tres carteras: recibida, optimista y pesimista.
- Generar un Excel por licitación.

No incluye:

- Extracción de contenido desde imágenes (sin OCR ni visión).
- Asignación de costo médico esperado.
- Valoración económica de coberturas.
- Automatización de Outlook y envío de mails.
- Integraciones, DWH, interfaces y arquitectura multiagente.

La extracción de contenido desde imágenes estaba en el alcance obligatorio original y se retiró. El motivo registrado en su momento —que el corpus no contenía ninguna imagen— es incorrecto: hay imágenes embebidas en los PDF. El motivo real es que no se implementa OCR ni visión en V0.

Lo que V0 sí hace, y es requisito incluido: **cuenta las imágenes por página y declara como fuente parcialmente leída todo PDF que tenga páginas sin texto extraíble.** El disparador es la ausencia de texto, no la presencia de imágenes: un PDF con logo en cada página tiene imágenes en todas y se lee entero. Implementado en `fuentes._leer_pdf`, se reporta en Diagnóstico y en Supuestos.

## 3. Insumos

### 3.1 Carpeta de licitación

Una carpeta por licitación, con archivos mixtos. Puede contener antecedentes, padrones internos, documentos originales del cliente y cotizaciones internas posteriores.

Estas fuentes nunca se suman como una única población.

### 3.2 Referencia corporativa

`Referencia/referencia_cartera_corpo_2026_08_28.xlsx`

Una sola hoja, `Hoja1`, 16 columnas. El detalle de volumen está en `docs/interno/spike_lectura.md`.

Columnas: `edad`, `grupo_etario`, `marca_st`, `id_emp_megacuenta`, `desc_emp_megacuenta`, `id_emp_empresa`, `desc_emp_empresa`, `segmento_megacuenta`, `rubro_megacuenta`, `plan_homologado`, `plan_codi`, `parentesco`, `suma_contador`, `Sanos`, `ST`, `consumo_ajustado_12m`.

Se usa completa. Sin filtros por empresa, rubro ni segmento.

Las distribuciones se ponderan por `suma_contador`. Nunca se cuentan filas.

Uso en V0: distribuir rangos etarios a edad entera. Nada más.

La referencia no tiene campo de provincia. No existe forma de inferir distribución provincial desde ella.

### 3.3 Tabla de escenarios de situación terapéutica

`Referencia/Escenarios_proporcion_ST.xlsx`

Una sola hoja, `Hoja1`, 21 grupos etarios, cuatro columnas: `Individuales`, `Corporate`, `Optimista`, `Pesimista`.

Las columnas de escenario están calculadas en el propio archivo:

- Optimista = Corporate × 0,9
- Pesimista = Individuales × 1,1

V0 aplica solo `Optimista` y `Pesimista`. Las otras dos columnas son insumo de esa derivación y se documentan, no se aplican.

La tabla es un insumo aprobado. V0 la consume como está y no la recalcula.

### 3.4 Archivo de overrides

Opcional, uno por licitación. Ver sección 8.

## 4. Modelo de datos

### 4.1 Tabla de mapeo (información recibida normalizada)

Columnas: edad o grupo etario, provincia, plan, situ, cantidad.

Los campos sin información llevan el valor literal «sin dato».

El plan original se conserva cuando está informado, incluso si no es homologable.

Las distribuciones separadas se conservan antes de construir cualquier cruce.

### 4.2 Tabla de cartera completada

| Columna | Dominio |
| --- | --- |
| subpoblacion | texto, o `unica` cuando la licitación tiene una sola |
| edad | interno: entero. Salida: etiqueta de grupo etario de la plantilla |
| provincia | catálogo de 24 valores |
| plan | catálogo de 9 valores |
| situ | 0 o 1 |
| cantidad | decimal |

Una licitación puede abarcar varias empresas con padrones y distribuciones separados. Cada una es una subpoblación. No se suman al construir la cartera, pero conviven en las mismas hojas y se pueden totalizar.

`situ` es situación terapéutica. 1 tiene, 0 no tiene.

La ausencia de información no equivale a cero.

### 4.3 Catálogo de provincia

BUENOS AIRES, AMBA, CORDOBA, SANTA FE, CATAMARCA, CHACO, CORRIENTES, ENTRE RIOS, FORMOSA, JUJUY, LA PAMPA, LA RIOJA, MENDOZA, MISIONES, SAN JUAN, SAN LUIS, SANTIAGO DEL ESTERO, TUCUMAN, CHUBUT, NEUQUEN, RIO NEGRO, SALTA, SANTA CRUZ, TIERRA DEL FUEGO.

La comparación para homologar es insensible a mayúsculas, a acentos y a espacios. Las fuentes escriben la misma provincia de varias formas dentro de una misma hoja.

### 4.4 Catálogo de plan

S1, SMG02, S2, SMG20, SMG30, SMG40, SMG50, SMG60, SMG70.

El orden es el declarado: 01) S1, 02) SMG02, 03) S2, 04) SMG20, 05) SMG30, 06) SMG40, 07) SMG50, 08) SMG60, 09) SMG70.

### 4.5 Mapeo de edad a grupo etario

Se replica la agrupación real de la referencia, no la etiqueta.

| Grupo | Edades |
| --- | --- |
| 01 | 0 a 1 |
| 02 | 2 a 5 |
| 03 | 6 a 10 |
| 04 | 11 a 15 |
| 05 | 16 a 20 |
| 06 | 21 a 25 |
| 07 | 26 a 30 |
| 08 | 31 a 35 |
| 09 | 36 a 40 |
| 10 | 41 a 45 |
| 11 | 46 a 50 |
| 12 | 51 a 55 |
| 13 | 56 a 60 |
| 14 | 61 a 65 |
| 15 | 66 a 70 |
| 16 | 71 a 75 |
| 17 | 76 a 80 |
| 18 | 81 a 85 |
| 19 | 86 a 90 |
| 20 | 91 a 95 |
| 21 | 96 y más |

**Decisión confirmada el 2026-09-13 (Opción 2).** Se usan las etiquetas literales de la plantilla aprobada: el grupo `01) 0 a 1` contiene las edades **0 y 1**, y el grupo `02) 2 a 5` contiene las edades 2 a 5. La tabla de escenarios se aplica según esas mismas etiquetas, como supuesto adoptado; su procedencia no está verificada y no se afirma nada sobre cómo se calcularon sus proporciones.

La referencia corporativa agrupa distinto por dentro: asigna la edad 0 al grupo 01 y las edades 1 a 5 al grupo 02, en contra de sus propias etiquetas. Ese agrupamiento se conserva **solo como validación**: `catalogos.grupo_referencia` verifica que el archivo de referencia siga siendo el que se inspeccionó, y `precomputar` falla ruidosamente si cambió. No interviene en ningún cálculo.

Los dos agrupamientos difieren únicamente en la edad 1, y hay un test que lo fija.

Las claves de `grupo_etario` en la referencia vienen con espacios de relleno y espacios internos múltiples. Hay que normalizar espacios antes de unir con la tabla de escenarios.

## 5. Pipeline

1. Inventariar la carpeta y clasificar el rol de cada archivo.
2. Aplicar el archivo de overrides si existe.
3. Extraer contenido por fuente y construir información recibida con identificador de fuente.
4. Propagar los atributos declarados a nivel de grupo familiar.
5. Normalizar y homologar edad, provincia, plan y situ.
6. Agregar distribuciones recibidas, por subpoblación.
7. Detectar conflictos y resolverlos por prioridad de fuente.
8. Elegir el total maestro y reescalar las distribuciones secundarias.
9. Construir cruces: observados donde existan, inferidos donde no.
10. Distribuir rangos etarios a edad entera con la referencia.
11. Completar provincia y expandir plan.
12. Asignar situ y generar las tres carteras.
13. Ejecutar los controles de cierre.
14. Escribir el Excel de salida.

El componente agéntico interviene en los pasos 1, 3 y 5. Los pasos 8 a 13 son determinísticos.

El LLM no calcula. No implementa reglas ni decisiones actuariales materiales.

## 6. Reglas

### 6.1 Clasificación de fuentes

El agente propone el rol de cada archivo y lo declara con un nivel de confianza.

Roles: padrón individual, distribución agregada, documento original del cliente, cotización interna posterior, contexto sin datos de cartera.

Niveles de confianza: alta, media, baja.

La clasificación completa se escribe en Diagnóstico, incluso cuando la confianza es alta. El humano corrige sobre esa hoja mediante overrides.

Señales disponibles para clasificar: nombre y fecha del archivo, remitente y asunto del mail asociado, estructura de la planilla, granularidad de las filas, y presencia de columnas de precio.

**Reconocedor determinístico del padrón interno.** El export del sistema propio tiene esquema fijo y se identifica por huella de columnas, sin intervención del LLM. Columnas de la huella: `contra`, `inte`, `plan_codi`, `megacuenta`, `Capitas`, `cuota_medica`. Este reconocedor corre antes que el agente.

Un padrón interno reconocido así es la cartera vigente de la cuenta, no la población a cotizar. Se clasifica como antecedente. El nombre del archivo puede decir «padrón» y no alcanza para decidir: la clasificación va por estructura.

Un archivo clasificado como cotización interna posterior se lee como contexto y no aporta población.

### 6.2 Prioridad y conflicto entre fuentes

Prioridad por granularidad:

1. Padrón individual.
2. Tabla agregada.
3. PDF y texto.

Ante empate de nivel, gana el archivo más reciente.

Todo conflicto se registra en Diagnóstico, incluso cuando la resolución es automática.

### 6.3 Homologación

El agente no inventa mapeos.

Un valor de provincia o plan que no entra en el catálogo queda como «sin dato». El valor original se conserva en Información recibida y se registra en Diagnóstico y Supuestos.

El proceso no se detiene por una denominación no reconocida.

### 6.4 Edad

Cada rango recibido se distribuye usando las edades de referencia contenidas en ese rango, ponderadas por `suma_contador`.

La cantidad original de cada rango se conserva.

Los rangos recibidos no se sustituyen por los rangos propios antes de distribuir.

Cada rango recibido se reparte con la `suma_contador` **absoluta** de las edades contenidas, renormalizada **sobre el rango** y nunca sobre el grupo. Un rango recibido puede cruzar los límites de los grupos de la referencia, y normalizar dentro de cada grupo repartiría mal entre ellos. Un rango abierto se topea en 100.

Las filas de la **referencia** con edad mayor a 100 se excluyen de la distribución etaria. Es una cola despreciable. Todas las edades de 0 a 100 tienen soporte.

**Edad mayor a 100 en la población recibida (confirmado el 2026-09-13).** No se descarta a nadie. La edad original se conserva en Información recibida, el cálculo y la asignación de escenario usan edad 100, y la salida agrupa en `21) +`. La transformación se registra en Supuestos y un control verifica que la cartera contenga todas las filas leídas menos las ilegibles. Esta regla aplica solo a la población recibida y no altera el tratamiento de la referencia corporativa.

### 6.5 Provincia

Si ninguna fuente informa provincia, se asigna AMBA a toda la cartera.

Las denominaciones recibidas se homologan al catálogo objetivo, con comparación insensible a mayúsculas, acentos y espacios.

Homologación del área metropolitana:

- Capital Federal, CABA y equivalentes van a AMBA.
- Las denominaciones que nombran explícitamente el GBA, como `Buenos Aires-GBA`, van a AMBA.
- Buenos Aires a secas, cuando la fuente distingue en otra fila el AMBA o el GBA, va a BUENOS AIRES.
- Buenos Aires a secas, cuando la fuente no distingue, va a AMBA.

Cuando la fuente trae localidad además de provincia, la localidad resuelve la ambigüedad mediante un catálogo de partidos del AMBA. El catálogo vive versionado en el repositorio y su aplicación se declara en Supuestos.

La referencia no tiene provincia, así que no hay distribución de respaldo desde la referencia. Cuando una parte de la población tiene provincia observada y otra no, se aplica la regla de la sección 6.9.

### 6.6 Plan

Si no se informan planes, la misma cartera se repite para los nueve planes del catálogo.

Cada repetición es una alternativa de cotización. Las alternativas no se suman entre sí.

Un plan informado pero no homologable, por ejemplo un plan de otro financiador, se trata igual: «sin dato» en la columna `plan`, valor original conservado en Información recibida, y expansión a las nueve alternativas.

### 6.7 Propagación dentro del grupo familiar

Las fuentes individuales suelen declarar los atributos del grupo una sola vez, en la fila del titular. Las filas de cónyuge e hijos quedan vacías.

Eso no es información faltante. Es estructura jerárquica. El atributo se propaga a todo el grupo mediante su identificador, sea legajo, número de grupo o equivalente.

La propagación se declara en Supuestos, con el campo propagado y la cantidad de filas afectadas.

Cuidado con el doble conteo. Cuando la fuente trae una columna de cápitas informada solo en la fila del titular, esa columna es el tamaño del grupo. Sumar la columna y contar filas son dos caminos al mismo total. Se usa uno y se verifica contra el otro. Nunca se suman entre sí.

### 6.8 Cruces inferidos

Los cruces son obligatorios cuando las distribuciones llegan separadas.

Donde exista un cruce observado, se usa el observado y no se infiere.

Cuando dos distribuciones observadas comparten una dimensión, el cruce se construye condicionado a esa dimensión, no por independencia total. Si una trae edad por plan y la otra provincia por plan, se cruza dentro de cada plan. Así el supuesto de independencia queda restringido a lo que efectivamente no se observó.

Solo cuando no hay dimensión compartida se cruza por independencia total.

Todo cruce inferido se identifica como tal. En Supuestos se declara el supuesto aplicado, si fue condicionado y sobre qué dimensión.

### 6.9 Distribuciones que cubren parte de la población

Una distribución recibida puede cubrir solo un segmento, por ejemplo los titulares y no los familiares.

En ese caso la distribución observada del segmento cubierto se aplica al segmento no cubierto, marcada como cruce inferido.

El supuesto se declara en Supuestos: por ejemplo, que el grupo familiar reside donde reside el titular.

Se prefiere esto antes que la regla por defecto de la sección 6.5, porque hay información observada disponible dentro de la misma licitación.

### 6.10 Totales incompatibles

**Antes de reescalar hay que verificar tres cosas**, porque reescalar distribuciones que no son comparables convierte una diferencia real en un factor de ajuste silencioso:

1. **Misma subpoblación.** Dos subpoblaciones no se reescalan entre sí; cada una cierra por separado.
2. **Mismo período o fecha de corte.** Si difieren, o si alguna no lo declara, la diferencia de totales puede ser real y no un error de lectura. Se declara y se marca revisión humana.
3. **Misma cobertura poblacional.** Si una cubre un segmento y la otra la población completa, corresponde la regla 6.9, no el reescalado.

Implementado en `normalizacion.verificar_antes_de_cruzar`, que informa y marca revisión humana pero no decide.

Recién superada esa verificación: cuando dos distribuciones recibidas suman totales distintos, se elige un total maestro con la prioridad de la sección 6.2, dentro de cada subpoblación, y se reescalan proporcionalmente las demás.

El factor de reescalado y su magnitud se registran en Supuestos y Diagnóstico.

### 6.11 Situación terapéutica y escenarios

Para cada edad se toma su grupo etario según la sección 4.5 y de ahí la proporción de la tabla de escenarios.

Cada fila de cartera se parte en dos: `cantidad × p` con situ 1 y `cantidad × (1 - p)` con situ 0.

La proporción no depende del plan ni de la provincia. La misma `p` aplica a todas las alternativas.

Para edades de 96 a 100 se usa el grupo 21, cuyo valor la tabla fijó igual al del grupo 20. La referencia muestra una proporción más alta para ese tramo. Se respeta el tope de la tabla.

Las tres carteras se definen así:

| Cartera | Situ | Población |
| --- | --- | --- |
| Recibida | situ observado en la fuente | solo la subpoblación con situ informado |
| Optimista | columna `Optimista` de la tabla | cartera completa |
| Pesimista | columna `Pesimista` de la tabla | cartera completa |

Las carteras optimista y pesimista aplican la tabla a toda la cartera, incluso cuando hay situ observado. Esto las mantiene comparables entre licitaciones.

La cartera recibida cubre únicamente la porción con situ informado. Su total se declara y se compara contra el total general en Diagnóstico. Cuando ninguna fuente informa situ, la hoja se emite vacía con una nota.

Decisión tomada sin consulta y sujeta a revisión: emitir siempre la hoja de cartera recibida, incluso vacía, para que el esquema del Excel sea estable. Ver sección 12.

Las tres carteras difieren únicamente en el eje situ. Edad, provincia, plan y totales son idénticos entre optimista y pesimista.

### 6.12 Cantidades y cierre

Las cantidades obtenidas por distribución no se redondean.

El control de cierre es estricto: tolerancia relativa 1e-6. Solo admite error de punto flotante. Un desvío mayor es error bloqueante.

El cierre se controla contra el total maestro, no contra los totales originales de cada distribución. El reescalado es un ajuste declarado, no un error.

La diferencia entre cada total original y el total maestro se reporta aparte como magnitud del ajuste.

El control se ejecuta por subpoblación, por escenario y por alternativa de plan.

**El total de la licitación es la suma de las subpoblaciones dentro de UNA alternativa.** Nunca la suma de las alternativas: nueve alternativas de 100 personas son la misma población de 100 cotizada de nueve formas, no 900 personas. Además se verifica que todas las alternativas cubran la misma población.

**Comparación entre escenarios.** Optimista y pesimista se comparan combinación por combinación de (subpoblación, alternativa, grupo etario, provincia, plan), sumando situ 0 y situ 1, no solo por el total general: un total igual puede esconder combinaciones distintas que se compensan.

En las carteras optimista y pesimista, la suma de situ 0 y situ 1 debe reproducir la cantidad previa a la partición, con la misma tolerancia.

## 7. Contrato de salida

Un Excel por licitación, con ocho hojas de nombre y orden fijos.

| Hoja | Contenido |
| --- | --- |
| Información recibida | Datos normalizados, campos con «sin dato», valores originales e `id_fuente`. |
| Distribuciones recibidas | Tablas agregadas, sin cruces reales identificables. |
| Diagnóstico | Clasificación de fuentes con confianza, faltantes, conflictos, ajustes de reescalado y decisiones humanas pendientes. |
| Supuestos | Distribuciones usadas, soporte muestral, referencia aplicada, homologaciones, supuestos de independencia y tabla de fuentes. |
| Coberturas | Detalles de cobertura documentados con su fuente. |
| Cartera recibida | Formato de cartera, con situ observado. |
| Cartera optimista | Formato de cartera. |
| Cartera pesimista | Formato de cartera. |

### 7.3 Formato de las hojas de cartera

Confirmado el 2026-09-13. Las cinco columnas y las denominaciones textuales de `Referencia/referencia_tabla_a_completar.xlsx`, más dos columnas identificatorias al frente:

`subpoblacion | alternativa | edad | provincia | plan | SITU | cantidad`

- Las denominaciones se escriben exactas: `01) 0 a 1`, `05) SMG30`, las 24 provincias en mayúsculas.
- **Se omiten las combinaciones con cantidad cero.** La plantilla es una grilla cartesiana de 9.072 filas; emitirla completa por alternativa serían 81.648 filas casi todas en cero.
- **Cuando falta plan se mantienen las nueve alternativas explícitas.** Sus cantidades se repiten entre alternativas: esa repetición es intencional, no un pendiente.
- Cada hoja de cartera lleva una nota en la primera fila advirtiendo que las alternativas no se suman.

### 7.1 Trazabilidad

Cada fila de las hojas de información lleva un `id_fuente` corto.

La tabla de fuentes vive en Supuestos y resuelve `id_fuente`, archivo, hoja, rango de celdas, rol clasificado y nivel de confianza.

### 7.2 Soporte muestral

Cada tramo distribuido con la referencia declara en Supuestos la `suma_contador` que lo respalda.

Esto permite ver cuándo una distribución se apoya en pocos casos, sin bloquear el proceso.

## 8. Overrides y re-corrida

Un Excel por licitación, con hojas espejo de Diagnóstico.

Hojas mínimas: clasificación de fuentes, homologaciones y conflictos.

El humano completa las correcciones, se vuelve a correr y la decisión queda registrada en la salida.

La salida es reproducible: misma carpeta más mismo archivo de overrides produce el mismo Excel.

## 9. Intervención humana y bloqueo

Tres niveles, no dos.

**Nivel 1 — bloqueo duro y ruidoso.** El proceso se detiene con excepción. Son fallas de insumo o de software, nunca decisiones humanas:

| Condición | Dónde |
| --- | --- |
| La tabla de escenarios no valida en forma | `escenarios.TablaEscenariosInvalida` |
| La referencia cambió su agrupamiento interno de edades | `referencia.ReferenciaInconsistente` |
| Un rango recibido no tiene soporte en la referencia | `referencia.RangoSinSoporte` |
| Error de cierre por encima de 1e-6 | `cartera.ErrorDeCierre` |
| Los escenarios no cubren la misma población o las mismas combinaciones | `cartera.ErrorDeCierre` |
| Se perdieron personas entre la lectura y la cartera | `pipeline.procesar` |
| Falta un insumo obligatorio | `scripts/procesar_licitacion.py` |

**Nivel 2 — produce y marca revisión humana obligatoria.** El Excel sale, con la fila señalada en Diagnóstico: reescalado por encima del umbral, PDF parcialmente leído, clasificación de fuente con confianza baja, cruce por independencia total, conflicto de atributos dentro de un grupo familiar, columna de cápitas que no coincide con el conteo de filas, distribuciones sin período declarado.

**Nivel 3 — produce y declara.** Faltantes, denominaciones no homologables y conflictos resueltos por prioridad. Todo va a Diagnóstico y Supuestos y no detiene nada.

Único caso de no producción de cartera: no se identifica ninguna fuente de la que derivar cantidades. Incluso entonces se escribe el Excel con Diagnóstico.

**Quién firma.** Pendiente de definir con el área. La checklist de 10.3 define qué se revisa; falta nombrar el rol responsable de cada corrida.

## 10. Pruebas y aceptación

### 10.1 Las tres pruebas

Las tres carpetas de `Ejemplos input de cotizaciones`, completas y sin recortar.

Los nombres reales de cliente y las cifras de cada caso están en `docs/interno/spike_lectura.md`.

**Prueba 1 — Caso A.** Padrón individual con edad, parentesco y grupo familiar. Provincia parcialmente informada. Sin columna de sexo. La carpeta incluye antecedentes y cotizaciones internas posteriores.

Resultado esperado: el padrón se clasifica como fuente de población y las cotizaciones internas como contexto. **La provincia parcial se completa propagando dentro del grupo familiar (6.7), no con la regla de AMBA de 6.5**, que solo aplica cuando ninguna fuente informa provincia. Lo que quede sin provincia después de propagar se resuelve por 6.9. Los planes informados son categorías internas del cliente, no homologables: quedan «sin dato» con el valor original conservado y la cartera se expande a nueve alternativas.

Verificado en la corrida real: la propagación completó la provincia de todos los integrantes de grupo familiar que la traían vacía, con 0 grupos en conflicto y 0 filas sin provincia al terminar. La regla de AMBA no intervino. El conteo de filas afectadas no se publica: es una fila por persona, así que equivale a publicar el tamaño de la cartera.

**Prueba 2 — Caso B.** Padrón con sexo, edad, plan, parentesco y ubicación. Las enfermedades aparecen en un resumen separado. Los planes son de otro financiador.

Resultado esperado: las enfermedades agregadas no se asignan a personas concretas. Los planes no homologables quedan como «sin dato» con el valor original conservado, y la cartera se expande a nueve alternativas. El resumen de enfermedades no se convierte en situ.

**Prueba 3 — Caso C.** Cantidades por rango etario, plan y parentesco. Distribución provincial en otra tabla.

Resultado esperado: se distinguen cruces observados de cruces inferidos. Si las dos tablas comparten una dimensión, el cruce se construye condicionado a ella según 6.8; solo sin dimensión compartida se cruza por independencia total. En cualquier caso queda marcado como inferido. Si los totales no coinciden, primero se verifica población, período y cobertura (6.10) y recién después se elige total maestro y se reporta el reescalado.

### 10.2 Verificación automática

- Las ocho hojas existen, con nombres y columnas esperados.
- Los dominios se respetan: edad entera 0 a 100, provincia y plan en catálogo, situ en 0 o 1.
- Ninguna fila de cartera queda sin subpoblación.
- Cierre estricto por subpoblación, escenario y alternativa de plan, tolerancia 1e-6.
- Suma de situ 0 más situ 1 igual a la cantidad previa a la partición.
- Toda fila de información recibida tiene un `id_fuente` resoluble en la tabla de fuentes.
- Todo cruce inferido está marcado como tal.
- La tabla de escenarios valida en forma: 21 grupos, proporciones entre 0 y 1, optimista menor o igual que pesimista en cada grupo.
- Re-corrida idéntica produce salida idéntica.

### 10.3 Checklist humana

Seis puntos sobre Diagnóstico y Supuestos:

1. La clasificación de fuentes es correcta, en especial qué archivo aportó la población.
2. Los conflictos declarados se resolvieron de forma razonable.
3. La magnitud del reescalado es aceptable y no esconde un error de lectura.
4. Los faltantes declarados coinciden con lo que efectivamente no vino.
5. Las homologaciones aplicadas y las omitidas son defendibles.
6. Los cruces inferidos son plausibles y su supuesto de independencia es aceptable para este caso.

No se exige reproducir la cotización histórica. Las cotizaciones que están en las carpetas de ejemplo incluyen criterio humano que V0 no reproduce. Sirven como referencia de orden de magnitud, no como resultado esperado.

## 11. Riesgos y límites conocidos

**La tabla de escenarios no es reproducible desde la referencia.** La columna Corporate se parece a `ST / (Sanos + ST)` de la referencia, pero no coincide en ningún grupo etario. Viene de otra extracción o de otro corte. Las diferencias medidas están en `docs/interno/spike_lectura.md`. V0 no puede validar sus valores contra nada.

**La columna Individuales no tiene respaldo en el repositorio.** Alimenta el escenario pesimista y no hay forma de auditarla desde acá.

**Los cruces inferidos suponen independencia.** El supuesto es casi siempre falso en grado desconocido. La edad y la provincia correlacionan con el rubro y con la estructura de la empresa. La cartera inferida es una construcción, no una estimación con error acotado.

**La provincia no tiene respaldo de referencia.** La regla de AMBA por defecto es una convención, no una inferencia. Con provincia ausente, la dimensión provincial de la salida no aporta información.

**Las nueve alternativas de plan no son una cartera.** Son nueve escenarios de cotización. Sumarlas produce un número sin sentido nueve veces mayor. La salida debe hacer esto evidente.

**El escenario pesimista no es un piso.** Es una proporción de situ 1,1 veces la de individuales. No cubre concentraciones de enfermedad específicas de la empresa.

**Los `.xls` legacy son pesados.** Siete archivos en formato antiguo, el mayor de 35 MB. Requieren `xlrd`, no `openpyxl`. El spike del 2026-09-13 confirmó que todos abren y que los padrones internos comparten un esquema fijo.

**Los PDF varían mucho entre sí.** Los tres son texto nativo y se extraen sin OCR, pero uno de ellos es un deck de presentación con más de la mitad de sus páginas casi sin texto y el contenido embebido en imágenes. La extracción desde PDF sigue siendo el punto más frágil del pipeline.

**Las imágenes quedan fuera, y aparecen dentro de los PDF.** El caso real no son archivos de imagen sueltos sino imágenes embebidas en un PDF de licitación. V0 debe contar las imágenes por página y declarar como fuente parcialmente leída todo PDF con páginas sin texto.

**`Sin Asigna` en `plan_homologado`.** La referencia trae un volumen menor de cápitas con ese valor, fuera del catálogo. Como se usa toda la referencia sin filtros, esas filas participan de la distribución etaria. Es correcto para edad, pero hay que tenerlo presente si en el futuro se distribuye por plan.

**Archivos de bloqueo de Excel.** Existen `~$referencia_cartera_corpo_2026_08_28.xlsx` y `~$Escenarios_proporcion_ST.xlsx`, lo que indica los libros abiertos. Conviene cerrarlos y que V0 ignore los archivos que empiezan con `~$`.

## 12. Pendientes abiertos

Ninguno bloquea el arranque de la implementación.

1. **Hoja de cartera recibida vacía.** Se decidió emitirla siempre, incluso sin situ observado, para mantener estable el esquema. Sujeto a revisión.
2. **Procedencia de la tabla de escenarios.** Documentar de dónde salen las columnas Individuales y Corporate, y con qué corte.
3. **Fórmulas de situ en el futuro.** Los factores 0,9 y 1,1 están embebidos en el archivo. Si se van a tocar, conviene decidir si viven en el Excel o en configuración.
4. **Rangos etarios recibidos que no coinciden con los grupos de la referencia.** La regla de distribución está definida, pero falta probarla contra un rango que cruce los límites de los grupos.
5. **Provincias ambiguas.** La regla cubre Buenos Aires contra AMBA. Faltan los casos que aparezcan en las pruebas.
6. **Organización interna de las hojas.** Cuando una hoja lleva varias tablas, falta definir separación y encabezados.
7. **Reincorporar imágenes** cuando exista una licitación real que las requiera.
8. **Extensión opcional.** Cruzar las carteras con la tabla de costo médico esperado. No es parte de V0 y su tabla resumen todavía no debe diseñarse.

## 13. Verificación

La estructura de todos los insumos y del corpus de prueba fue verificada contra el repositorio el 2026-09-13.

Las cifras, los nombres de cliente y el detalle archivo por archivo están en `docs/interno/spike_lectura.md`, que no se commitea.

Este documento se mantiene libre de datos de cliente y de volúmenes reales, para que el repositorio pueda publicarse sin sanear la historia.


## 14. Backend del modelo

Confirmado el 2026-09-13.

El agente corre sobre el **binario de Claude Code** (`CLAUDE_CODE_EXECPATH`), con el modelo `claude-haiku-4-5`. No hay API de Anthropic habilitada en este entorno y no se va a incorporar. `agente.ClienteCLI` encapsula el backend detrás de la misma interfaz que tendría un cliente de API, así que cambiarlo no toca al resto del sistema.

**Sobre los costos.** Lo que se registra por llamada es lo que reporta el CLI: `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens` y `total_cost_usd`. Los tokens de caché están incluidos en el total de entrada que informamos.

Dos advertencias sobre esa cifra:

- `total_cost_usd` es una **estimación a precio de lista** que produce la herramienta. No es el cobro efectivo de la cuenta, que depende del plan contratado.
- El CLI inyecta su propio prompt de sistema además del nuestro, así que el conteo de entrada incluye tokens que no son del contrato del agente. **No está medido** cuánto costaría lo mismo por API directa, y no se afirma que sería más barato sin esa comparación.

**Qué interpreta el agente y qué resuelve el código.**

| Paso | Quién |
| --- | --- |
| Huella de columnas del padrón interno | Código, determinístico, antes del agente |
| Rol y confianza de cada fuente | Agente |
| Detección de la hoja de población y mapeo de columnas | Código, por nombre de columna |
| Extracción de detalles de cobertura del pliego | Agente |
| Propagación en el grupo familiar | Código |
| Homologación de provincia y plan | Código, contra catálogo |
| Distribución etaria, escenarios, controles y cierre | Código |

El LLM no calcula. No implementa reglas ni decisiones actuariales materiales.
