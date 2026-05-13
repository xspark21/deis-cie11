# Metodología de mapeo DEIS → CIE-11

## Motivación

Los registros históricos de urgencia del DEIS contienen una mezcla de glosas
clínicas, categorías operacionales, subtotales y encabezados administrativos
dentro de una misma columna (`GlosaCausa`).

Ejemplos reales:

- `SECCIÓN 1. TOTAL ATENCIONES DE URGENCIA`
- `- Causas sistema circulatorio (I00-I99)`
- `Trastornos del Humor (Afectivos) (F30-F39)`
- `COVID-19, VIRUS IDENTIFICADO`

La estructura original no distingue explícitamente qué filas representan causas
clínicas reales y cuáles corresponden a agregaciones operacionales o elementos
del formulario SADU. Antes de analizar los registros fue necesario reconstruir
esa semántica y separar ambos niveles.

El objetivo del proyecto fue construir una capa de estructuración sobre los datos
históricos del DEIS utilizando referencias compatibles con CIE-11, manteniendo
la mayor trazabilidad posible respecto al registro original.

No se buscó reinterpretar diagnósticos ni generar información clínica nueva.
El trabajo consiste únicamente en remapear y organizar lo ya existente.

---

# Principios utilizados

## 1. No inferir información ausente

Si el registro original no distingue etiologías, subtipos o mecanismos clínicos,
el mapeo tampoco los distingue.

Por ejemplo, `Crisis obstructiva bronquial` no permite separar:

- asma,
- EPOC,
- broncoespasmo viral,
- ni otras causas respiratorias.

En esos casos el resultado permanece en categorías agregadas compatibles con
el nivel real de especificidad disponible.

El objetivo fue evitar sobreinterpretar el dato administrativo.

---

## 2. Priorizar coherencia semántica antes que exactitud artificial

Algunas glosas del DEIS no tienen equivalencia exacta en CIE-11.

En esos casos se priorizó:

- preservar el significado epidemiológico original,
- mantener coherencia clínica,
- y evitar códigos excesivamente específicos que el dato original no soporta.

Por esa razón existen categorías marcadas como:

- `Exacta`
- `Agregada`
- `Proxy`

### Exacta

Existe una equivalencia razonablemente directa entre la glosa y el código CIE-11.

Ejemplo:

`Infarto agudo miocardio → BA41`

### Agregada

La glosa original no entrega suficiente detalle y el resultado queda a nivel de
capítulo o categoría amplia.

Ejemplo:

`TOTAL CAUSAS SISTEMA RESPIRATORIO → capítulo 12`

### Proxy

No existe una equivalencia completamente directa y se utiliza la aproximación
más razonable disponible dentro de CIE-11.

Esto ocurre principalmente en:

- categorías operacionales históricas,
- glosas administrativas,
- o agrupaciones antiguas del SADU que no tienen representación moderna exacta.

---

# Normalización de glosas

Las glosas históricas presentan múltiples variaciones de escritura:

- prefijos administrativos,
- diferencias de puntuación,
- códigos CIE incrustados,
- mayúsculas/minúsculas,
- espacios inconsistentes,
- y variantes textuales equivalentes.

Antes del mapeo se aplicó una normalización orientada únicamente a permitir joins
determinísticos entre años y formularios.

La normalización incluye:

- eliminación de espacios no estándar,
- remoción de códigos CIE embebidos,
- limpieza de prefijos de indentación,
- homogenización de mayúsculas,
- y compactación de texto.

El texto original se conserva sin modificaciones en `glosa_original`.

---

# Categorías operacionales

El formulario SADU contiene filas que no representan diagnósticos clínicos.

Ejemplos:

- `TOTAL ATENCIONES DE URGENCIA`
- `TOTAL DEMANDA`
- `CIRUGÍAS DE URGENCIA`

Estas entradas fueron marcadas explícitamente mediante el código sentinela
`OP00`.

`OP00` no corresponde a un código oficial CIE-11.

Su único propósito es permitir:

- separar actividad operacional de actividad clínica,
- evitar análisis epidemiológicos sobre subtotales,
- y filtrar registros administrativos de manera explícita.

---

# Quiebres de serie entre CIE-10 y CIE-11

Uno de los problemas principales de la transición hacia CIE-11 es que algunas
entidades cambian de capítulo respecto a CIE-10.

Esto puede producir variaciones artificiales en series históricas si no se
documenta correctamente.

Los casos más relevantes encontrados durante el mapeo fueron:

## ACV

En CIE-10 el ACV se clasifica dentro de enfermedades circulatorias.

En CIE-11 migra hacia enfermedades neurológicas.

Esto significa que una serie histórica cardiovascular puede mostrar una caída
aparente al migrar a CIE-11, incluso si la incidencia real no cambia.

## Influenza

En CIE-10 la influenza se agrupa dentro del sistema respiratorio.

En CIE-11 migra hacia enfermedades infecciosas.

El efecto es similar: una parte de la carga respiratoria desaparece
artificialmente si no se considera el cambio estructural.

Ambos casos quedan marcados mediante:

`riesgo_quiebre_serie = Alto`

para que cualquier análisis posterior pueda tratarlos explícitamente.

---

# COVID-19

Los registros históricos del DEIS contienen múltiples variantes textuales para
COVID-19 dependiendo del año y del formulario utilizado.

Ejemplos reales:

- `COVID 19 Confirmado`
- `COVID-19, VIRUS IDENTIFICADO`
- `COVID 19 Sospechoso`
- `COVID-19, VIRUS NO IDENTIFICADO`

Aunque el texto cambia, conceptualmente corresponden a dos categorías:

- `RA01.0` → virus identificado
- `RA01.1` → virus no identificado

Las variantes textuales se conservaron para mantener compatibilidad histórica
con todos los años del dataset.

Al agrupar por `codigo_tallo_cie11`, las glosas colapsan naturalmente en las
dos categorías epidemiológicas correspondientes.

---

# Limitaciones

El proyecto no resuelve problemas estructurales de origen presentes en el DEIS.

Si una glosa fue registrada de manera ambigua, incompleta o excesivamente amplia,
esa pérdida de información permanece.

El mapeo mejora:

- trazabilidad,
- interoperabilidad,
- capacidad de agrupación,
- consistencia semántica,
- y análisis longitudinal.

Pero no puede recuperar especificidad clínica inexistente.

Tampoco reemplaza validación médica ni redefine criterios diagnósticos utilizados
en atención de urgencia.

---

# Alcance

El proyecto debe entenderse como una propuesta de estructuración sobre registros
históricos ya existentes.

No corresponde a una tabla oficial ni intenta definir cómo debería implementarse
institucionalmente CIE-11 en Chile.

La adopción completa de modelos composicionales compatibles con CIE-11 requiere
trabajo posterior junto a:

- clínicos,
- epidemiólogos,
- estadísticos,
- DEIS,
- MINSAL,
- y eventualmente organismos internacionales.

El objetivo actual es dejar una base interoperable y trazable sobre la cual esa
discusión futura pueda apoyarse.