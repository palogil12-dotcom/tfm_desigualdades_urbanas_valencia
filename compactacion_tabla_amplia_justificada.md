# Compactacion adicional justificada de la tabla amplia

## Resumen

- Tabla de partida: `C:\Users\paloma.gil\Desktop\otros\Valencia\Resultados\tabla_por_distritos_preseleccion_final.csv`
- Tabla resultante: `C:\Users\paloma.gil\Desktop\Valencia\outputs\compactacion_tabla_amplia\tabla_por_distritos_preseleccion_compactada.csv`
- Columnas iniciales: **743**
- Columnas finales: **590**
- Columnas eliminadas o sustituidas: **187**
- Columnas nuevas agregadas: **34**

## Criterio general

- Se conserva la variable más interpretable, más comparable entre distritos o más reciente cuando varias columnas representan prácticamente la misma dimensión.
- Cuando un bloque estaba sobrerrepresentado por desagregaciones temporales o técnicas, se sustituye por un resumen anual, un total o una proporción.
- En el bloque electoral se conservan las participaciones y se derivan porcentajes de voto por partido, porque son más comparables que los recuentos absolutos.
- Cuando se quiso integrar en una sola columna información procedente de variables con unidades distintas, se construyó un índice sintético explícito basado en z-scores medios.
- No se fusionan en una sola columna variables con unidades incompatibles cuando eso obligaría a construir un índice arbitrario.

## Decisiones aplicadas

### Percentatge de població de nacionalitat estrangera [2025]

- Tipo: `conservar_una`
- Se elimina: Distribució percentual de la població de nacionalitat estrangera [2025] || Encuesta demografica 2025 | Porcentaje de poblacion extranjera
- Motivo: Se conserva el porcentaje distrital directamente interpretable y comparable entre distritos; se eliminan versiones redundantes o con denominador menos claro.

### Padron 2025 extranjera | Africa [% extranjera]

- Tipo: `conservar_una`
- Se elimina: Distribució percentual de població de nacionalitat estrangera d'Àfrica [2025]
- Motivo: Se prioriza la composición interna de la población extranjera del distrito frente a la distribución territorial del conjunto de la ciudad.

### Padron 2025 extranjera | America Sur [% extranjera]

- Tipo: `conservar_una`
- Se elimina: Distribució percentual de població de nacionalitat estrangera d'Amèrica del Sud [2025]
- Motivo: Se conserva la cuota dentro de la población extranjera del distrito por ser más interpretable que la distribución de esa población a escala ciudad.

### Padron 2025 extranjera | Asia [% extranjera]

- Tipo: `conservar_una`
- Se elimina: Distribució percentual de població de nacionalitat estrangera d'Àsia, Oceania o apàtrida [2025]
- Motivo: Se conserva la variable porcentual directamente comparable dentro de cada distrito y se elimina la versión de distribución territorial.

### Edat mitjana [2025]

- Tipo: `conservar_una`
- Se elimina: INE 2023 demograficos | Edad media de la población [distrito] || Encuesta demografica 2025 | Edad media [total]
- Motivo: Se conserva la versión más reciente y coherente con el bloque principal de indicadores demográficos de 2025.

### Edat mitjana de les dones [2025]

- Tipo: `conservar_una`
- Se elimina: Encuesta demografica 2025 | Edad media [mujeres]
- Motivo: Las dos columnas describen el mismo indicador con diferencias mínimas de redondeo; se mantiene la serie de 2025 ya integrada en el bloque principal.

### Edat mitjana dels homes [2025]

- Tipo: `conservar_una`
- Se elimina: Encuesta demografica 2025 | Edad media [hombres]
- Motivo: Se mantiene una única versión del indicador masculino para evitar duplicidad fuente-rótulo con valores casi idénticos.

### Índex de sobrenvelliment [2025]

- Tipo: `conservar_una`
- Se elimina: Encuesta demografica 2025 | Indice de sobre-envejecimiento
- Motivo: Se conserva una única versión del índice, priorizando la familia demográfica de 2025 ya utilizada en otras variables equivalentes.

### Índex demogràfic de dependència global [2025]

- Tipo: `conservar_una`
- Se elimina: Encuesta demografica 2025 | Indice demografico de dependencia
- Motivo: Se elimina la duplicidad interfuentes y se conserva la versión de 2025 coherente con el resto del bloque demográfico.

### Índex d'envelliment [2025]

- Tipo: `conservar_una`
- Se elimina: Encuesta demografica 2025 | Indice de envejecimiento
- Motivo: Se compacta la dimensión envejecimiento en una sola columna, evitando dos medidas prácticamente equivalentes.

### Índex d'estructura de la població en edat activa [2025]

- Tipo: `conservar_una`
- Se elimina: Encuesta demografica 2025 | Indice de estructura de la poblacion activa
- Motivo: Se conserva la versión integrada en la serie de 2025 y se elimina la réplica de encuesta con diferencias menores.

### Encuesta demografica 2024 | Tasa bruta de natalidad

- Tipo: `conservar_una`
- Se elimina: Naixements registrats al Padró [2024]
- Motivo: Se prioriza la tasa frente al recuento absoluto porque permite comparar distritos sin arrastrar el efecto del tamaño poblacional.

### Taxa global de fecunditat registrada al Padró [2024]

- Tipo: `conservar_una`
- Se elimina: Encuesta demografica 2024 | Tasa general de fecundidad
- Motivo: Se conserva una sola tasa de fecundidad para evitar duplicación de la misma dimensión en 2024.

### Padron 2025 | Densidad poblacion [hab/km2]

- Tipo: `conservar_una`
- Se elimina: Densitat de població [2025]
- Motivo: Se conserva la densidad con unidad explícita y coherente con la relación población-superficie ya presente en la tabla.

### Mediana de la renda per unitat de consum [2023]

- Tipo: `conservar_una`
- Se elimina: Mitjana de la renda per unitat de consum [2023]
- Motivo: Se prioriza la mediana por ser más robusta frente a valores extremos y más representativa del nivel típico de renta.

### Renta consumo precios 2024 agua | Litros facturados por habitante y dia

- Tipo: `conservar_una`
- Se elimina: Renta consumo precios 2024 agua | Facturacion [miles m3]
- Motivo: Se conserva el indicador normalizado por habitante, más comparable entre distritos que la facturación agregada.

### Renta consumo precios 2024 alumbrado publico | Consumo electrico [kWh]

- Tipo: `conservar_una`
- Se elimina: Renta consumo precios 2024 alumbrado publico | Facturacion [EUR]
- Motivo: Se prioriza la medida física de consumo frente a la facturación monetaria, más sensible a tarifas y menos comparable territorialmente.

### Renta consumo precios 2024 pasos inferiores | Potencia instalada total [kW]

- Tipo: `conservar_una`
- Se elimina: Renta consumo precios 2024 pasos inferiores | Halogenos metalicos puntos [n] || Renta consumo precios 2024 pasos inferiores | Otros puntos [n] || Renta consumo precios 2024 pasos inferiores | Halogenos metalicos potencia [kW] || Renta consumo precios 2024 pasos inferiores | Puntos alumbrado total [n] || Renta consumo precios 2024 pasos inferiores | Vapor sodio puntos [n] || Renta consumo precios 2024 pasos inferiores | Lamparas led potencia [kW] || Renta consumo precios 2024 pasos inferiores | Lamparas led puntos [n] || Renta consumo precios 2024 pasos inferiores | Vapor sodio potencia [kW] || Renta consumo precios 2024 pasos inferiores | Otros potencia [kW]
- Motivo: Se resume el bloque de pasos inferiores en una sola medida sintética de dotación lumínica, evitando desagregaciones tecnológicas muy finas.

### Renta consumo precios 2024 monumentos | Potencia instalada total [kW]

- Tipo: `conservar_una`
- Se elimina: Renta consumo precios 2024 monumentos | Halogenos metalicos puntos [n] || Renta consumo precios 2024 monumentos | Otros puntos [n] || Renta consumo precios 2024 monumentos | Halogenos metalicos potencia [kW] || Renta consumo precios 2024 monumentos | Puntos alumbrado total [n] || Renta consumo precios 2024 monumentos | Vapor mercurio potencia [kW] || Renta consumo precios 2024 monumentos | Vapor sodio puntos [n] || Renta consumo precios 2024 monumentos | Lamparas led potencia [kW] || Renta consumo precios 2024 monumentos | Vapor mercurio puntos [n] || Renta consumo precios 2024 monumentos | Lamparas led puntos [n] || Renta consumo precios 2024 monumentos | Vapor sodio potencia [kW] || Renta consumo precios 2024 monumentos | Otros potencia [kW]
- Motivo: Se conserva la potencia instalada total como resumen del bloque de monumentos y se eliminan las desagregaciones por tecnología.

### Medio ambiente 2024 | Escombros contenedores total [n]

- Tipo: `conservar_una`
- Se elimina: Medio ambiente 2024 | Escombros contenedores enero [n] || Medio ambiente 2024 | Escombros contenedores febrero [n] || Medio ambiente 2024 | Escombros contenedores marzo [n] || Medio ambiente 2024 | Escombros contenedores abril [n] || Medio ambiente 2024 | Escombros contenedores mayo [n] || Medio ambiente 2024 | Escombros contenedores junio [n] || Medio ambiente 2024 | Escombros contenedores julio [n] || Medio ambiente 2024 | Escombros contenedores agosto [n] || Medio ambiente 2024 | Escombros contenedores septiembre [n] || Medio ambiente 2024 | Escombros contenedores octubre [n] || Medio ambiente 2024 | Escombros contenedores noviembre [n] || Medio ambiente 2024 | Escombros contenedores diciembre [n]
- Motivo: Se conserva el total anual porque resume la presión del fenómeno sin sobrerrepresentar la dimensión temporal mediante doce columnas mensuales.

### Superficie zonas verdes [m2]

- Tipo: `conservar_una`
- Se elimina: Zonas verdes [n] || Zonas verdes CSV - superficie poligono [m2] || Zonas verdes CSV - superficie diciembre [m2]
- Motivo: Se prioriza la superficie de zonas verdes como indicador más estable y comparable; se eliminan recuentos de polígonos y variantes de fuente muy cercanas.

### Arbolado [n]

- Tipo: `conservar_una`
- Se elimina: (sin eliminación asociada)
- Motivo: Se mantiene porque aporta una dimensión distinta de infraestructura verde y no es reducible de forma limpia a la superficie de zonas verdes.

### Medio ambiente 2024 | Juegos infantiles zonas [n]

- Tipo: `conservar_una`
- Se elimina: Medio ambiente 2024 | Juegos infantiles elementos [n] || Medio ambiente 2024 | Juegos infantiles superficie [m2] || Zonas de juegos infantiles [n]
- Motivo: Se conserva un único indicador general de disponibilidad de zonas de juego y se eliminan desagregaciones o duplicados de fuente.

### Percentatge d' habitatges turístics. Dades fins a 2024 [2025]

- Tipo: `conservar_una`
- Se elimina: Nombre d'habitatges turístics. Dades fins a 2024 [2025] || Places en habitatges turístics. Dades fins a 2024 [2025] || Economia 2024 | Viviendas turisticas [n] || Economia 2024 | Viviendas turisticas [% viviendas] || Economia 2024 | Viviendas turisticas [plazas]
- Motivo: Se prioriza la intensidad relativa de vivienda turística frente a recuentos o plazas absolutas, y se conserva la versión más reciente del indicador.

### Recursos municipales 2024 bomberos | Servicios totales [n]

- Tipo: `conservar_una`
- Se elimina: Recursos municipales 2024 bomberos | Asistencia tecnica [n] || Recursos municipales 2024 bomberos | Falsas alarmas [n] || Recursos municipales 2024 bomberos | Incendios [n] || Recursos municipales 2024 bomberos | Mercancias peligrosas [n] || Recursos municipales 2024 bomberos | Salvamentos [n]
- Motivo: Se conserva el total anual de servicios por distrito y se eliminan las tipologías operativas, que fragmentan mucho la información sin aportar comparabilidad clara.

### Recursos municipales 2024 policia local | Servicios totales [n]

- Tipo: `conservar_una`
- Se elimina: Recursos municipales 2024 policia local | Actos via publica [n] || Recursos municipales 2024 policia local | Humanitarios y riesgos [n] || Recursos municipales 2024 policia local | Incidencias [n] || Recursos municipales 2024 policia local | Informacion [n] || Recursos municipales 2024 policia local | Policia administrativa [n] || Recursos municipales 2024 policia local | Seguridad ciudadana [n] || Recursos municipales 2024 policia local | Servicios trafico [n] || Recursos municipales 2024 policia local | Vigilancias [n]
- Motivo: Se resume la actividad policial en una sola medida global, evitando un bloque muy desagregado cuyas subcategorías son difíciles de interpretar comparativamente.

### Recursos municipales 2024 | Sugerencias quejas y reclamaciones [%]

- Tipo: `conservar_una`
- Se elimina: Recursos municipales 2024 | Sugerencias quejas y reclamaciones [n]
- Motivo: Se prioriza la versión porcentual por ser más comparable entre distritos que el recuento absoluto de sugerencias o reclamaciones.

### ValenBisi - estaciones [n] || ValenBisi - bicis disponibles [media]

- Tipo: `conservar_una`
- Se elimina: ValenBisi - anclajes libres [media] || ValenBisi - anclajes totales [n]
- Motivo: No se fuerza un índice único de accesibilidad por resultar demasiado arbitrario; se mantienen dos dimensiones complementarias: cobertura territorial y disponibilidad operativa.

### Economia 2024 | Terrazas hosteleria [superficie_m2]

- Tipo: `conservar_una`
- Se elimina: Economia 2024 | Terrazas hosteleria [n]
- Motivo: Se conserva la superficie ocupada, más informativa sobre intensidad de uso del espacio público que el simple número de terrazas.

### Economia 2024 | Hoteles [plazas]

- Tipo: `conservar_una`
- Se elimina: Economia 2024 | Hoteles [n]
- Motivo: Se prioriza la capacidad turística real frente al mero número de establecimientos.

### Economia 2024 | Hostales y pensiones [plazas]

- Tipo: `conservar_una`
- Se elimina: Economia 2024 | Hostales y pensiones [n]
- Motivo: Se conserva la capacidad de alojamiento, más útil para medir presión turística que el recuento de establecimientos.

### Bienestar social | Distribución de solicitudes de Cheques escolares, concesiones y renta familiar media. Distritos. Curso 202425 | Porcentaje de concedidos

- Tipo: `conservar_una`
- Se elimina: Bienestar social | Distribución de solicitudes de Cheques escolares, concesiones y renta familiar media. Distritos. Curso 202425 | Concedidos
- Motivo: Se prioriza el porcentaje de concedidos por ser más comparable entre distritos que el recuento absoluto, fuertemente condicionado por el tamaño de la demanda.

### Edificacion vivienda 2025 valor catastral medio | Valor total medio [EUR] || Edificacion vivienda 2025 valor catastral medio | Valor medio m2 [EUR]

- Tipo: `conservar_una`
- Se elimina: Edificacion vivienda 2025 valor catastral medio | Valor construccion medio [EUR] || Edificacion vivienda 2025 valor catastral medio | Valor suelo medio [EUR]
- Motivo: Se conservan el valor total medio y el valor medio por metro cuadrado, que resumen mejor el nivel absoluto y la intensidad del valor catastral; se eliminan sus componentes parciales.

### % Participació a les Eleccions Autonòmiques [2023] || % Participació a les Eleccions Europees [2024] || % Participació a les Eleccions Generals [2023] || % Participació a les Eleccions Locals [2023] || porcentajes de voto por partido derivados de recuentos absolutos

- Tipo: `reducir_bloque`
- Se elimina: Elecciones 2023 autonomicas | Electorado || Elecciones 2023 autonomicas | Votos Leídos || Elecciones 2023 autonomicas | Votos Nulos || Elecciones 2023 autonomicas | Votos en Blanco || Elecciones 2023 autonomicas | Votos a Candidaturas || Elecciones 2024 europeas | Electorado || Elecciones 2024 europeas | Vots Leídos || Elecciones 2024 europeas | Votos Nulos || Elecciones 2024 europeas | Votos Válidos || Elecciones 2024 europeas | Votos en Blanco || Elecciones 2024 europeas | Votos a Candidaturas || Elecciones 2023 generales | Electorado || Elecciones 2023 generales | Votos Leídos || Elecciones 2023 generales | Votos Nulos || Elecciones 2023 generales | Votos Válidos || Elecciones 2023 generales | Votos en Blanco || Elecciones 2023 municipales | Electorado || Elecciones 2023 municipales | Votos Leídos || Elecciones 2023 municipales | Votos Nulos || Elecciones 2023 municipales | Votos en Blanco || Elecciones 2023 municipales | Votos a Candidaturas || Votos 2023 generales | PP [n] || Votos 2023 generales | PSOE [n] || Votos 2023 generales | SUMAR_COMPROMÍS [n] || Votos 2023 generales | VOX [n] || Votos 2023 generales | Otros [n] || Votos 2023 autonomicas | PP [n] || Votos 2023 autonomicas | PSOE [n] || Votos 2023 autonomicas | COMPROMÍS [n] || Votos 2023 autonomicas | VOX [n] || Votos 2023 autonomicas | UNIDES_PODEM [n] || Votos 2023 autonomicas | C's [n] || Votos 2023 autonomicas | Otros [n] || Votos 2024 europeas | PP [n] || Votos 2024 europeas | PSOE [n] || Votos 2024 europeas | VOX [n] || Votos 2024 europeas | COMPROMÍS_SUMAR [n] || Votos 2024 europeas | SE_ACABÓ_LA_FIESTA [n] || Votos 2024 europeas | PODEMOS [n] || Votos 2024 europeas | Otros [n] || Votos 2023 municipales | PP [n] || Votos 2023 municipales | COMPROMÍS_MUNICIPAL [n] || Votos 2023 municipales | PSOE [n] || Votos 2023 municipales | VOX [n] || Votos 2023 municipales | PODEM___EUPV [n] || Votos 2023 municipales | Cs [n] || Votos 2023 municipales | Otros [n]
- Motivo: En vez de eliminar por completo el bloque electoral, se conservan las participaciones y se transforman los votos por partido en porcentajes comparables entre distritos. Se eliminan recuentos absolutos, nulos, blancos, leídos y otros totales administrativos.

### Edificacion vivienda 2024 venta trimestral | Precio medio venta anual [EUR_m2]

- Tipo: `agregar_media`
- Se elimina: Edificacion vivienda 2024 venta trimestral | Precio medio venta T1 [EUR_m2] || Edificacion vivienda 2024 venta trimestral | Precio medio venta T2 [EUR_m2] || Edificacion vivienda 2024 venta trimestral | Precio medio venta T3 [EUR_m2] || Edificacion vivienda 2024 venta trimestral | Precio medio venta T4 [EUR_m2]
- Motivo: Se sintetiza la serie trimestral en una media anual para evitar que una misma dimensión de precio ocupe cuatro columnas.
- Detalle: Media de T1-T4 de 2024.

### Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero anual [%]

- Tipo: `agregar_media`
- Se elimina: Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T1 [%] || Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T2 [%] || Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T3 [%] || Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T4 [%]
- Motivo: Se resume en un único indicador anual la carga financiera asociada a la venta.
- Detalle: Media de T1-T4 de 2024.

### Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto medio [%]

- Tipo: `agregar_media`
- Se elimina: Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T1 [%] || Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T2 [%] || Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T3 [%] || Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T4 [%]
- Motivo: Se evita la fragmentación trimestral de una misma tendencia de crecimiento.
- Detalle: Media de T1-T4 de 2024.

### Edificacion vivienda 2024 venta idealista | Media enero-octubre [EUR_m2]

- Tipo: `agregar_media`
- Se elimina: Edificacion vivienda 2024 venta idealista | Enero [EUR_m2] || Edificacion vivienda 2024 venta idealista | Febrero [EUR_m2] || Edificacion vivienda 2024 venta idealista | Marzo [EUR_m2] || Edificacion vivienda 2024 venta idealista | Abril [EUR_m2] || Edificacion vivienda 2024 venta idealista | Mayo [EUR_m2] || Edificacion vivienda 2024 venta idealista | Junio [EUR_m2] || Edificacion vivienda 2024 venta idealista | Julio [EUR_m2] || Edificacion vivienda 2024 venta idealista | Agosto [EUR_m2] || Edificacion vivienda 2024 venta idealista | Septiembre [EUR_m2] || Edificacion vivienda 2024 venta idealista | Octubre [EUR_m2]
- Motivo: Se resume la serie mensual del portal en una única media anual disponible, reduciendo ruido temporal.
- Detalle: Media de enero a octubre de 2024.

### Edificacion vivienda 2024 venta fotocasa | Media enero-octubre [EUR_m2]

- Tipo: `agregar_media`
- Se elimina: Edificacion vivienda 2024 venta fotocasa | Enero [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Febrero [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Marzo [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Abril [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Mayo [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Junio [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Julio [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Agosto [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Septiembre [EUR_m2] || Edificacion vivienda 2024 venta fotocasa | Octubre [EUR_m2]
- Motivo: Se resume la serie mensual del portal en una única media anual disponible.
- Detalle: Media de enero a octubre de 2024.

### Edificacion vivienda 2024 alquiler idealista | Media enero-octubre [EUR_m2_mes]

- Tipo: `agregar_media`
- Se elimina: Edificacion vivienda 2024 alquiler idealista | Enero [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Febrero [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Marzo [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Abril [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Mayo [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Junio [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Julio [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Agosto [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Septiembre [EUR_m2_mes] || Edificacion vivienda 2024 alquiler idealista | Octubre [EUR_m2_mes]
- Motivo: Se resume la serie mensual de alquiler del portal en una sola media anual disponible.
- Detalle: Media de enero a octubre de 2024.

### Edificacion vivienda 2024 alquiler fotocasa | Media enero-octubre [EUR_mes]

- Tipo: `agregar_media`
- Se elimina: Edificacion vivienda 2024 alquiler fotocasa | Enero [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Febrero [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Marzo [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Abril [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Mayo [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Junio [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Julio [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Agosto [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Septiembre [EUR_mes] || Edificacion vivienda 2024 alquiler fotocasa | Octubre [EUR_mes]
- Motivo: Se resume la serie mensual de alquiler del portal en una sola media anual disponible.
- Detalle: Media de enero a octubre de 2024.

### Voto 2023 generales | PP [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 generales | PP [n] || Elecciones 2023 generales | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: PP sobre votos válidos en generales 2023.

### Voto 2023 generales | PSOE [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 generales | PSOE [n] || Elecciones 2023 generales | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: PSOE sobre votos válidos en generales 2023.

### Voto 2023 generales | SUMAR_COMPROMÍS [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 generales | SUMAR_COMPROMÍS [n] || Elecciones 2023 generales | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: SUMAR_COMPROMÍS sobre votos válidos en generales 2023.

### Voto 2023 generales | VOX [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 generales | VOX [n] || Elecciones 2023 generales | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: VOX sobre votos válidos en generales 2023.

### Voto 2023 generales | Otros [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 generales | Otros [n] || Elecciones 2023 generales | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: Otros sobre votos válidos en generales 2023.

### Voto 2023 autonomicas | PP [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 autonomicas | PP [n] || Elecciones 2023 autonomicas | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: PP sobre candidaturas en autonómicas 2023.

### Voto 2023 autonomicas | PSOE [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 autonomicas | PSOE [n] || Elecciones 2023 autonomicas | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: PSOE sobre candidaturas en autonómicas 2023.

### Voto 2023 autonomicas | COMPROMÍS [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 autonomicas | COMPROMÍS [n] || Elecciones 2023 autonomicas | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: COMPROMÍS sobre candidaturas en autonómicas 2023.

### Voto 2023 autonomicas | VOX [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 autonomicas | VOX [n] || Elecciones 2023 autonomicas | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: VOX sobre candidaturas en autonómicas 2023.

### Voto 2023 autonomicas | UNIDES_PODEM [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 autonomicas | UNIDES_PODEM [n] || Elecciones 2023 autonomicas | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: UNIDES_PODEM sobre candidaturas en autonómicas 2023.

### Voto 2023 autonomicas | C's [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 autonomicas | C's [n] || Elecciones 2023 autonomicas | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: C's sobre candidaturas en autonómicas 2023.

### Voto 2023 autonomicas | Otros [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 autonomicas | Otros [n] || Elecciones 2023 autonomicas | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: Otros sobre candidaturas en autonómicas 2023.

### Voto 2024 europeas | PP [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2024 europeas | PP [n] || Elecciones 2024 europeas | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: PP sobre votos válidos en europeas 2024.

### Voto 2024 europeas | PSOE [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2024 europeas | PSOE [n] || Elecciones 2024 europeas | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: PSOE sobre votos válidos en europeas 2024.

### Voto 2024 europeas | VOX [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2024 europeas | VOX [n] || Elecciones 2024 europeas | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: VOX sobre votos válidos en europeas 2024.

### Voto 2024 europeas | COMPROMÍS_SUMAR [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2024 europeas | COMPROMÍS_SUMAR [n] || Elecciones 2024 europeas | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: COMPROMÍS_SUMAR sobre votos válidos en europeas 2024.

### Voto 2024 europeas | SE_ACABÓ_LA_FIESTA [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2024 europeas | SE_ACABÓ_LA_FIESTA [n] || Elecciones 2024 europeas | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: SE_ACABÓ_LA_FIESTA sobre votos válidos en europeas 2024.

### Voto 2024 europeas | PODEMOS [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2024 europeas | PODEMOS [n] || Elecciones 2024 europeas | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: PODEMOS sobre votos válidos en europeas 2024.

### Voto 2024 europeas | Otros [% validos]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2024 europeas | Otros [n] || Elecciones 2024 europeas | Votos Válidos
- Motivo: Se conserva la afinidad partidista como porcentaje de voto válido, más comparable entre distritos que el recuento absoluto.
- Detalle: Otros sobre votos válidos en europeas 2024.

### Voto 2023 municipales | PP [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 municipales | PP [n] || Elecciones 2023 municipales | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: PP sobre candidaturas en municipales 2023.

### Voto 2023 municipales | COMPROMÍS_MUNICIPAL [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 municipales | COMPROMÍS_MUNICIPAL [n] || Elecciones 2023 municipales | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: COMPROMÍS_MUNICIPAL sobre candidaturas en municipales 2023.

### Voto 2023 municipales | PSOE [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 municipales | PSOE [n] || Elecciones 2023 municipales | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: PSOE sobre candidaturas en municipales 2023.

### Voto 2023 municipales | VOX [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 municipales | VOX [n] || Elecciones 2023 municipales | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: VOX sobre candidaturas en municipales 2023.

### Voto 2023 municipales | PODEM___EUPV [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 municipales | PODEM___EUPV [n] || Elecciones 2023 municipales | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: PODEM___EUPV sobre candidaturas en municipales 2023.

### Voto 2023 municipales | Cs [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 municipales | Cs [n] || Elecciones 2023 municipales | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: Cs sobre candidaturas en municipales 2023.

### Voto 2023 municipales | Otros [% candidaturas]

- Tipo: `agregar_ratio`
- Se elimina: Votos 2023 municipales | Otros [n] || Elecciones 2023 municipales | Votos a Candidaturas
- Motivo: Se conserva la afinidad partidista como porcentaje sobre candidaturas, más comparable entre distritos que el recuento absoluto.
- Detalle: Otros sobre candidaturas en municipales 2023.

### Renta consumo precios 2024 | Indice sintetico de consumos e infraestructuras urbanas [z-media]

- Tipo: `agregar_indice`
- Se elimina: Renta consumo precios 2024 agua | Litros facturados por habitante y dia || Renta consumo precios 2024 alumbrado publico | Consumo electrico [kWh] || Renta consumo precios 2024 monumentos | Potencia instalada total [kW] || Renta consumo precios 2024 pasos inferiores | Potencia instalada total [kW]
- Motivo: Aquí sí se integra la información de varias columnas en una sola, pero únicamente tras estandarizar cada variable para hacer comparables unidades distintas.
- Detalle: Media de los z-scores de agua facturada por habitante, consumo eléctrico de alumbrado público, potencia de monumentos y potencia de pasos inferiores.

## Nota metodológica

Esta versión compactada no sustituye a la tabla amplia original. Constituye una derivación más manejable para visualización, comparación distrital y preparación posterior del análisis, manteniendo dimensiones relevantes como la afinidad política mediante variables porcentuales en lugar de recuentos absolutos.
