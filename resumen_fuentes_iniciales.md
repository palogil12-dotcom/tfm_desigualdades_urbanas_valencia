# Resumen de reconstruccion de fuentes iniciales

Este script separa con claridad las fuentes que se redescargan por HTTP,
las que se reflejan desde las carpetas originales descargadas manualmente
y las que en realidad fueron incorporadas manualmente en el propio pipeline.

- Carpeta legado inspeccionada: `C:\Users\paloma.gil\Desktop\otros\Valencia`
- Salida de reconstruccion: `C:\Users\paloma.gil\Desktop\Valencia\Resultados\reconstruccion_fuentes_iniciales`
- Descarga HTTP activada: `no`

## Conteo por metodo

- `direct_http`: 3
- `manual_table`: 2
- `mirror_local_download`: 243

## Conteo por estado

- `copied`: 243
- `manual_only`: 2
- `skipped_http`: 3

## Lectura metodologica

- `mirror_local_download` indica que el proceso original dependia de ficheros ya descargados manualmente y guardados en carpetas tematicas.
- `direct_http` indica que el script original si consumia un endpoint o capa remota directamente.
- `manual_table` indica que no existia una descarga original recuperable dentro del pipeline y los valores se introdujeron manualmente.

## Tabla scaffold

- Se genera tambien `tabla_distritos_inicial_scaffold.csv` como esqueleto minimo de la tabla distrital con la fila `__categoria__`.
