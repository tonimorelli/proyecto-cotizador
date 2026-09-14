# Bitácora de decisiones

Este archivo registra las decisiones reales tomadas durante el desarrollo. No debe reescribirse posteriormente para que el proceso parezca más prolijo.

## 2026-09-03 — Alcance de la v1

**Versión / etapa:** v1 / Etapa 0

**Contexto:** Se definió el primer entregable del sistema de automatización actuarial.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** El tiempo disponible es de dos semanas de atención parcial.

**Decisión:** Automatizar interpretación de Excel heterogéneos, normalización, aplicación de reglas, estimación de costo médico esperado, controles y generación de Excel. Dejar fuera cartera conocida, pricing comercial, Outlook, conexión directa al DW, UI y multiagentes.

**Alternativas descartadas:** Incluir cartera conocida, pricing comercial, integraciones externas, interfaz y multiagentes en la v1.

**Motivo:** Prioridad por un flujo completo, probado y documentado dentro de dos semanas de atención parcial.

**Impacto en el sistema:** La v1 se concentra en una cartera nueva y en un resultado auditable de costo médico esperado.

**Tema abierto:** N/A

## 2026-09-03 — Arquitectura mínima

**Versión / etapa:** v1 / Etapa 0

**Contexto:** Se definió la separación de responsabilidades para la v1.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** N/A

**Decisión:** Usar un solo agente para interpretación, herramientas determinísticas para transformaciones y cálculos, y revisión humana para criterio actuarial material.

**Alternativas descartadas:** Arquitectura multiagente y LLM realizando cálculos.

**Motivo:** Simplicidad, reproducibilidad, trazabilidad y fácil debugging.

**Impacto en el sistema:** El LLM no implementará cálculos, reglas determinísticas ni decisiones actuariales materiales.

**Tema abierto:** N/A

## 2026-09-03 — Tratamiento de SITU

**Versión / etapa:** v1 / Etapa 0

**Contexto:** SITU requiere una definición para escenarios mínimo y máximo.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** Actualmente no existe una regla estándar defendible para mínimo/máximo.

**Decisión:** La v1 no debe inventar una regla para SITU; su definición requiere revisión actuarial hasta que exista una regla formal.

**Alternativas descartadas:** Inferir o asignar SITU de forma automática sin regla formal.

**Motivo:** Evitar decisiones actuariales no defendibles.

**Impacto en el sistema:** Los casos ambiguos de SITU deberán detenerse para revisión humana.

**Tema abierto:** Formalizar una regla actuarial aprobada para SITU.

## 2026-09-03 — Estrategia de implementación

**Versión / etapa:** v1 / Etapa 0

**Contexto:** Se estableció el orden de construcción de la v1.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** N/A

**Decisión:** Primero se construirá y validará el motor determinístico; después se incorporará el componente agéntico para interpretar inputs.

**Alternativas descartadas:** Construir primero el componente agéntico.

**Motivo:** Validar la base reproducible y auditable antes de incorporar interpretación semántica.

**Impacto en el sistema:** La implementación posterior empezará por casos de referencia y comportamiento determinístico.

**Tema abierto:** N/A

## 2026-09-13 — Alcance de la V0

**Versión / etapa:** V0 / cierre de planificación

**Contexto:** Se cerró la planificación del agente de normalización. El alcance evolucionó respecto de la entrada del 2026-09-03.

**Hipótesis:** N/A

**Qué probé:** Se revisó el corpus de ejemplos: 14 mails, 11 XLSX, 7 XLS y 3 PDF en tres licitaciones.

**Qué ocurrió:** El corpus no contiene ninguna imagen, ni adjunta ni embebida. Los mails son solo cuerpo HTML con los adjuntos ya extraídos a disco.

**Problema encontrado:** El alcance obligatorio incluía lectura de imágenes sin ningún caso real que la respaldara. La entrada del 2026-09-03 incluía además la estimación de costo médico esperado dentro de la v1.

**Decisión:** V0 normaliza información, construye cruces inferidos y entrega tres carteras en un Excel por licitación. La estimación de costo médico esperado pasa a extensión opcional fuera del MVP. La lectura de imágenes queda fuera de V0.

**Alternativas descartadas:** Implementar lectura de imágenes contra un caso de prueba sintético. Mantener el costo médico esperado dentro del primer entregable.

**Motivo:** No construir capacidades sin evidencia de uso, y entregar primero la normalización documentada, que es el cuello de botella real.

**Impacto en el sistema:** El alcance de esta entrada reemplaza el de la entrada «Alcance de la v1» del 2026-09-03 donde haya contradicción. El detalle vive en `docs/handoff_v0.md`.

**Tema abierto:** Reincorporar imágenes cuando exista una licitación real que las requiera.

## 2026-09-13 — Situación terapéutica y escenarios

**Versión / etapa:** V0 / cierre de planificación

**Contexto:** La entrada del 2026-09-03 dejó SITU sin regla y con detención para revisión humana. Se aportó una tabla de proporciones por grupo etario.

**Hipótesis:** Se había propuesto inferir situ desde la proporción de `marca_st` de la referencia corporativa.

**Qué probé:** Se calculó la proporción de ST por grupo etario desde la referencia de tres formas distintas y se comparó contra `Referencia/Escenarios_proporcion_ST.xlsx`.

**Qué ocurrió:** Ninguna forma de cálculo reproduce la tabla. La más cercana, `ST / (Sanos + ST)`, queda consistentemente por encima de la columna Corporate. La tabla trae las fórmulas explícitas: Optimista es Corporate por 0,9 y Pesimista es Individuales por 1,1, verificado en las 21 filas.

**Problema encontrado:** La tabla es un insumo aprobado que no se puede auditar contra la referencia disponible.

**Decisión:** V0 aplica las columnas Optimista y Pesimista de la tabla, consumida como está y sin recalcular. Se valida solo su forma. Cuando una fuente informa situ real, se emiten tres carteras: recibida con el dato observado, más optimista y pesimista con la tabla aplicada a la cartera completa.

**Alternativas descartadas:** Inferir situ desde `marca_st`. Recalcular la tabla desde la referencia. Que el dato recibido reemplace a los escenarios y los dejara idénticos.

**Motivo:** Existe una regla aprobada por el área, y conservar las tres versiones permite comparar el dato observado contra los dos escenarios sin perder ninguno.

**Impacto en el sistema:** Reemplaza la entrada «Tratamiento de SITU» del 2026-09-03. SITU ya no detiene el proceso. El Excel de salida pasa de siete a ocho hojas.

**Tema abierto:** Documentar la procedencia de las columnas Individuales y Corporate, y con qué corte se calcularon.

## 2026-09-13 — Mapeo de edad a grupo etario

**Versión / etapa:** V0 / cierre de planificación

**Contexto:** La cartera objetivo usa edad entera de 0 a 100 y la tabla de escenarios usa 21 grupos etarios.

**Hipótesis:** N/A

**Qué probé:** Se recorrió la referencia corporativa completa y se calculó edad mínima y máxima por grupo etario.

**Qué ocurrió:** El grupo etiquetado «01) 0 a 1» contiene únicamente edad 0, y el grupo «02) 2 a 5» contiene las edades 1 a 5. Las etiquetas de los dos primeros grupos contradicen el contenido. El grupo «21) +» llega hasta edad 106. Las claves vienen con espacios de relleno.

**Problema encontrado:** Dos mapeos posibles y contradictorios entre edad y grupo etario.

**Decisión:** Usar la agrupación real de la referencia, no la etiqueta. Edad 0 al grupo 01 y edades 1 a 5 al grupo 02. Para edades de 96 a 100 se usa el grupo 21, cuyo valor la tabla fijó igual al del grupo 20. Las filas de referencia con edad mayor a 100 se excluyen.

**Alternativas descartadas:** Interpretar las etiquetas literalmente. Usar para 96 y más la proporción observada en la referencia, que es más alta. Marcar la discrepancia como decisión humana en cada licitación.

**Motivo:** La distribución etaria y la proporción de situ deben leerse con la misma clave. El tope en el grupo 21 fue una decisión deliberada al armar la tabla, y la cola por encima de 100 es despreciable.

**Impacto en el sistema:** El mapeo queda fijado en la sección 4.5 del handoff. Hay que normalizar espacios antes de unir las dos fuentes.

**Tema abierto:** Probar la distribución contra un rango etario recibido que cruce los límites de los grupos de referencia.

## 2026-09-13 — Fuentes, conflictos y homologación

**Versión / etapa:** V0 / cierre de planificación

**Contexto:** Cada licitación llega como carpeta mixta con padrones, antecedentes, documentos del cliente y cotizaciones internas posteriores.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** Sin clasificar el rol de cada archivo, fuentes distintas se confunden como una sola población. Y las denominaciones de provincia y plan no siempre entran en los catálogos objetivo.

**Decisión:** El agente clasifica el rol de cada archivo con un nivel de confianza y lo declara en Diagnóstico. Ante conflicto entre fuentes gana la mayor granularidad, primero padrón individual, después tabla agregada, después PDF y texto, y ante empate el archivo más reciente. Una denominación no homologable queda como «sin dato», con el valor original conservado, y no detiene el proceso.

**Alternativas descartadas:** Manifiesto manual obligatorio por licitación. Convención de nombres de archivo. Detener el proceso ante denominación desconocida. Mapeo automático por similitud de texto.

**Motivo:** Evitar un paso manual en cada licitación y evitar homologaciones silenciosas incorrectas. El agente no inventa mapeos, pero tampoco se bloquea por casos menores.

**Impacto en el sistema:** Un plan de otro financiador termina como «sin dato» y la cartera se expande a las nueve alternativas de plan. Todo conflicto se registra incluso cuando se resuelve solo.

**Tema abierto:** Las provincias ambiguas que aparezcan en las pruebas reales.

## 2026-09-13 — Totales incompatibles y control de cierre

**Versión / etapa:** V0 / cierre de planificación

**Contexto:** Los cruces inferidos se construyen desde distribuciones recibidas por separado, que pueden no sumar el mismo total.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** Un control de cierre estricto y un reescalado de totales son incompatibles si el control se aplica contra los totales originales.

**Decisión:** Elegir un total maestro con la prioridad de fuentes y reescalar proporcionalmente las demás distribuciones. El control de cierre es estricto, tolerancia relativa 1e-6, y se aplica contra el total maestro. La diferencia contra cada total original se reporta aparte como magnitud del ajuste.

**Alternativas descartadas:** Frenar ante cualquier discrepancia. Reescalar solo bajo un umbral. Entregar las distribuciones sin cruzar. Tolerancia absoluta de media cápita. Exigir cierre contra cada total original.

**Motivo:** Los cruces son obligatorios, así que frenar no es opción. Con tolerancia estricta, un desvío de cierre indica falla de la distribución y no redondeo.

**Impacto en el sistema:** Las cantidades no se redondean. El control corre por escenario y por alternativa de plan. Un error de cierre es error de software y debe fallar ruidosamente.

**Tema abierto:** N/A

## 2026-09-13 — Contrato de salida, trazabilidad y overrides

**Versión / etapa:** V0 / cierre de planificación

**Contexto:** La salida es el único producto del agente y tiene que ser auditable por un actuario.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** Sin trazabilidad al nivel de celda no se puede auditar un número. Y sin mecanismo de corrección, el trabajo humano se pierde en la siguiente corrida.

**Decisión:** Un Excel por licitación con ocho hojas de nombre y orden fijos. Cada fila de información lleva un `id_fuente` corto, resuelto en una tabla de fuentes dentro de Supuestos con archivo, hoja, rango, rol y confianza. Las correcciones humanas se cargan en un Excel de overrides por licitación, con hojas espejo de Diagnóstico, y se vuelve a correr.

**Alternativas descartadas:** Repetir archivo, hoja y rango en columnas de cada fila. Registrar solo el nombre del archivo. Editar a mano el Excel de salida. Overrides en YAML, JSON o CSV. No tener mecanismo de corrección en V0.

**Motivo:** Hojas legibles con trazabilidad completa, y un formato de corrección que un actuario completa sin tocar código.

**Impacto en el sistema:** La salida es reproducible: misma carpeta más mismo archivo de overrides produce el mismo Excel.

**Tema abierto:** La organización interna de las hojas que llevan varias tablas. Y si conviene emitir siempre la hoja de cartera recibida, incluso vacía, como se decidió para mantener estable el esquema.

## 2026-09-13 — Pruebas y criterios de aceptación

**Versión / etapa:** V0 / cierre de planificación

**Contexto:** Hacía falta fijar qué se prueba y cuándo una corrida es aceptable.

**Hipótesis:** N/A

**Qué probé:** Se revisó el contenido de las tres carpetas de ejemplo, incluidas las cotizaciones históricas que cada una contiene.

**Qué ocurrió:** Cada carpeta incluye el Excel de cotización que se produjo en su momento, pero esas cotizaciones incorporan criterio humano que V0 no reproduce.

**Problema encontrado:** No existe verdad de referencia para la cartera completada. Los números inferidos no tienen resultado correcto único.

**Decisión:** Las tres pruebas son las tres carpetas de ejemplo completas, identificadas como Caso A, Caso B y Caso C. El mapeo a clientes reales vive en `docs/interno/`. La aceptación combina verificación automática de cierre, dominios e integridad de las ocho hojas, con una checklist humana de seis puntos sobre Diagnóstico y Supuestos. V0 solo omite las hojas de cartera si no identifica ninguna fuente de población, y aun así escribe el Excel con Diagnóstico.

**Alternativas descartadas:** Recortar las carpetas a los archivos imprescindibles. Sustituir un ejemplo por un caso sintético. Exigir que la salida reproduzca la cotización histórica. Aceptar solo con verificación automática.

**Motivo:** Recortar las carpetas dejaría sin probar la clasificación de fuentes, que es la parte difícil. Y una cartera puede cerrar perfecto y ser actuarialmente absurda, así que la revisión humana no se puede eliminar.

**Impacto en el sistema:** Las cotizaciones históricas sirven como referencia de orden de magnitud, no como resultado esperado.

**Tema abierto:** El contenido definitivo de la checklist puede ajustarse después de la primera corrida real.

## 2026-09-13 — Politica de datos y de documentacion

**Versión / etapa:** V0 / arranque de implementación

**Contexto:** El repositorio es privado hoy y se piensa publicar más adelante.

**Hipótesis:** Alcanzaba con commitear los datos ahora y sanearlos antes de publicar.

**Qué probé:** Se auditó el estado de git: historia, objetos sueltos y remotos configurados.

**Qué ocurrió:** La historia está limpia, ningún archivo de datos fue commiteado nunca y no hay remoto configurado. Pero había datos reales como objetos inalcanzables dentro de `.git`, de un `git add` que después se deshizo.

**Problema encontrado:** La historia de git es permanente. Commitear los padrones ahora y sanearlos antes de publicar exige reescribir la historia, lo que cambia todos los SHA y deja copias en clones y forks. Los padrones son datos personales de empleados de terceros, alcanzados por la Ley 25.326.

**Decisión:** Los datos reales nunca entran al repositorio. Se ignoran `Ejemplos input de cotizaciones/`, `Referencia/`, `output/`, `runs/` y los archivos de bloqueo `~$`. La documentación se separa en dos niveles: `docs/` queda libre de nombres de cliente y de cifras reales, y `docs/interno/` concentra ese detalle y también se ignora.

**Alternativas descartadas:** Commitear en privado y reescribir la historia con filter-repo antes de publicar. Un segundo repositorio privado solo con los datos.

**Motivo:** La decisión es gratis ahora, porque la historia está limpia y no hay remoto. En cualquier otro momento cuesta una cirugía sobre la historia.

**Impacto en el sistema:** El repositorio queda publicable sin sanear nada. Hacen falta un manifiesto del corpus y fixtures anonimizados para que las pruebas sean reproducibles sin los datos.

**Tema abierto:** Generar el manifiesto y los fixtures anonimizados. Limpiar los objetos inalcanzables que quedaron en `.git`.

## 2026-09-13 — Reglas surgidas del spike de lectura

**Versión / etapa:** V0 / arranque de implementación

**Contexto:** Antes de construir el motor se hizo un spike para abrir los siete XLS y los tres PDF, que nunca se habían inspeccionado por dentro.

**Hipótesis:** Los XLS legacy podían estar protegidos o traer estructuras imposibles, y los PDF podían ser escaneos sin texto.

**Qué probé:** Lectura completa de los siete XLS con `xlrd`, de los XLSX de población con `openpyxl` y de los tres PDF con `pdfplumber`. Perfil de columnas con cardinalidad, sin volcar datos personales.

**Qué ocurrió:** Todo se lee. Ningún archivo protegido. Los tres PDF son texto nativo. Se descartó además una sospecha de corrupción de acentos: los datos están bien y lo que fallaba era la consola. Aparecieron seis situaciones que las reglas no cubrían.

**Problema encontrado:** Los archivos llamados padrón resultaron ser el export interno del sistema propio, con esquema fijo, y son la cartera vigente de la cuenta y no la población a cotizar. Los atributos del grupo familiar vienen informados solo en la fila del titular. Una licitación puede traer dos empresas con padrones separados. Una distribución puede cubrir solo a los titulares. Dos distribuciones observadas pueden compartir una dimensión. Y un PDF de licitación resultó ser un deck con la mayor parte del contenido en imágenes.

**Decisión:** Un reconocedor determinístico por huella de columnas captura el padrón interno antes que el agente y lo clasifica como antecedente. Los atributos declarados a nivel de grupo se propagan por su identificador, y eso se trata como lectura correcta del archivo, no como inferencia. Las subpoblaciones conviven en el mismo Excel con una columna propia y los controles corren por subpoblación. La distribución observada de un segmento se aplica al segmento no cubierto, marcada como inferida. Los cruces se construyen condicionados a la dimensión compartida cuando existe, y solo por independencia total cuando no. La homologación es insensible a mayúsculas, acentos y espacios, y un catálogo versionado de partidos del AMBA resuelve la ambigüedad entre AMBA y BUENOS AIRES cuando la fuente trae localidad.

**Alternativas descartadas:** Clasificar los padrones por nombre de archivo. Tratar los atributos de grupo como faltantes. Sumar las dos empresas en una sola cartera o emitir un Excel por empresa. Asignar AMBA por defecto a los familiares sin provincia. Suponer independencia total pudiendo condicionar.

**Motivo:** Todas estas situaciones aparecen en los casos reales de prueba, no son hipotéticas. Tratar la estructura jerárquica como faltante habría dejado casi toda una población sin provincia por un error de lectura.

**Impacto en el sistema:** El pipeline pasa de 13 a 14 pasos, con propagación como paso nuevo. Las hojas de cartera suman una columna de subpoblación. Las reglas 6.7 a 6.12 del handoff se renumeraron.

**Tema abierto:** Revisar si las 17 páginas sin texto del PDF de licitación del Caso B tienen especificaciones de cobertura o son portadas. De eso depende si hay que reabrir la decisión sobre imágenes.

## 2026-09-13 — Agrupamiento etario: se adoptan las etiquetas literales de la plantilla

**Versión / etapa:** V0 / implementación

**Contexto:** Apareció `Referencia/referencia_tabla_a_completar.xlsx`, la plantilla aprobada de la cartera de salida: 9.072 filas, grilla cartesiana de 21 grupos × 24 provincias × 9 planes × 2 SITU, con `cantidad` vacía. Usa etiquetas de grupo etario, no edades individuales.

**Hipótesis:** N/A

**Qué probé:** Se midió el impacto de la edad 1 sobre la referencia corporativa: es el 0,91% de la cartera, el 17% del grupo 02, y moverla al grupo 01 duplicaría ese grupo (×2,09). La tabla de escenarios asigna al grupo 02 una proporción de situ 5,6 veces la del grupo 01.

**Qué ocurrió:** Quedaron dos opciones incompatibles. Seguir el agrupamiento real de la referencia (01={0}, 02={1..5}) entrega un Excel cuya celda «2 a 5» contiene también a los de 1 año. Seguir las etiquetas literales (01={0,1}, 02={2..5}) entrega un Excel que dice la verdad sobre su contenido, pero rompe la coincidencia de clave con la referencia.

**Problema encontrado:** La recomendación técnica y la coherencia del entregable apuntaban a lados distintos.

**Decisión:** Opción 2. Se usan las etiquetas literales de la plantilla: el grupo `01) 0 a 1` contiene las edades 0 y 1. La tabla de escenarios se aplica según esas mismas etiquetas, como supuesto adoptado.

**Alternativas descartadas:** Conservar el agrupamiento de la referencia. Modificar la etiqueta de la plantilla, que es insumo aprobado.

**Motivo:** Decisión del responsable del proyecto, tomada con el impacto cuantificado a la vista.

**Impacto en el sistema:** El código tiene ahora dos agrupamientos con nombres distintos: `catalogos.grupo_etario` (salida, literal, se usa para todo cálculo) y `catalogos.grupo_referencia` (solo valida que el archivo de referencia no haya cambiado). Un test fija que difieren únicamente en la edad 1. El precómputo sigue fallando ruidosamente si la referencia cambia su agrupamiento interno.

**Tema abierto:** Pedir al área que corrija la etiqueta en una versión futura de la plantilla.

## 2026-09-13 — Corrección: afirmé una procedencia de la tabla de escenarios que no está verificada

**Versión / etapa:** V0 / implementación

**Contexto:** Al comparar las dos opciones de agrupamiento etario, se argumentó que el valor del grupo 01 de la tabla de escenarios «fue medido sobre una población de solo recién nacidos».

**Hipótesis:** N/A

**Qué probé:** Se buscó esa afirmación en el repositorio.

**Qué ocurrió:** La afirmación no tiene respaldo. El propio handoff §11 dice que la tabla no se reproduce desde la referencia corporativa y que su procedencia se desconoce. La afirmación quedó solo en la conversación y nunca llegó a ningún archivo.

**Problema encontrado:** Se presentó como hecho verificado algo que el proyecto tiene documentado como desconocido.

**Decisión:** La tabla de escenarios se aplica según sus propias etiquetas de grupo, como **supuesto adoptado**. No se afirma nada sobre cómo se calcularon sus proporciones. Queda anotado así en el código y en el handoff §14.

**Alternativas descartadas:** Dejar la afirmación como estaba.

**Motivo:** El proyecto entero se apoya en distinguir lo recibido de lo inferido. Una afirmación de procedencia sin respaldo contradice eso.

**Impacto en el sistema:** Documental. Ningún número cambia.

**Tema abierto:** Documentar la procedencia real de las columnas Individuales y Corporate.

## 2026-09-13 — Edad mayor a 100 en la población recibida

**Versión / etapa:** V0 / implementación

**Contexto:** El padrón del Caso A trae una persona de 114 años. El dominio declarado de la cartera es 0 a 100.

**Hipótesis:** N/A

**Qué probé:** Se contó cuántas personas exceden el dominio: una sola en la poblacion del caso.

**Qué ocurrió:** Descartarla habría roto el cierre contra el total de la fuente por una cápita, sin dejar rastro.

**Problema encontrado:** El dominio del handoff no contempla el dato real.

**Decisión:** No se descarta a nadie. La edad original se conserva en Información recibida, el cálculo y la asignación de escenario usan edad 100, y la salida agrupa en `21) +`. La transformación se registra en Supuestos y un control verifica que la cartera contenga todas las filas leídas menos las ilegibles.

**Alternativas descartadas:** Descartar la fila. Dejar la edad original en el cálculo. Aplicar la misma regla a la referencia corporativa.

**Motivo:** Perder una persona en silencio es peor que declarar una transformación.

**Impacto en el sistema:** La regla aplica solo a la población recibida. La referencia corporativa sigue excluyendo las edades mayores a 100 de la distribución etaria, como estaba.

**Tema abierto:** N/A

## 2026-09-13 — Formato de las hojas de cartera

**Versión / etapa:** V0 / implementación

**Contexto:** La plantilla aprobada tiene cinco columnas fijas y no trae `subpoblacion` ni `alternativa`, que el modelo de datos necesita para que el doble conteo sea imposible.

**Hipótesis:** N/A

**Qué probé:** Se generó una licitación de juguete de 100 personas sin plan informado y se midió el volumen de cada presentación posible.

**Qué ocurrió:** Repetir la grilla completa por alternativa da 81.648 filas por hoja, de las cuales el 99,93% serían ceros. Además se detectó que cuando ninguna fuente informa plan, las nueve alternativas son numéricamente idénticas y solo cambia la etiqueta de plan.

**Problema encontrado:** Respetar la plantilla al pie de la letra producía un archivo inmanejable.

**Decisión:** Las cinco columnas y las denominaciones textuales exactas de la plantilla, más `subpoblacion` y `alternativa` al frente. Se omiten las combinaciones con cantidad cero. Cuando falta plan se mantienen las nueve alternativas explícitas, y la repetición de cantidades es intencional. Cada hoja abre con una nota que advierte que las alternativas no se suman.

**Alternativas descartadas:** Repetir la grilla completa por alternativa. Bloques rotulados apilados, que rompen la tabla rectangular. Colapsar a un solo bloque cuando no hay plan observado.

**Motivo:** La hoja es insumo de un actuario que filtra por alternativa; que cada alternativa exista completa evita que alguien concluya que faltan filas.

**Impacto en el sistema:** Handoff §7.3. Las tres corridas usan este formato.

**Tema abierto:** N/A

## 2026-09-13 — Tres fallas: dos las encontró un control, una la encontró una persona

**Versión / etapa:** V0 / implementación

**Contexto:** Se construyó el núcleo de cartera con controles de cierre estrictos antes de correr nada real.

**Hipótesis:** N/A

**Qué probé:** Las tres licitaciones reales, más una suite de 60 tests sintéticos.

**Qué ocurrió:** Tres fallas, de tres tipos distintos.

1. **El total de licitación sumaba las alternativas de plan.** Devolvía nueve veces la población real, porque acumulaba las nueve alternativas como si fueran poblaciones distintas. Peor: la prueba que lo cubría comparaba contra esa misma suma, así que consagraba el error en vez de detectarlo. Lo detectó el responsable del proyecto leyendo el resumen, no el código.

   Reproducido en un caso sintético, que es el que quedó como test de regresión: una licitación **inventada** de 100 personas sin plan informado devolvía 900. Los totales reales de la licitación no se publican: como el total mal calculado era exactamente nueve veces la población, publicarlo equivale a publicar el tamaño de la cartera dividiendo por nueve.

2. **El control de cierre por fila comparaba un agregado contra una fila individual.** En un padrón individual muchas personas comparten la clave (edad, provincia, plan), así que el agregado por clave es mayor que cualquiera de sus filas. El control levantó `ErrorDeCierre` en la primera corrida real y no dejó producir el Excel. Funcionó como debía: un error de software falló ruidosamente.
3. **Se concluyó que el Caso C no tenía detalles de cobertura** habiendo revisado únicamente la grilla de cotización. El comparativo de planes del mismo caso tiene decenas de miles de caracteres de detalle de cobertura repartidos en doce hojas. Lo detectó el responsable del proyecto.

Hubo además un error de verificación, no de producto: al releer el Excel para validarlo se usó un desplazamiento de encabezado equivocado, se perdieron dos filas y el total informado quedó por debajo del correcto. El archivo siempre estuvo bien; el informe no.

**Problema encontrado:** Los controles automáticos atrapan lo que saben mirar. Un total mal definido, una conclusión sacada de material incompleto y un script de verificación mal escrito los encontró una persona.

**Decisión:** (1) El total de licitación es la suma de subpoblaciones dentro de una alternativa, con verificación de que las nueve cubren la misma población, más dos tests de regresión con el caso 100 contra 900. (2) El control agrega por clave antes de comparar. (3) La extracción de coberturas recorre todas las fuentes con rol de documento del cliente o de cotización interna, detectando hojas con contenido de cobertura, y declara la procedencia de cada detalle.

**Alternativas descartadas:** Ajustar la prueba al comportamiento observado en el caso 1.

**Motivo:** Un control que valida el comportamiento actual en vez del correcto no es un control.

**Impacto en el sistema:** El Caso C pasó de 1 a 26 detalles de cobertura y el Caso A de 48 a 124. Las corridas anteriores a la corrección se conservan bajo su propia marca de tiempo.

**Tema abierto:** El detector de hojas con cobertura busca la palabra «cobertura»; no está probado contra un comparativo que no la use.

## 2026-09-13 — Backend del modelo: binario de Claude Code

**Versión / etapa:** V0 / implementación

**Contexto:** La capa agéntica necesita un modelo y el entorno no tiene clave de API, ni archivo `.env`, ni SDK instalado.

**Hipótesis:** N/A

**Qué probé:** Se verificó que el binario de Claude Code responde en modo no interactivo con salida JSON y contabilidad de tokens y costo.

**Qué ocurrió:** Funciona. El primer intento con el pliego completo falló con `WinError 206`: el prompt de 51 KB supera el límite de línea de comandos de Windows. Se pasó a enviarlo por entrada estándar.

**Problema encontrado:** No hay API disponible y no se va a incorporar.

**Decisión:** El cliente encapsula el binario detrás de la misma interfaz que tendría un cliente de API. Modelo `claude-haiku-4-5`. Toda llamada registra prompt, respuesta literal, modelo, tokens con desglose de caché, costo estimado y duración.

**Alternativas descartadas:** Habilitar una API. Prescindir de la capa agéntica.

**Motivo:** Decisión del responsable del proyecto.

**Impacto en el sistema:** El CLI inyecta su propio prompt de sistema, así que el conteo de entrada incluye tokens que no son del contrato del agente. No se midió cuánto costaría por API directa y no se afirma que sería más barato.

**Tema abierto:** N/A

## 2026-09-13 — Una llamada al modelo que no aportaba, y el orden que la evitó

**Versión / etapa:** V0 / implementación

**Contexto:** El Caso C llega sin padrón individual. El pipeline intentaba primero el reconocimiento por nombre de columna, después pedía al modelo que mapeara columnas, y recién después probaba el camino agregado.

**Hipótesis:** N/A

**Qué probé:** La primera corrida del Caso C.

**Qué ocurrió:** Se gastaron dos llamadas al modelo mapeando columnas de planillas que no eran padrones, 494.367 tokens de entrada y USD 0,13 estimados, para descartarlas. El camino agregado, que es determinístico, las habría resuelto sin consultar nada.

**Problema encontrado:** El orden de los intentos ponía una llamada al modelo antes de un reconocedor determinístico.

**Decisión:** El camino agregado se prueba antes de pedirle al modelo que mapee columnas. El mapeo por modelo queda como último recurso.

**Alternativas descartadas:** Dejar el orden como estaba.

**Motivo:** No se le pregunta al modelo lo que el código ya sabe resolver.

**Impacto en el sistema:** El Caso C pasó de tres llamadas a una en esa etapa.

**Tema abierto:** N/A

## 2026-09-13 — Dos revisiones de fuentes antes de la entrega

**Versión / etapa:** V0 / implementación

**Contexto:** Quedaban dos fuentes mal tratadas al cerrar las tres corridas.

**Hipótesis:** N/A

**Qué probé:** Se abrieron y leyeron las dos, a mano.

**Qué ocurrió:** (a) una planilla comparativa del Caso B del Caso B había quedado sin rol. La causa era del lector, no del agente: tomaba siempre la fila 0 como encabezado, y esa planilla tiene el encabezado real en la fila 3, debajo de dos filas de título. El agente recibía una ficha vacía. (b) El comparativo de planes del Caso C sí tenía detalles de cobertura, en hojas que no se estaban mirando.

**Problema encontrado:** Una fuente sin clasificar y una conclusión de ausencia sacada de material incompleto.

**Decisión:** El lector detecta el encabezado como la fila con más celdas de texto entre las primeras doce. La recolección de coberturas recorre planillas además de PDF. Con eso ninguna fuente del corpus queda sin rol.

**Alternativas descartadas:** Dejar la fuente sin clasificar y declararla para revisión humana.

**Motivo:** Una fuente sin leer no es una fuente sin contenido.

**Impacto en el sistema:** Se generó la versión `v2` de las tres corridas. Las originales se conservan.

**Tema abierto:** Contenido real de una planilla comparativa del Caso B: es una comparación de débitos y créditos de una cuenta distinta y mucho más chica que la licitación, con fecha **anterior** a la invitación a cotizar. El agente le asignó «cotización interna posterior» con confianza media; el calificativo «posterior» no corresponde por la fecha. No cambia ningún número —no aporta población y no tiene texto de cobertura— pero el rol es discutible y queda para revisión humana.

## 2026-09-13 — Evidencia pública: qué se publica, qué no, y quién firma

**Versión / etapa:** V0 / preparación de la entrega

**Contexto:** La consigna pide tres corridas reales guardadas tal como salieron, y el repositorio va a ser público. Los datos son padrones de empleados de terceros y pliegos de clientes en licitaciones vivas.

**Hipótesis:** Que anonimizar nombres de cliente y de persona alcanzaba para poder publicar la evidencia de las corridas.

**Qué probé:** Se generó la evidencia pública con un mapa de seudónimos y después se auditó el resultado buscando fugas: términos del mapa con y sin acento, correos, rutas absolutas, porcentajes, importes y toda cifra de cuatro o más dígitos.

**Qué ocurrió:** Aparecieron tres fugas que el mapa no cubría.

1. Un nombre de persona con acento que el mapa tenía sin acento. El anonimizador era insensible a mayúsculas pero no a acentos.
2. Un diferencial de precio que el modelo citó al justificar una clasificación. Una cifra comercial identifica una negociación aunque el cliente esté seudonimizado.
3. El conteo de filas de la hoja Información recibida. Es una fila por persona, así que publicarlo equivale a publicar el tamaño de la cartera del cliente. No estaba en ningún campo llamado «población».

**Problema encontrado:** La hipótesis era falsa. Anonimizar nombres no alcanza, y la tercera fuga muestra por qué: el dato identificatorio puede estar en un conteo estructural que nadie clasificaría como dato.

**Decisión:** Las salidas originales no se publican. `corridas/` contiene descripciones de las corridas —inventario con hashes, controles, conteos no personales, huella de código y respuestas del modelo anonimizadas— y se declara explícitamente que **eso no reemplaza a la salida original**. Las cifras de población quedan sin publicar (`publicar_cifras: false`). El requisito 2 de la consigna queda declarado como **parcialmente cumplido**, no como cumplido. Se documenta un procedimiento de revisión asistida para un evaluador autorizado, sujeto a una autorización que todavía no existe.

**Alternativas descartadas:** Publicar los totales de población. Se evaluó y se descartó: no resuelve la limitación, porque lo que falta no son números sino los artefactos que el requisito pide, y sí agrega exposición del volumen de tres cuentas reales.

**Motivo:** Decisión del responsable. Declarar un incumplimiento parcial con precisión vale más que presentar un resumen como si fuera la salida exigida.

**Impacto en el sistema:** El anonimizador es insensible a acentos y depura porcentajes, importes y cifras largas. El conteo de filas de las hojas con una fila por persona queda detrás del mismo flag que las cifras. La auditoría de fugas es parte del procedimiento de generación.

**Tema abierto:** La autorización interna para que un evaluador revise los originales. No depende de este proyecto.

## 2026-09-13 — Responsable de firmar las corridas

**Versión / etapa:** V0 / preparación de la entrega

**Contexto:** El requisito de gobierno pide nombrar quién firma el resultado, y la sección quedaba pendiente.

**Hipótesis:** N/A

**Qué probé:** N/A

**Qué ocurrió:** N/A

**Problema encontrado:** La checklist de aceptación define qué se revisa, pero ningún documento decía quién es responsable de aprobar una corrida antes de que su salida se use.

**Decisión:** Antonio Morelli, autor del sistema, firma cada corrida. Ninguna salida se usa para cotizar sin su aprobación explícita sobre las hojas Diagnóstico y Supuestos, aplicando los seis puntos de la checklist.

**Alternativas descartadas:** Dejarlo pendiente hasta definirlo con el área.

**Motivo:** Un sistema que produce información para decisiones actuariales no puede entregarse sin un responsable nombrado.

**Impacto en el sistema:** El sistema no aprueba nada por sí mismo: produce, declara y se detiene. Queda documentado en el README.

**Tema abierto:** Si el sistema pasa a uso regular, revisar si el rol que firma debe ser el del área de Cotizaciones Corporate en lugar del autor.
