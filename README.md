# Apendice metodologico: materiales complementarios del pipeline

Este anexo recoge los materiales complementarios asociados a la construccion, depuracion, compactacion, jerarquizacion y visualizacion de la base de datos distrital. Su finalidad no es repetir la explicacion metodologica desarrollada en el cuerpo principal del trabajo, sino identificar de forma sintetica los ficheros que permiten reconstruir el proceso seguido y reforzar su trazabilidad.

Todos estos materiales se encuentran disponibles en el repositorio GitHub del proyecto:

`https://github.com/USUARIO/REPOSITORIO`

A efectos expositivos, los archivos complementarios pueden agruparse en cinco bloques.

## 1. Fuentes iniciales y estructura de partida

Este bloque documenta el punto de partida material de la base de datos y la reconstruccion de la tabla inicial. En esta version del anexo se ha priorizado el material final y reproducible, por lo que la carpeta principal no incorpora todavia el conjunto completo de inventarios iniciales y tablas scaffold. Cuando esos materiales se anadan, este sera el bloque donde queden descritos.

## 2. Scripts principales del pipeline

Los scripts en Python recogen la implementacion operativa de las fases descritas en la memoria:

- `01_codigo/depurar_tabla.py`: limpieza, depuracion y transformacion de la tabla distrital.
- `01_codigo/correlaciones.py`: comprobaciones cuantitativas y analisis de correlaciones como apoyo a decisiones metodologicas.
- `01_codigo/jerarquizar_tabla.py`: clasificacion de variables segun bloque tematico, subdimension y rol analitico.
- `01_codigo/generar_mapa_interactivo.py`: generacion del visor territorial a partir de la tabla final y de la geometria distrital.
- `01_codigo/crear_tabla_distritos_final_depurada_y_jerarquizada.py`: ensamblaje de la version final depurada y jerarquizada de la tabla distrital.

## 3. Tablas finales generadas

Como resultado del proceso de depuracion y jerarquizacion se generaron varias tablas principales. Estas tablas representan el punto de llegada del pipeline de construccion de datos y el punto de partida para las fases posteriores de analisis y visualizacion.

- `02_datos_finales/tabla_por_distritos_final_depurada.csv`: matriz distrital resultante tras la depuracion de la tabla inicial, con las variables seleccionadas, normalizadas o agregadas.
- `02_datos_finales/tabla_por_distritos_final_jerarquizada.csv`: version final de la matriz distrital, en la que se incorporan metadatos de bloque tematico, subdimension y rol analitico.
- `02_datos_finales/diccionario_jerarquia_variables_final.csv`: diccionario de variables y categorias analiticas utilizado para organizar la tabla final.
- `04_material_complementario/resultados_intermedios/tabla_por_distritos_limpia_derivada_integrada_v31.csv`: version intermedia limpia y derivada, conservada como material complementario de trazabilidad.

## 4. Ficheros de control metodologico

Este bloque reune documentos auxiliares que permiten justificar y auditar las decisiones de reduccion y compactacion de variables:

- `03_resultados/reporte_correlaciones.csv`: correlaciones y comprobaciones cuantitativas empleadas como respaldo de decisiones de depuracion.
- `03_resultados/reporte_correlaciones_respaldo_final.csv`: version de respaldo del reporte final de correlaciones.
- `03_resultados/reporte_auditoria_transformaciones_final.csv`: registro de transformaciones y verificaciones aplicadas durante la preparacion de la tabla final.
- `03_resultados/resumen_jerarquia_bloques_final.csv`: resumen sintetico de la organizacion jerarquica por bloques tematicos.

## 5. Visualizacion interactiva

La visualizacion interactiva se conserva como producto complementario del pipeline, con una funcion principalmente exploratoria y comunicativa:

- `03_resultados/mapa_interactivo_distritos.html`: fichero de la visualizacion interactiva final conservado como material complementario.

En conjunto, estos materiales complementarios permiten reconstruir el recorrido seguido desde la recopilacion inicial de fuentes hasta la obtencion de una matriz distrital depurada, jerarquizada y preparada para su exploracion territorial y analisis posterior. De este modo, el repositorio funciona como soporte reproducible del pipeline desarrollado en el TFM.
