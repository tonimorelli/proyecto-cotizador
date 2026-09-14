# Agente de normalización para cotización corporativa

Interpreta una carpeta mixta de licitación —mails, Excel, PDF— y produce
información normalizada, un diagnóstico auditable y dos carteras de escenario,
optimista y pesimista, en un Excel por licitación.

**El agente no cotiza.** Prepara información para que un actuario la evalúe. La
salida distingue siempre tres cosas: lo recibido, lo faltante y lo inferido.

> **Nota sobre el formato de este README.** La consigna pide «el README estándar
> de la materia». No tengo esa plantilla, así que esto sigue una estructura
> propia que cubre los seis requisitos. Si la plantilla existe, hay que
> reordenar el contenido a ese formato.

## Qué problema resuelve

Cada licitación corporativa llega como una carpeta con archivos heterogéneos:
padrones, antecedentes, pliegos del cliente, cotizaciones internas y mails. Sin
clasificar el rol de cada archivo, poblaciones distintas terminan sumadas como
si fueran una sola. Preparar esa información a mano lleva días y no deja rastro
de qué se supuso.

## Cómo funciona

Catorce pasos. El agente interviene en tres; el resto es determinístico.

| Paso | Quién lo resuelve |
| --- | --- |
| Reconocer el export del sistema propio por huella de columnas | Código, antes del agente |
| Proponer el rol y la confianza de cada fuente | **Agente** |
| Detectar la hoja de población y mapear columnas | Código; **agente** solo si el nombre de columna no alcanza |
| Leer tablas cruzadas y detectar subpoblaciones | Código |
| Extraer detalles de cobertura de pliegos y comparativos | **Agente** |
| Propagar atributos en el grupo familiar | Código |
| Homologar provincia y plan contra catálogo | Código |
| Distribuir rangos etarios a edad entera | Código |
| Construir cruces inferidos | Código |
| Aplicar escenarios, controlar cierre, escribir el Excel | Código |

**El LLM no calcula.** No implementa reglas ni decisiones actuariales.

### Salida

Un Excel por licitación, ocho hojas de nombre y orden fijos: Información
recibida, Distribuciones recibidas, Diagnóstico, Supuestos, Coberturas, Cartera
recibida, Cartera optimista, Cartera pesimista.

Las hojas de cartera usan las cinco columnas y las denominaciones textuales
exactas de la plantilla aprobada, más `subpoblacion` y `alternativa`:

```
subpoblacion  alternativa  edad         provincia  plan        SITU  cantidad
unica         S1           01) 0 a 1    AMBA       01) S1         1  0.12345678901234
```

La cantidad del ejemplo es **inventada**. Las reales son decimales largos como
ese, porque las cantidades distribuidas no se redondean; pero una cantidad real
de una corrida real no se publica.

**Las alternativas de plan no se suman entre sí.** Nueve alternativas de 100
personas son la misma población de 100 cotizada de nueve formas, no 900. El
total de la licitación es la suma de las subpoblaciones dentro de *una*
alternativa. Cada hoja de cartera lo advierte en su primera fila.

## Las tres corridas

Tres licitaciones reales, completas y sin recortar.

| Caso | Fuentes | Personas | Camino | Alternativas | Coberturas |
| --- | --- | --- | --- | --- | --- |
| A | 11 | no publicada | padrón individual | 9 | 124 |
| B | 11 | no publicada | padrón individual | 9 | 23 |
| C | 13 | no publicada | agregado + cruce condicionado | 18 (2 subpobl. × 9) | 26 |

[`corridas/`](corridas/) contiene evidencia **anonimizada y parcial** de esas
corridas. Las salidas originales no se publican y **no están reemplazadas** por
ese material; ver **Limitaciones de la evidencia pública** más abajo.

## Puesta en marcha

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/precomputar_referencia.py
.venv/Scripts/python -m unittest discover -s tests
.venv/Scripts/python scripts/procesar_licitacion.py "<carpeta de licitación>" caso_x
```

El precómputo recorre la referencia una sola vez, tarda cerca de un minuto y
deja `cache/distribucion_edad.csv`. Verifica además que el agrupamiento etario
de la referencia siga siendo el inspeccionado, y falla si cambió.

**60 tests.** Los de cálculo son sintéticos y corren en un clon limpio. Los que
dependen de datos locales se saltean solos.

## Datos

**Los datos reales no están en el repositorio y no deben commitearse.** Son
datos personales de empleados de terceros, alcanzados por la Ley 25.326. Ver la
entrada «Política de datos y de documentación» en [DECISIONES.md](DECISIONES.md).

Para correr hacen falta, locales y no versionados:

- `Referencia/referencia_cartera_corpo_2026_08_28.xlsx`
- `Referencia/Escenarios_proporcion_ST.xlsx`
- `Referencia/referencia_tabla_a_completar.xlsx` — plantilla de la cartera
- `Ejemplos input de cotizaciones/` — el corpus de prueba
- `anonimizacion.local.json` — mapa de seudónimos, solo para generar evidencia

## Reproducibilidad

Hay que distinguir dos cosas que no se reproducen igual.

**Reproducción determinística de cálculos.** Los pasos de normalización,
distribución etaria, cruces, escenarios y controles son determinísticos: con los
mismos insumos producen exactamente los mismos números. Los controles de cierre
con tolerancia 1e-6 lo verifican en cada corrida.

**Repetición del modelo.** Los pasos donde interviene el agente —clasificar
fuentes, mapear columnas, extraer coberturas— **no** son determinísticos. Una
re-corrida puede clasificar distinto. Por eso cada llamada se graba con su
prompt, su respuesta literal, el modelo, los tokens y el costo.

### Huella del código

`git rev-parse HEAD` **no identifica el código de una corrida** cuando hay
cambios sin commitear, que es el caso de estas tres. Cada manifiesto guarda:

- `digest_codigo`: sha256 agregado de los 18 archivos de código y prompt usados.
- `archivos`: sha256 de cada uno por separado.
- `git_sha` y `git_arbol_limpio`, con una nota explícita cuando el árbol está
  sucio.

Eso permite afirmar que dos corridas usaron el mismo código sin atribuirlas a un
commit que no las contiene. La huella está en
[`corridas/<caso>/huella_codigo.json`](corridas/).

Cada manifiesto guarda además el sha256 de cada archivo de entrada, de la tabla
de escenarios y del cache de distribución etaria.

## Análisis económico

Cifras **medidas** en las tres corridas de la versión `v2`, tal como las reporta
el CLI. No hay estimaciones inventadas ni comparaciones con otros modelos.

| Caso | Llamadas | Entrada total | Entrada nueva | Caché creación | Caché lectura | Salida | USD estimado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 4 | 190.888 | 36 | 99.620 | 91.232 | 21.184 | 0,3899 |
| B | 4 | 131.179 | 36 | 39.911 | 91.232 | 9.694 | 0,1534 |
| C | 2 | 90.296 | 18 | 44.662 | 45.616 | 8.005 | 0,1666 |
| **Total** | **10** | **412.363** | **90** | **184.193** | **228.080** | **38.883** | **0,7099** |

Promedio por corrida: **USD 0,2366**, 128 segundos, 3,3 llamadas.

### Cómo leer estas cifras

1. **Es costo estimado a precio de lista, no cobro efectivo.** `total_cost_usd`
   lo calcula la herramienta a tarifa pública. El cobro real depende del plan
   contratado de la cuenta, y no lo verifiqué contra ninguna factura.
2. **El 99,98% de la entrada es caché.** Solo 90 tokens de 412.363 son entrada
   nueva. Caché de creación y caché de lectura tienen precios distintos entre sí
   y distintos del token de entrada normal, así que multiplicar el total de
   entrada por una tarifa única da un número equivocado.
3. **Desglose faltante:** el costo por corrida viene agregado; el CLI no informa
   cuánto del costo corresponde a cada categoría de token. No lo puedo separar.
   Las tres primeras corridas (versión previa a `v2`) tampoco guardaron el
   desglose de caché; por eso las cifras de arriba son solo de `v2`.
4. **Parte del costo no es del contrato.** El CLI inyecta su propio prompt de
   sistema además del nuestro. No medí cuánto costaría lo mismo por API directa
   y **no afirmo que sería más barato**.

### Proyección

Con fórmulas y supuestos explícitos, porque el volumen real no me consta.

```
costo_anual ≈ L × R × c

L = licitaciones por año
R = corridas por licitación (≥ 1: cada corrección humana vía overrides re-corre)
c = costo estimado por corrida = USD 0,2366   (medido, n = 3)
```

| L | R | Costo anual estimado (USD) |
| --- | --- | --- |
| 12 | 2 | 5,68 |
| 50 | 2 | 23,66 |
| 100 | 3 | 70,98 |

Supuestos: que el costo por corrida se mantiene, que las licitaciones futuras
tienen un volumen de fuentes comparable, y que el precio de lista no cambia.
**`L` y `R` hay que confirmarlos con el área**; los valores de la tabla son
ilustrativos.

### Elección de modelo

`claude-haiku-4-5`, el más chico disponible en el backend. Las tareas que hace
el agente son clasificación y extracción estructurada sobre texto acotado, no
razonamiento de varios pasos. Resolvió correctamente las 35 fuentes de las tres
licitaciones, incluidos los casos difíciles. No probé modelos mayores: **no hay
comparación medida** y no afirmo que un modelo más grande no mejoraría algo.

## Gobierno y riesgo

### Qué toca el sistema y con qué permisos

| Sistema | Acceso | Alcance |
| --- | --- | --- |
| Carpeta de licitación (disco local) | **Lectura** | Solo la carpeta indicada por argumento |
| `Referencia/` (disco local) | **Lectura** | Tres archivos de referencia |
| `cache/`, `output/`, `runs/` (disco local) | **Escritura** | Solo dentro del repositorio |
| Claude Code CLI → API de Anthropic | **Comunicación saliente** | Envía fichas de archivo y texto de documentos; recibe texto |

**El sistema no está aislado de la red.** El paso agéntico envía contenido a un
servicio externo a través del binario de Claude Code. Lo que se envía:

- Nombres de archivo, fechas, tamaños, nombres de hoja y encabezados de columna.
- Asuntos, remitentes y un recorte del cuerpo de los mails.
- Texto de los PDF y de las hojas de planilla con contenido de cobertura, que
  incluye **el pliego del cliente**.

Lo que **no** se envía: filas de datos de los padrones. Ninguna fila con datos
personales sale del equipo. Esa restricción está en el código, no solo en el
prompt: la ficha que se arma para el modelo no incluye contenido de filas.

No toca Outlook, ni el datawarehouse, ni ningún sistema de producción. No
escribe fuera del repositorio.

### Qué puede salir mal

| Falla | Qué pasa | Detección |
| --- | --- | --- |
| Clasificar mal la fuente de población | La cartera se construye sobre el archivo equivocado | Diagnóstico lista las 35 fuentes con rol, confianza y origen; checklist humana punto 1 |
| Cruce inferido implausible | Cartera que cierra pero es actuarialmente absurda | Supuestos declara cada cruce y su condicionamiento; checklist punto 6 |
| Fuente parcialmente leída | Se pierde contenido sin que nadie lo note | Bloqueo nivel 2: se declara en Diagnóstico y Supuestos |
| Error de cierre | Cantidades que no conservan el total | Bloqueo nivel 1: excepción, no se produce el Excel |
| Insumo cambiado | Resultados sobre una referencia distinta | Bloqueo nivel 1: el precómputo falla si cambió el agrupamiento; hashes en el manifiesto |
| Fuga de datos al modelo | Datos personales salen del equipo | El armado de la ficha excluye filas; revisable en los prompts grabados |

Los tres niveles de bloqueo están en [`docs/handoff_v0.md`](docs/handoff_v0.md)
§9.

### Revisión humana

Automático, sin intervención: inventario, lectura, reconocedor determinístico,
homologación, distribución etaria, escenarios, controles y escritura.

**Requiere revisión humana antes de usar la salida** —los seis puntos de la
checklist de aceptación, §10.3 del handoff—: la clasificación de fuentes, la
resolución de conflictos, la magnitud de los reescalados, los faltantes
declarados, las homologaciones aplicadas y omitidas, y la plausibilidad de los
cruces inferidos.

Las correcciones se cargan en un Excel de overrides y se vuelve a correr.

> La consigna pide expresar la supervisión con el vocabulario L0–L4 del curso.
> **No tengo esa definición** y no la invento. Lo de arriba describe qué hace
> solo el sistema y qué revisa una persona; falta mapearlo a esa escala.

### Quién firma

**Antonio Morelli**, autor del sistema, firma cada corrida. Ninguna salida se
usa para cotizar sin su aprobación explícita sobre las hojas Diagnóstico y
Supuestos, aplicando los seis puntos de la checklist.

El sistema no aprueba nada por sí mismo: produce, declara y se detiene.

## Limitaciones de la evidencia pública

Esta sección es una declaración de incumplimiento parcial, no un descargo.

### Qué exige la consigna y qué hay

El requisito 2 pide **tres corridas reales guardadas tal como salieron**, de
modo que un tercero pueda reconstruir qué pasó en cada una. Las tres corridas
existen y son reales, pero **sus salidas no están en el repositorio**.

`corridas/` contiene descripciones de las corridas: inventario de entradas con
sus hashes, controles ejecutados, conteos, huella de código y respuestas del
modelo anonimizadas. **Eso no es la salida.** Un resumen de una corrida no
permite reconstruirla al nivel que pide la consigna: no se puede verificar una
cantidad, ni auditar una fila, ni revisar una homologación concreta.

**Publicar los totales de población tampoco resolvería esto.** La limitación no
es que falten unos números: es que faltan los artefactos que el requisito pide.
Por eso los totales siguen sin publicarse y eso no cambia el estado del
requisito.

Con lo que hay en el repositorio público, el requisito 2 está **parcialmente
cumplido**.

### Por qué no se publican

| Artefacto | Motivo |
| --- | --- |
| Excel de salida | La hoja Información recibida tiene una fila por persona con legajo, edad y provincia: datos personales seudonimizados de empleados de terceros, alcanzados por la Ley 25.326. Diagnóstico y Supuestos traen nombres de cliente; Coberturas trae texto literal del pliego. |
| Prompts enviados al modelo | Contienen nombres de archivo, asuntos y remitentes de mail, y el texto del pliego del cliente. |
| Respuestas de coberturas | Citan textualmente el pliego del cliente. |
| Cifras de población | Son el tamaño de la cartera de un cliente identificable en una licitación viva. No hay autorización para difundirlas. |
| Corridas originales en `runs/` | Los manifiestos traen nombres de archivo con el cliente. |

Quitar nombres no alcanza para anonimizar. Durante la revisión aparecieron tres
fugas que el mapa de seudónimos no cubría:

1. Un nombre de persona **con acento** que el mapa tenía sin acento.
2. Un **diferencial de precio** que el modelo citó al justificar una
   clasificación.
3. El **conteo de filas** de la hoja Información recibida, que es una fila por
   persona y por lo tanto equivale a publicar el tamaño de la cartera.

Las tres están corregidas. La tercera es la más instructiva: el dato no estaba
en ningún campo llamado «población».

### Cómo puede revisar los originales un evaluador autorizado

Los originales se conservan **sin modificación** en el equipo del responsable:

| Qué | Dónde |
| --- | --- |
| Excel de salida de las tres corridas | `output/caso_{a,b,c}_<timestamp>.xlsx` |
| Manifiestos completos, con hashes y huella de código | `runs/caso_{a,b,c}/<timestamp>/manifiesto.json` |
| Prompts y respuestas literales del modelo | `runs/caso_{a,b,c}/<timestamp>/llamadas_modelo.json` |
| Corpus de entrada | `Ejemplos input de cotizaciones/` |
| Mapa de seudónimos usado para la evidencia pública | `anonimizacion.local.json` |

Procedimiento propuesto, **sujeto a la autorización correspondiente**, que
todavía no está otorgada:

1. El evaluador solicita la revisión al responsable que firma.
2. El responsable gestiona la autorización interna que corresponda, por tratarse
   de datos personales de terceros y de documentación comercial de clientes en
   licitaciones vivas. Esa autorización no depende de este proyecto.
3. Con la autorización, la revisión se hace **en sesión asistida sobre el equipo
   del responsable**, sin copiar archivos.
4. Correspondencia verificable: cada archivo de entrada tiene su sha256 en el
   manifiesto y en `corridas/<caso>/entrada.md`, y cada prompt y respuesta tiene
   su sha256 en `corridas/<caso>/llamadas_modelo.json`. El evaluador puede
   confirmar que lo que ve en privado es exactamente lo que la evidencia pública
   describe, sin que nada confidencial haya salido del equipo.
5. La huella de código (`huella_codigo.json`) permite verificar que la corrida
   revisada usó el código publicado.

Mientras esa autorización no exista, el requisito queda parcialmente cumplido y
así está declarado.

## Documentación

- [DECISIONES.md](DECISIONES.md) — la historia del proceso: 21 entradas con
  iteraciones, hipótesis refutadas, errores y correcciones.
- [docs/handoff_v0.md](docs/handoff_v0.md) — contrato de implementación.
- [prompts/](prompts/) — los contratos del agente realmente usados.
- [corridas/](corridas/) — evidencia anonimizada de las tres corridas.
- `docs/interno/` — detalle con nombres de cliente y cifras reales. No se
  commitea.

## Alcance

**Incluye:** carpeta mixta, mails, Excel y PDF; clasificación de fuentes;
normalización y homologación; diagnóstico de faltantes; cruces inferidos;
distribución etaria contra la referencia; escenarios de situación terapéutica;
Excel de ocho hojas.

**No incluye:** extracción de contenido desde imágenes (sin OCR ni visión);
costo médico esperado; valoración económica de coberturas; Outlook; DWH;
interfaces; arquitectura multiagente.

## Material del curso que falta

Señalado sin inventar definiciones:

- **Las seis piezas del contrato** (system prompt + user prompt). Los prompts de
  `prompts/` son los realmente usados, pero no están estructurados contra esa
  lista porque no la tengo.
- **El vocabulario L0–L4** de supervisión humana.
- **La plantilla del README estándar de la materia.**
