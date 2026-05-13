#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script único final para construir la tabla depurada y jerarquizada de distritos.

Flujo completo:
1. Lee tabla_por_distritos_limpia.csv.
2. Aplica toda la depuración, normalización, fusión y reducción de variables.
3. Genera tabla_por_distritos_final_depurada.csv.
4. Añade metadatos de subdimensión y rol de análisis.
5. Genera tabla_por_distritos_final_jerarquizada.csv, diccionario y resumen.

No depende de versiones intermedias vXX.
"""

from __future__ import annotations

import math
import unicodedata
from pathlib import Path

import pandas as pd


INPUT_NAME = "tabla_por_distritos_limpia.csv"
OUTPUT_NAME = "tabla_por_distritos_final_depurada.csv"
REPORT_NAME = "reporte_correlaciones_respaldo_final.csv"
AUDIT_REPORT_NAME = "reporte_auditoria_transformaciones_final.csv"


def find_input_csv() -> Path:
    """
    Localiza la tabla original de forma robusta.

    El script puede ejecutarse desde la carpeta `scripts`, desde la raíz del
    proyecto o desde una carpeta de resultados. Por eso se buscan el directorio
    del script, el directorio actual y sus ascendientes, tanto directamente como
    dentro de carpetas habituales de salida (`resultados`, `Resultados`).
    """
    script_dir = Path(__file__).resolve().parent
    start_dirs = [script_dir, Path.cwd().resolve()]

    candidates = []
    seen = set()
    for start in start_dirs:
        for base in [start, *start.parents]:
            for subdir in ("", "resultados", "Resultados", "RESULTADOS"):
                candidate = (base / subdir / INPUT_NAME) if subdir else (base / INPUT_NAME)
                if candidate not in seen:
                    candidates.append(candidate)
                    seen.add(candidate)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    checked = "\n".join(str(c) for c in candidates[:40])
    raise FileNotFoundError(
        "No se encontró tabla_por_distritos_limpia.csv. "
        "Coloca el script en la raíz del proyecto, en scripts/, en resultados/ "
        "o junto al CSV original. Rutas comprobadas:\n" + checked
    )


def resolve_output_path(filename: str, input_csv: Path | None = None) -> Path:
    """
    Decide dónde escribir los ficheros de salida.

    Se prioriza la carpeta del propio script para que la ejecución sea
    reproducible y no dependa de permisos o bloqueos en la carpeta donde está
    el CSV de entrada.
    """
    script_dir = Path(__file__).resolve().parent
    if script_dir.exists():
        return script_dir / filename
    if input_csv is not None:
        return input_csv.with_name(filename)
    return Path(filename)


# -----------------------------------------------------------------------------
# Columnas sustituidas por variables derivadas ya depuradas
# -----------------------------------------------------------------------------

EXTRANJERIA_DROP_COLS = [
    # Variables antiguas/duplicadas de extranjería y nacionalidad extranjera
    "Distribució percentual de la població de nacionalitat estrangera [2025]",
    "Distribució percentual de població de nacionalitat estrangera d'Àfrica [2025]",
    "Distribució percentual de població de nacionalitat estrangera d'Amèrica Central [2025]",
    "Distribució percentual de població de nacionalitat estrangera d'Amèrica del Nord [2025]",
    "Distribució percentual de població de nacionalitat estrangera d'Amèrica del Sud [2025]",
    "Distribució percentual de població de nacionalitat estrangera d'Àsia, Oceania o apàtrida [2025]",
    "Distribució percentual de població de nacionalitat estrangera de la Unió Europea [2025]",
    "Distribució percentual de població de nacionalitat estrangera Europea no UE [2025]",
    "Percentatge de població de nacionalitat estrangera [2025]",
    "Edat mitjana de la població estrangera [2025]",
    "Proporció d'immigrants de nacionalitat estrangera [2024]",
    "Relació de masculinitat de la població de nacionalitat estrangera [2025]",
    "Encuesta demografica 2025 | Porcentaje de poblacion extranjera",
    "Padron 2025 extranjera | Total [n]",
    "Padron 2025 extranjera | UE27 [n]",
    "Padron 2025 extranjera | Resto Europa [n]",
    "Padron 2025 extranjera | Africa [n]",
    "Padron 2025 extranjera | America Norte [n]",
    "Padron 2025 extranjera | America Central [n]",
    "Padron 2025 extranjera | America Sur [n]",
    "Padron 2025 extranjera | Asia [n]",
    "Padron 2025 extranjera | Otros [n]",
    "Padron 2025 extranjera | Africa [% extranjera]",
    "Padron 2025 extranjera | America Sur [% extranjera]",
    "Padron 2025 extranjera | Asia [% extranjera]",
]

NEW_EXTRANJERIA_COLS = [
    "Demografia - Poblacion extranjera [% poblacion]",
    "Demografia - Edad media poblacion extranjera [anos]",
    "Demografia - Poblacion extranjera UE27 [% extranjera]",
    "Demografia - Poblacion extranjera resto Europa [% extranjera]",
    "Demografia - Poblacion extranjera Africa [% extranjera]",
    "Demografia - Poblacion extranjera America Norte [% extranjera]",
    "Demografia - Poblacion extranjera America Central [% extranjera]",
    "Demografia - Poblacion extranjera America Sur [% extranjera]",
    "Demografia - Poblacion extranjera Asia [% extranjera]",
    "Demografia - Poblacion extranjera otros origenes [% extranjera]",
]

DEMOGRAFIA_DROP_COLS = [
    # Duplicados o medidas antiguas sustituidas por indicadores sintéticos 2025
    "Densitat de població [2025]",
    "Edat mitjana [2025]",
    "Edat mitjana de les dones [2025]",
    "Edat mitjana dels homes [2025]",
    "Índex de reemplaçament de la població en edat activa [2025]",
    "Índex d'estructura de la població en edat activa [2025]",
    "Població resident (1) [2025]",
    "Població resident [2025]",
    "Variació anual de la població [2025]",
    "INE 2023 demograficos | Porcentaje de hogares unipersonales [dif Valencia]",
    "INE 2023 demograficos | Tamaño medio del hogar [dif Valencia]",
    "INE 2023 demograficos | Edad media de la población [distrito]",
    "INE 2023 demograficos | Edad media de la población [dif Valencia]",
    "INE 2023 demograficos | Población [distrito]",
    "INE 2023 demograficos | Población [dif Valencia]",
    "INE 2023 demograficos | Porcentaje de población de 65 y más años [distrito]",
    "INE 2023 demograficos | Porcentaje de población de 65 y más años [dif Valencia]",
    "INE 2023 demograficos | Porcentaje de población española [distrito]",
    "INE 2023 demograficos | Porcentaje de población española [dif Valencia]",
    "INE 2023 demograficos | Porcentaje de población menor de 18 años [distrito]",
    "INE 2023 demograficos | Porcentaje de población menor de 18 años [dif Valencia]",
    "Poblacion distrito [anuario 2021]",
    "Encuesta demografica 2024 | Esperanza de vida al nacimiento [total]",
    "Encuesta demografica 2024 | Esperanza de vida al nacimiento [hombres]",
    "Encuesta demografica 2024 | Esperanza de vida al nacimiento [mujeres]",
    "Encuesta demografica 2025 | Edad media [total]",
    "Encuesta demografica 2025 | Edad media [hombres]",
    "Encuesta demografica 2025 | Edad media [mujeres]",
    "Encuesta demografica 2025 | Indice de estructura de la poblacion activa",
    "Padron 2024 | Poblacion",
    "Padron 2025 | Densidad poblacion [hab/km2]",
    "Padron 2025 | Variacion interanual poblacion [%]",
    "Padron 2025 edad | 0-14 [n]",
    "Padron 2025 edad | 15-64 [n]",
    "Padron 2025 edad | 65+ [n]",
    "Padron 2025 edad | 0-14 [%]",
    "Padron 2025 edad | 15-64 [%]",
    "Padron 2025 edad | 65+ [%]",
    "Padron 2025 nacimiento | Valencia [n]",
    "Padron 2025 nacimiento | Resto Horta [n]",
    "Padron 2025 nacimiento | Resto Comunidad [n]",
    "Padron 2025 nacimiento | Resto Estado [n]",
    "Padron 2025 nacimiento | Extranjero [n]",
    "Padron 2025 nacimiento | Valencia [%]",
    "Padron 2025 nacimiento | Extranjero [%]",
]

NEW_DEMOGRAFIA_COLS = [
    "Demografia - Densidad poblacion [hab_km2]",
    "Demografia - Variacion interanual poblacion [%]",
    "Demografia - Edad media [anos]",
    "Demografia - Esperanza de vida al nacimiento [anos]",
    "Demografia - Indice estructura poblacion activa",
    "Demografia - Poblacion 0-14 [%]",
    "Demografia - Poblacion 15-64 [%]",
    "Demografia - Poblacion 65+ [%]",
    "Demografia - Nacidos en Valencia [%]",
    "Demografia - Nacidos en el extranjero [%]",
]

HECHOS_DROP_COLS = [
    "Hechos discriminatorios [n]",
    "Hechos discriminatorios - Antisemitismo [n]",
    "Hechos discriminatorios - Aporofobia [n]",
    "Hechos discriminatorios - Disfobia [n]",
    "Hechos discriminatorios - Edadismo [n]",
    "Hechos discriminatorios - Genero [n]",
    "Hechos discriminatorios - Ideologia [n]",
    "Hechos discriminatorios - Interseccional [n]",
    "Hechos discriminatorios - Islamofobia [n]",
    "Hechos discriminatorios - Lengua y Cultura [n]",
    "Hechos discriminatorios - LGTBIFobia [n]",
    "Hechos discriminatorios - Malalties Rares i Físics no Normatius [n]",
    "Hechos discriminatorios - Racismo [n]",
    "Hechos discriminatorios - Religion [n]",
    "Hechos discriminatorios - Romafobia [n]",
    "Hechos discriminatorios - SD [n]",
    "Hechos discriminatorios [por_km2]",
    "Hechos discriminatorios [por_1000_hab]",
    "Hechos discriminatorios - Malalties Rares i Físics no Normatius [por_km2]",
    "Hechos discriminatorios - Malalties Rares i Físics no Normatius [por_1000_hab]",
]

NEW_HECHOS_COLS = [
    "Hechos discriminatorios [por_1000_hab]",
    "Hechos discriminatorios - Discriminación étnico-cultural y racial [por_1000_hab]",
    "Hechos discriminatorios - Intolerancia religiosa [por_1000_hab]",
    "Hechos discriminatorios - Capacitismo [por_1000_hab]",
    "Hechos discriminatorios - Discriminación por sexo-género y diversidad sexual [por_1000_hab]",
    "Hechos discriminatorios - Aporofobia [por_1000_hab]",
    "Hechos discriminatorios - Ideologia [por_1000_hab]",
    "Hechos discriminatorios - Interseccional [por_1000_hab]",
    "Hechos discriminatorios - Edadismo [por_1000_hab]",
]

POLICIA_DROP_COLS = [
    "Recursos municipales 2024 policia local | Informacion [n]",
    "Recursos municipales 2024 policia local | Servicios totales [n]",
    "Recursos municipales 2024 policia local | Actos via publica [n]",
    "Recursos municipales 2024 policia local | Humanitarios y riesgos [n]",
    "Recursos municipales 2024 policia local | Incidencias [n]",
    "Recursos municipales 2024 policia local | Policia administrativa [n]",
    "Recursos municipales 2024 policia local | Seguridad ciudadana [n]",
    "Recursos municipales 2024 policia local | Vigilancias [n]",
    "Recursos municipales 2024 policia local | Servicios trafico [n]",
]

NEW_POLICIA_COLS = [
    "Policia local - Trafico y movilidad [por_1000_hab]",
    "Policia local - Seguridad y vigilancia [por_1000_hab]",
    "Policia local - Control administrativo y espacio publico [por_1000_hab]",
    "Policia local - Atencion e incidencias humanitario-riesgo [por_1000_hab]",
]

BOMBEROS_DROP_COLS = [
    "Recursos municipales 2024 bomberos | Servicios totales [n]",
    "Recursos municipales 2024 bomberos | Incendios [n]",
    "Recursos municipales 2024 bomberos | Mercancias peligrosas [n]",
    "Recursos municipales 2024 bomberos | Falsas alarmas [n]",
    "Recursos municipales 2024 bomberos | Salvamentos [n]",
    "Recursos municipales 2024 bomberos | Asistencia tecnica [n]",
]

NEW_BOMBEROS_COLS = [
    "Bomberos - Rescate y asistencia [por_1000_hab]",
    "Bomberos - Incendios y alertas de riesgo [por_1000_hab]",
]

TOURISM_DROP_COLS = [
    "Nombre d'habitatges turístics. Dades fins a 2024 [2025]",
    "Percentatge d' habitatges turístics. Dades fins a 2024 [2025]",
    "Places en habitatges turístics. Dades fins a 2024 [2025]",
    "Economia 2024 | Hoteles [n]",
    "Economia 2024 | Hoteles [plazas]",
    "Economia 2024 | Hostales y pensiones [n]",
    "Economia 2024 | Hostales y pensiones [plazas]",
    "Economia 2024 | Albergues urbanos [n]",
    "Economia 2024 | Albergues urbanos [plazas]",
    "Economia 2024 | Viviendas turisticas [n]",
    "Economia 2024 | Viviendas turisticas [plazas]",
]

NEW_TOURISM_COLS = [
    "Economia 2024 | Hoteles [plazas_por_1000_hab]",
    "Economia 2024 | Hostales y pensiones [plazas_por_1000_hab]",
    "Economia 2024 | Albergues urbanos [plazas_por_1000_hab]",
    "Economia 2024 | Viviendas turisticas [plazas_por_1000_hab]",
]

ECONOMIA_DROP_COLS = [
    "Nombre d\'habitatges turístics. Dades fins a 2024 [2025]",
    "Percentatge d' habitatges turístics. Dades fins a 2024 [2025]",
    "Places en habitatges turístics. Dades fins a 2024 [2025]",
    "Activitats a l'Impost d'Activitats Econòmiques [2025]",
 'Activitats econòmiques per 1.000 habitants [2025]',
 'Grau de terciarització econòmica [2025]',
 'Mediana de la renda per unitat de consum [2023]',
 'Mitjana de la renda per unitat de consum [2023]',
 'Renda neta mitjana per llar [2023]',
 'Renda neta mitjana per persona [2023]',
 'IBI - media Num. Recibos personalidad F',
 'IBI - media Num. Recibos personalidad J',
 'IBI - media Num.Recibos sin personalidad',
 'IBI - media Num.Recibos Almacen-Estacionamiento',
 'IBI - media Num. Recibos Actv. Comercial',
 'IBI - media Num. Recibos Actv. Cultural',
 'IBI - media Num. Recibos Actv. Deportiva',
 'IBI - media Num.Recibos Actv.Edificio singular',
 'IBI - media Num. Recibos Actv. Espectaculos',
 'IBI - media Num. Recibos Actv. Industrial',
 'IBI - media Num.Recibos Actv.Obras Urbanizacion',
 'IBI - media Num.Recibos Actv.Ocio y Hostaleria',
 'IBI - media Num. Recibos Actv. Oficinas',
 'IBI - media Num. Recibos Actv. Religiosas',
 'IBI - media Num. Recibos Actv. Residencial',
 'IBI - media Num.Recibos Actv.Sanidad y Beneficiencia',
 'IBI - media Num. Recibos totales',
 'IBI - media Importe Recibos personalidad F',
 'IBI - media Importe Recibos personalidad J',
 'IBI - media Importe Recibos sin personalidad',
 'IBI - media Imp.Recibos Actv.Almacen-Estacionamiento',
 'IBI - media Imp. Recibos Actv. Comercial',
 'IBI - media Imp. Recibos Actv. Cultural',
 'IBI - media Imp. Recibos Actv. Deportiva',
 'IBI - media Imp.Recibos Actv.Edificio singular',
 'IBI - media Imp. Recibos Actv. Espectaculos',
 'IBI - media Imp. Recibos Actv. Industrial',
 'IBI - media Imp.Recibos Actv.Obras urbanizacion',
 'IBI - media Imp.Recibos Actv.Ocio y Hosteleria',
 'IBI - media Imp. Recibos Actv. Oficinas',
 'IBI - media Imp. Recibos Actv. Religiosas',
 'IBI - media Imp. Recibos Actv. Residencial',
 'IBI - media Imp.Recibos Actv.Sanidad y Beneficiencia',
 'IBI - media Importe Recibos totales',
 'IAE - media Numero recibos personalidad juridica',
 'IAE - media Numero recibos sin personalidad',
 'IAE - media Numero recibos actividad empresarial',
 'IAE - media Número recibos actividad local',
 'IAE - media Numero recibos totales',
 'IAE - media Importe recibos personalidad juridica',
 'IAE - media Importe recibos sin personalidad',
 'IAE - media Importe recibos actividad empresarial',
 'IAE - media Importe recibos actividad Profesional',
 'IAE - media Importe recibos actividad Artistica',
 'IAE - media Importe recibos actividad local',
 'IAE - media Importe recibos totales',
 'IVTM - media Año',
 'IVTM - media Codigo distrito',
 'IVTM - media Num. Recibos personalidad fisica',
 'IVTM - media Num. Recibos personalidad juridica',
 'IVTM - media Num. Recibos sin personalitat',
 'IVTM - media Recibos Autobus',
 'IVTM - media Recibos Camion',
 'IVTM - media Recibos Ciclomotor',
 'IVTM - media Recibos Motocicleta',
 'IVTM - media Recibos Remolque',
 'IVTM - media Recibos Semirremolque',
 'IVTM - media Recibos Tractor',
 'IVTM - media Recibos Turismo',
 'IVTM - media Recibos Totales',
 'IVTM - media Importe Rec, Personalidad fisica',
 'IVTM - media Importe Rec, Personalidad juridica',
 'IVTM - media Importe Rec, Sin personlidad',
 'IVTM - media Importe Rec, Autobus',
 'IVTM - media Importe Rec, Camion',
 'IVTM - media Importe Rec, Ciclomotor',
 'IVTM - media Importe Rec, Motocicleta',
 'IVTM - media Importe Rec, Remolque',
 'IVTM - media Importe Rec, Semirremolque',
 'IVTM - media Importe Rec, Tractor',
 'IVTM - media Importe Rec, Turismos',
 'IVTM - media Importe Rec, Totales',
 'INE - Renta media por persona [EUR distrito]',
 'INE - Renta media por persona [dif Valencia EUR]',
 'INE - Renta media por hogar [EUR distrito]',
 'INE - Renta media por hogar [dif Valencia EUR]',
 'INE - Media renta por unidad de consumo [EUR distrito]',
 'INE - Media renta por unidad de consumo [dif Valencia EUR]',
 'INE - Mediana renta por unidad de consumo [EUR distrito]',
 'INE - Mediana renta por unidad de consumo [dif Valencia EUR]',
 'INE - Fuente ingresos salario [% distrito]',
 'INE - Fuente ingresos salario [dif Valencia p.p.]',
 'INE - Fuente ingresos pensiones [% distrito]',
 'INE - Fuente ingresos pensiones [dif Valencia p.p.]',
 'INE - Fuente ingresos prestaciones desempleo [% distrito]',
 'INE - Fuente ingresos prestaciones desempleo [dif Valencia p.p.]',
 'INE - Fuente ingresos otras prestaciones [% distrito]',
 'INE - Fuente ingresos otras prestaciones [dif Valencia p.p.]',
 'INE - Fuente ingresos otros [% distrito]',
 'INE - Fuente ingresos otros [dif Valencia p.p.]',
 'INE 2023 desigualdad | Índice de Gini [distrito]',
 'INE 2023 desigualdad | Índice de Gini [dif Valencia]',
 'INE 2023 desigualdad | Distribución de la renta P80/P20 [distrito]',
 'INE 2023 desigualdad | Distribución de la renta P80/P20 [dif Valencia]',
 'Parados marzo 2024 [distrito]',
 '% parados sobre total Valencia marzo 2024 [distrito]',
 'Anuario 2021 actividad | ocupada [% distrito 16+]',
 'Anuario 2021 actividad | parada [% distrito 16+]',
 'Anuario 2021 actividad | jubilacion o prejubilacion [% distrito 16+]',
 'Anuario 2021 situacion profesional | cuenta propia [% ocupadas distrito]',
 'Anuario 2021 situacion profesional | cuenta ajena fija [% ocupadas distrito]',
 'Anuario 2021 situacion profesional | cuenta ajena temporal [% ocupadas distrito]',
 'Anuario 2021 lugar trabajo | mismo municipio [% ocupadas distrito]',
 'Anuario 2021 lugar trabajo | distinta provincia o comunidad [% ocupadas distrito]',
 'Economia 2025 | Oficinas bancarias [n]',
 'Economia 2025 | Oficinas bancarias [por_10000_hab]',
 'Economia 2024 | Terrazas hosteleria [n]',
 'Economia 2024 | Terrazas hosteleria [superficie_m2]',
 'Economia 2024 | Terrazas anuales [n]',
 'Economia 2024 | Terrazas temporada [n]',
 'Economia 2025 | Actividades industriales [n]',
 'Economia 2025 | Actividades industriales energia y agua [n]',
 'Economia 2025 | Actividades industriales minerales [n]',
 'Economia 2025 | Actividades industriales metales [n]',
 'Economia 2025 | Actividades industriales manufactureras resto [n]',
 'Economia 2024 | Hoteles [n]',
 'Economia 2024 | Hoteles [plazas]',
 'Economia 2024 | Hostales y pensiones [n]',
 'Economia 2024 | Hostales y pensiones [plazas]',
 'Economia 2024 | Albergues urbanos [n]',
 'Economia 2024 | Albergues urbanos [plazas]',
 'Economia 2024 | Viviendas turisticas [n]',
 'Economia 2024 | Viviendas turisticas [plazas]',
 'Economia 2024 | Viviendas turisticas [% viviendas]',
 'Economia 2024 | Sociedades cooperativas registro territorial [n]',
 'Economia 2024 | Sociedades cooperativas registro central [n]',
 'Economia 2024 | Sociedades laborales [n]',
 'Economia 2024 | Empresas activas [n]',
 'Economia 2024 | Empresas activas persona fisica [n]',
 'Economia 2024 | Empresas activas persona juridica [n]',
 'Economia 2024 | Empresas activas industria [n]',
 'Economia 2024 | Empresas activas construccion [n]',
 'Economia 2024 | Empresas activas servicios [n]',
 'Edificacion vivienda 2023 alquiler | Superficie colectiva mediana [m2]',
 'Edificacion vivienda 2023 alquiler | Cuantia colectiva mediana [EUR_mes]']

NEW_ECONOMIA_COLS = ['Economia - Renta neta media por persona [EUR]',
 'Economia - Mediana renta por unidad de consumo [EUR]',
 'Economia - Desigualdad renta Gini [indice]',
 'Economia - Fuente ingresos salario [%]',
 'Economia - Fuente ingresos pensiones [%]',
 'Economia - Fuente ingresos prestaciones desempleo [%]',
 'Economia - Poblacion ocupada [% 16+]',
 'Economia - Poblacion parada [% 16+]',
 'Economia - Jubilacion o prejubilacion [% 16+]',
 'Economia - Ocupados por cuenta propia [% ocupados]',
 'Economia - Ocupados cuenta ajena temporal [% ocupados]',
 'Economia - Trabaja en el mismo municipio [% ocupados]',
 'Economia - Actividades economicas [por_1000_hab]',
 'Economia - Empresas activas [por_1000_hab]',
 'Economia - Empresas persona juridica [% empresas]',
 'Economia - Empresas industria [% empresas]',
 'Economia - Empresas construccion [% empresas]',
 'Economia - Empresas servicios [% empresas]',
 'Economia - Actividades industriales [por_1000_hab]',
 'Economia - Grado de terciarizacion economica [%]',
 'Economia - Plazas alojamiento turistico reglado [por_1000_hab]',
 'Economia - Viviendas turisticas [plazas_por_1000_hab]',
 'Economia - Viviendas turisticas [% viviendas]',
 'Economia - Oficinas bancarias [por_10000_hab]',
 'Economia - Terrazas hosteleria [por_1000_hab]',
 'Economia - Terrazas hosteleria superficie [m2_por_1000_hab]',
 'Economia - Economia social cooperativas y sociedades laborales [por_1000_hab]']

SALE_QUARTERLY_DROP_COLS = [
    "Edificacion vivienda 2024 venta trimestral | Precio medio venta T1 [EUR_m2]",
    "Edificacion vivienda 2024 venta trimestral | Precio medio venta T2 [EUR_m2]",
    "Edificacion vivienda 2024 venta trimestral | Precio medio venta T3 [EUR_m2]",
    "Edificacion vivienda 2024 venta trimestral | Precio medio venta T4 [EUR_m2]",
    "Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T1 [%]",
    "Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T2 [%]",
    "Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T3 [%]",
    "Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero T4 [%]",
    "Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T1 [%]",
    "Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T2 [%]",
    "Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T3 [%]",
    "Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto T4 [%]",
]

NEW_SALE_QUARTERLY_COLS = [
    "Edificacion vivienda 2024 venta trimestral | Precio medio anual [EUR_m2]",
    "Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero medio [%]",
    "Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto medio [%]",
]

SALE_PORTAL_DROP_COLS = [
    "Edificacion vivienda 2024 venta idealista | Enero [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Febrero [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Marzo [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Abril [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Mayo [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Junio [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Julio [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Agosto [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Septiembre [EUR_m2]",
    "Edificacion vivienda 2024 venta idealista | Octubre [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Enero [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Febrero [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Marzo [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Abril [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Mayo [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Junio [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Julio [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Agosto [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Septiembre [EUR_m2]",
    "Edificacion vivienda 2024 venta fotocasa | Octubre [EUR_m2]",
]

RENT_IDEALISTA_DROP_COLS = [
    "Edificacion vivienda 2024 alquiler idealista | Enero [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Febrero [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Marzo [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Abril [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Mayo [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Junio [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Julio [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Agosto [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Septiembre [EUR_m2_mes]",
    "Edificacion vivienda 2024 alquiler idealista | Octubre [EUR_m2_mes]",
]

NEW_RENT_IDEALISTA_COLS = [
    "Edificacion vivienda 2024 alquiler idealista | Precio medio anual [EUR_m2_mes]",
]

RENT_FOTOCASA_DROP_COLS = [
    "Edificacion vivienda 2024 alquiler fotocasa | Enero [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Febrero [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Marzo [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Abril [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Mayo [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Junio [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Julio [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Agosto [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Septiembre [EUR_mes]",
    "Edificacion vivienda 2024 alquiler fotocasa | Octubre [EUR_mes]",
]

RENTAL_2023_DROP_COLS = [
    "Edificacion vivienda 2023 alquiler | Viviendas alquiladas total [n]",
    "Edificacion vivienda 2023 alquiler | Viviendas alquiladas colectivas [n]",
    "Edificacion vivienda 2023 alquiler | Viviendas alquiladas unifamiliares_rurales [n]",
    "Edificacion vivienda 2023 alquiler | Superficie colectiva p25 [m2]",
    "Edificacion vivienda 2023 alquiler | Superficie colectiva p75 [m2]",
    "Edificacion vivienda 2023 alquiler | Superficie unifamiliar mediana [m2]",
    "Edificacion vivienda 2023 alquiler | Superficie unifamiliar p25 [m2]",
    "Edificacion vivienda 2023 alquiler | Superficie unifamiliar p75 [m2]",
    "Edificacion vivienda 2023 alquiler | Cuantia colectiva p25 [EUR_mes]",
    "Edificacion vivienda 2023 alquiler | Cuantia colectiva p75 [EUR_mes]",
    "Edificacion vivienda 2023 alquiler | Cuantia unifamiliar mediana [EUR_mes]",
    "Edificacion vivienda 2023 alquiler | Cuantia unifamiliar p25 [EUR_mes]",
    "Edificacion vivienda 2023 alquiler | Cuantia unifamiliar p75 [EUR_mes]",
]

NEW_RENTAL_2023_COLS = [
    "Edificacion vivienda 2023 alquiler | Viviendas alquiladas [por_1000_hab]",
]

CATALAN_CADASTRAL_PCT_DROP_COLS = [
    "% Habitatges amb valor cadastral major de 48.000 euros [2025]",
    "% Habitatges amb valor cadastral menor de 18.000 euros [2025]",
]

HOUSING_COUNT_DROP_COLS = [
    "Nombre d'habitatges [2025]",
]

NEW_HOUSING_COUNT_COLS = [
    "Edificacion vivienda 2025 residencial | Viviendas [por_1000_hab]",
]

LICENSE_REHAB_DROP_COLS = [
    "Edificacion vivienda 2024 licencias construccion | Total [n]",
    "Edificacion vivienda 2024 licencias construccion | Viviendas [n]",
    "Edificacion vivienda 2024 licencias construccion | Aparcamientos [n]",
    "Edificacion vivienda 2024 licencias construccion | Industrial_comercial [n]",
    "Edificacion vivienda 2024 licencias construccion | Edificios [n]",
    "Edificacion vivienda 2024 licencias construccion | Viviendas con licencia [n]",
    "Edificacion vivienda 2024 licencias construccion | Garajes con licencia [n]",
    "Edificacion vivienda 2024 rehabilitacion | Integral [n]",
    "Edificacion vivienda 2024 rehabilitacion | Parcial [n]",
]

NEW_LICENSE_REHAB_COLS = [
    "Edificacion vivienda 2024 licencias construccion | Viviendas [por_1000_hab]",
    "Edificacion vivienda 2024 licencias construccion | Aparcamientos [por_1000_hab]",
    "Edificacion vivienda 2024 licencias construccion | Industrial/comercial [por_1000_hab]",
    "Edificacion vivienda 2024 licencias construccion | Edificios [por_1000_hab]",
    "Edificacion vivienda 2024 licencias construccion | Viviendas con licencia [por_1000_hab]",
    "Edificacion vivienda 2024 licencias construccion | Garajes con licencia [por_1000_hab]",
    "Edificacion vivienda 2024 rehabilitacion | Integral [por_1000_hab]",
    "Edificacion vivienda 2024 rehabilitacion | Parcial [por_1000_hab]",
]

INMUEBLES_USO_DROP_COLS = [
    "Edificacion vivienda 2025 inmuebles uso | Total [n]",
    "Edificacion vivienda 2025 inmuebles uso | Residencial [n]",
    "Edificacion vivienda 2025 inmuebles uso | Almacen_aparcamiento [n]",
    "Edificacion vivienda 2025 inmuebles uso | Comercial [n]",
    "Edificacion vivienda 2025 inmuebles uso | Oficinas [n]",
    "Edificacion vivienda 2025 inmuebles uso | Industrial [n]",
    "Edificacion vivienda 2025 inmuebles uso | Resto [n]",
]

NEW_INMUEBLES_USO_COLS = [
    "Edificacion vivienda 2025 inmuebles uso | Residencial [por_1000_hab]",
    "Edificacion vivienda 2025 inmuebles uso | Almacen/aparcamiento [por_1000_hab]",
    "Edificacion vivienda 2025 inmuebles uso | Comercial [por_1000_hab]",
    "Edificacion vivienda 2025 inmuebles uso | Oficinas [por_1000_hab]",
    "Edificacion vivienda 2025 inmuebles uso | Industrial [por_1000_hab]",
    "Edificacion vivienda 2025 inmuebles uso | Resto [por_1000_hab]",
]

ANTIGUEDAD_DROP_COLS = [
    "Percentatge d'habitatges amb menys de 10 anys [2025]",
    "Percentatge d'habitatges amb menys de 5 anys [2025]",
    "Percentatge d'habitatges amb més de 50 anys [2025]",
    "Edificacion vivienda 2025 residencial antiguedad | Total [n]",
    "Edificacion vivienda 2025 residencial antiguedad | <=1800 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 1801_1900 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 1901_1920 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 1921_1940 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 1941_1960 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 1961_1980 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 1981_2000 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 2001_2010 [n]",
    "Edificacion vivienda 2025 residencial antiguedad | 2011_2024 [n]",
]

NEW_ANTIGUEDAD_COLS = [
    "Edificacion vivienda 2025 residencial antiguedad | Menos de 5 anos [%]",
    "Edificacion vivienda 2025 residencial antiguedad | Menos de 10 anos [%]",
    "Edificacion vivienda 2025 residencial antiguedad | Menos de 25 anos [%]",
    "Edificacion vivienda 2025 residencial antiguedad | Mas de 30 anos aprox [%]",
    "Edificacion vivienda 2025 residencial antiguedad | Mas de 50 anos [%]",
    "Edificacion vivienda 2025 residencial antiguedad | Mas de 100 anos aprox [%]",
    "Edificacion vivienda 2025 residencial antiguedad | Mas de 220 anos aprox [%]",
]

VALUE_CADASTRAL_TRAMOS_DROP_COLS = [
    "Edificacion vivienda 2025 valor catastral tramos | Total [n]",
    "Edificacion vivienda 2025 valor catastral tramos | <=12k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | 12_18k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | 18_24k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | 24_30k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | 30_36k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | 36_48k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | 48_60k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | 60_72k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | >72k [n]",
    "Edificacion vivienda 2025 valor catastral tramos | No consta [n]",
]

NEW_VALUE_CADASTRAL_TRAMOS_COLS = [
    "Edificacion vivienda 2025 valor catastral tramos | Bajo <=18k [%]",
    "Edificacion vivienda 2025 valor catastral tramos | Medio 18_36k [%]",
    "Edificacion vivienda 2025 valor catastral tramos | Medio-alto 36_60k [%]",
    "Edificacion vivienda 2025 valor catastral tramos | Alto >60k [%]",
]

VALUE_CADASTRAL_MEDIO_DROP_COLS = [
    "Edificacion vivienda 2025 valor catastral medio | Numero inmuebles [n]",
]

MEDIO_AMBIENTE_DROP_COLS = [
    "Zonas verdes [n]",
    "Superficie zonas verdes [m2]",
    "Zonas verdes CSV - superficie poligono [m2]",
    "Zonas verdes CSV - superficie diciembre [m2]",
    "Zonas verdes [por_km2]",
    "Zonas verdes [por_1000_hab]",
    "Arbolado [n]",
    "Arbolado [por_km2]",
    "Arbolado [por_1000_hab]",
    "Ruido Lden [media]",
    "Ruido Lden [moda]",
    "Contaminacion - estacion asignada",
    "Contaminacion - periodo fuente",
    "Contaminacion - PM2.5(�g/m�) [media]",
    "Contaminacion - SO2(�g/m�) [media]",
    "Contaminacion - NO(�g/m�) [media]",
    "Contaminacion - NO2(�g/m�) [media]",
    "Contaminacion - PM10(�g/m�) [media]",
    "Contaminacion - NOx(�g/m�) [media]",
    "Contaminacion - Ozono(�g/m�) [media]",
    "Contaminacion - PM1(�g/m�) [media]",
    "Contaminacion - CO(mg/m�) [media]",
    "Contaminacion - Xileno(�g/m�) [media]",
    "Contaminacion - Tolueno(�g/m�) [media]",
    "Contaminacion - Benceno(�g/m�) [media]",
    "Contaminacion - Ruido(dBA) [media]",
    "Contaminacion - Ni(ng/m�) [media]",
    "Contaminacion - As(ng/m�) [media]",
    "Contaminacion - Pb(�g/m�) [media]",
    "Contaminacion - Cd(ng/m�) [media]",
    "Contaminacion - BaP(ng/m�) [media]",
    "Medio ambiente 2024 | Zonas verdes gestion municipal [n]",
    "Medio ambiente 2024 | Zonas verdes gestion municipal superficie [m2]",
]

NEW_MEDIO_AMBIENTE_COLS = [
    "Medio ambiente - Superficie zonas verdes [m2_hab]",
    "Medio ambiente - Arbolado [por_1000_hab]",
    "Medio ambiente - Ruido ambiental Lden [media]",
    "Medio ambiente - NO2 (trafico) [ug_m3_media]",
    "Medio ambiente - Contaminacion por particulas PM10_PM2.5 [indice_z]",
    "Medio ambiente - Ozono (contaminante secundario) [ug_m3_media]",
]

MOVILIDAD_DROP_COLS = [
    "Paradas EMT [n]",
    "Distribució percentual del nombre de turismes [2025]",
    "Edat mitjana dels turismes particulars [2025]",
    "Nombre de turismes [2025]",
    "Percentatge de turismes particulars de 10 i més anys [2025]",
    "Percentatge de turismes particulars de 16 i més CV [2025]",
    "Superfície d'aparcament per habitatge [2025]",
    "Superfície d'aparcament per turisme [2025]",
    "Trafico tramos - lectura media [actual]",
    "Trafico tramos - IMV media [actual]",
    "Itinerarios ciclistas - longitud total [m]",
    "Itinerarios ciclistas - tramos [n]",
    "Itinerarios ciclistas - tramos [por_km2]",
    "Itinerarios ciclistas - tramos [por_1000_hab]",
    "Aparcamientos totales [n]",
    "Aparcamientos libres [n]",
    "Aparcamientos ORA [n]",
    "Aparcamientos vados [n]",
    "Aparcamientos parkings [n]",
    "Aparcamientos totales [por_km2]",
    "Aparcamientos totales [por_1000_hab]",
    "Aparcamientos libres [por_km2]",
    "Aparcamientos libres [por_1000_hab]",
    "Aparcamientos ORA [por_km2]",
    "Aparcamientos ORA [por_1000_hab]",
    "Aparcamientos vados [por_km2]",
    "Aparcamientos vados [por_1000_hab]",
    "Aparcamientos parkings [por_km2]",
    "Aparcamientos parkings [por_1000_hab]",
]

NEW_MOVILIDAD_COLS = [
    "Movilidad - Paradas EMT [por_km2]",
    "Movilidad - Turismos [por_1000_hab]",
    "Movilidad - Edad media turismos particulares [anos]",
    "Movilidad - Superficie aparcamiento por vivienda [m2_vivienda]",
    "Movilidad - Superficie aparcamiento por turismo [m2_turismo]",
    "Movilidad - Aparcamiento publico o de rotacion [por_1000_hab]",
    "Movilidad - Aparcamiento asociado a vados [por_1000_hab]",
    "Movilidad - Itinerarios ciclistas [m_por_km2]",
    "Movilidad - Intensidad media de trafico IMV [actual]",
]


BIENESTAR_DROP_COLS = [
    # Asociaciones de ayuda social: se sustituyen recuentos, densidades por superficie y tasas antiguas
    # por una selección más interpretable de tasas por cada 1.000 habitantes.
    "Asociaciones ayuda social discapacidad [n]",
    "Asociaciones ayuda social enfermedad mental [n]",
    "Asociaciones ayuda social mayores [n]",
    "Asociaciones ayuda social sintecho [n]",
    "Asociaciones ayuda social etnicas [n]",
    "Asociaciones ayuda social poblacion general [n]",
    "Asociaciones ayuda adicciones [n]",
    "Asociaciones ayuda social discapacidad [por_km2]",
    "Asociaciones ayuda social discapacidad [por_1000_hab]",
    "Asociaciones ayuda social enfermedad mental [por_km2]",
    "Asociaciones ayuda social enfermedad mental [por_1000_hab]",
    "Asociaciones ayuda social mayores [por_km2]",
    "Asociaciones ayuda social mayores [por_1000_hab]",
    "Asociaciones ayuda social sintecho [por_km2]",
    "Asociaciones ayuda social sintecho [por_1000_hab]",
    "Asociaciones ayuda social etnicas [por_km2]",
    "Asociaciones ayuda social etnicas [por_1000_hab]",
    "Asociaciones ayuda social poblacion general [por_km2]",
    "Asociaciones ayuda social poblacion general [por_1000_hab]",
    "Asociaciones ayuda adicciones [por_km2]",
    "Asociaciones ayuda adicciones [por_1000_hab]",
    # Recursos sociales antiguos de discapacidad fisica: se conserva una versión normalizada y renombrada.
    "Recursos sociales discapacidad fisica [n]",
    "Recursos sociales discapacidad fisica [por_km2]",
    "Recursos sociales discapacidad fisica [por_1000_hab]",
    # Vulnerabilidad: se mantienen los indices y se eliminan los niveles categóricos.
    "Vulnerabilidad equipamientos [indice]",
    "Vulnerabilidad equipamientos [nivel]",
    "Vulnerabilidad demografia [indice]",
    "Vulnerabilidad demografia [nivel]",
    "Vulnerabilidad economia [indice]",
    "Vulnerabilidad economia [nivel]",
    "Vulnerabilidad global [indice]",
    "Vulnerabilidad global [nivel]",
    # Asociaciones generales por tipo.
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | No consta",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Total",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Otras Participación Social",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Asistencia Social",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Otras",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Profesionales y Económicas",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Culturales",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Deportivas",
    "Bienestar social | Asociaciones según distrito y tipo. 2024 | Otras Fiestas y Recreativas",
    # Cheques escolares.
    "Bienestar social | Distribución de concesiones de Cheques escolares según cobertura. Distritos. Curso 202425 | Población 0 a 5 años",
    "Bienestar social | Distribución de concesiones de Cheques escolares según cobertura. Distritos. Curso 202425 | Cheques concedidos",
    "Bienestar social | Distribución de concesiones de Cheques escolares según cobertura. Distritos. Curso 202425 | %",
    "Bienestar social | Distribución de concesiones de Cheques escolares según cobertura. Distritos. Curso 202425 | Cobertura",
    "Bienestar social | Distribución de solicitudes de Cheques escolares, concesiones y renta familiar media. Distritos. Curso 202425 | Solicitantes",
    "Bienestar social | Distribución de solicitudes de Cheques escolares, concesiones y renta familiar media. Distritos. Curso 202425 | Concedidos",
    "Bienestar social | Distribución de solicitudes de Cheques escolares, concesiones y renta familiar media. Distritos. Curso 202425 | Renta familiar media",
    "Bienestar social | Distribución de solicitudes de Cheques escolares, concesiones y renta familiar media. Distritos. Curso 202425 | Porcentaje de concedidos",
    # Pobreza material e infantil.
    "Pobreza 2025 movil | Si [%]",
    "Pobreza 2025 movil | No [%]",
    "Pobreza 2025 movil | NsNc [%]",
    "Pobreza 2025 imprevisto 650 EUR | Si [%]",
    "Pobreza 2025 imprevisto 650 EUR | No [%]",
    "Pobreza 2025 imprevisto 650 EUR | NsNc [%]",
    "Pobreza 2025 comer fuera mensual | Si [%]",
    "Pobreza 2025 comer fuera mensual | No [%]",
    "Pobreza 2025 comer fuera mensual | NsNc [%]",
    "Pobreza 2025 lavadora | Si [%]",
    "Pobreza 2025 lavadora | No [%]",
    "Pobreza 2025 lavadora | NsNc [%]",
    "Pobreza infantil 2021 | Tasa distrito [%]",
    "Pobreza infantil 2021 | Tasa C. A. [%]",
    "Pobreza infantil 2021 | Tasa nacional [%]",
    "Pobreza infantil 2021 | Dif. C. A. [p. p.]",
    "Pobreza infantil 2021 | Dif. nacional [p. p.]",
    "Pobreza infantil 2021 | Ninos distrito [n]",
    # Recursos sociales por sector de poblacion.
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Toda la población",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Conductas adictivas",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Familia, Menores y Adopciones",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Inmigración",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Enfermedad Mental",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Dependencia",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Discapacidad",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Mayores",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Personas presas y exreclusas",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Juventud",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Total",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Sin techo",
    "Bienestar social | Recursos por distrito y sector de población. 2025 | Mujeres",
]

NEW_BIENESTAR_COLS = [
    "Bienestar social - Vulnerabilidad equipamientos [indice]",
    "Bienestar social - Vulnerabilidad demografia [indice]",
    "Bienestar social - Vulnerabilidad economia [indice]",
    "Bienestar social - Vulnerabilidad global [indice]",
    "Bienestar social - Asociaciones discapacidad y enfermedad mental [por_1000_hab]",
    "Bienestar social - Asociaciones adicciones [por_1000_hab]",
    "Bienestar social - Asociaciones mayores [por_1000_hab]",
    "Bienestar social - Asociaciones sintecho [por_1000_hab]",
    "Bienestar social - Asociaciones etnicas [por_1000_hab]",
    "Bienestar social - Asociaciones poblacion general y participacion social [por_1000_hab]",
    "Bienestar social - Asociaciones culturales, deportivas y recreativas [por_1000_hab]",
    "Bienestar social - Asociaciones profesionales y economicas [por_1000_hab]",
    "Bienestar social - Recursos discapacidad fisica [por_1000_hab]",
    "Bienestar social - Recursos toda la poblacion [por_1000_hab]",
    "Bienestar social - Recursos conductas adictivas [por_1000_hab]",
    "Bienestar social - Recursos familia menores y adopciones [por_1000_hab]",
    "Bienestar social - Recursos inmigracion [por_1000_hab]",
    "Bienestar social - Recursos enfermedad mental [por_1000_hab]",
    "Bienestar social - Recursos dependencia [por_1000_hab]",
    "Bienestar social - Recursos discapacidad [por_1000_hab]",
    "Bienestar social - Recursos mayores [por_1000_hab]",
    "Bienestar social - Recursos personas presas y exreclusas [por_1000_hab]",
    "Bienestar social - Recursos juventud [por_1000_hab]",
    "Bienestar social - Recursos sin techo [por_1000_hab]",
    "Bienestar social - Recursos mujeres [por_1000_hab]",
    "Bienestar social - Cheques escolares cobertura poblacion de 0 a 5 anos [%]",
    "Bienestar social - Cheques escolares solicitantes [por_1000_hab]",
    "Bienestar social - Cheques escolares concedidos sobre solicitudes [%]",
    "Bienestar social - Renta familiar media solicitantes cheques escolares [EUR]",
    "Pobreza - No puede permitirse movil [%]",
    "Pobreza - No puede afrontar imprevisto 650 EUR [%]",
    "Pobreza - No tiene lavadora [%]",
    "Pobreza - Infantil (2021) Tasa distrito [%]",
]


EDUCACION_DROP_COLS = ["Població de 18 anys o més amb nivell d'estudis de Batxillerat o superior [2025]",
 "Població de 18 anys o més amb nivell d'estudis inferior a Batxillerat [2025]",
 'Centros educativos [n]',
 'Colecaminos - tramos [n]',
 'Colecaminos - longitud total [m]',
 'Area escolar secundaria [zona]',
 'Area escolar secundaria [fuente]',
 'Educacion primaria [% distrito, mayores 15, censo 2022]',
 '1a etapa secundaria [% distrito, mayores 15, censo 2022]',
 '2a etapa secundaria [% distrito, mayores 15, censo 2022]',
 'Educacion superior [% distrito, mayores 15, censo 2022]',
 'Anuario 2021 educacion | analfabetas [% distrito 16+]',
 'Anuario 2021 educacion | primarios incompletos [% distrito 16+]',
 'Padron 2025 titulacion 18+ | Total [n]',
 'Padron 2025 titulacion 18+ | No sabe leer ni escribir [n]',
 'Padron 2025 titulacion 18+ | Inferior a graduado escolar [n]',
 'Padron 2025 titulacion 18+ | Graduado escolar o equivalente [n]',
 'Padron 2025 titulacion 18+ | Bachiller FP2 o superior [n]']

EDUCACION_ALUMNADO_DROP_COLS = ['Educacion | Características generales del alumnado de Preescolar Educación Infantil por distrito. Curso 20242025 | '
 'Total',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil por distrito. Curso 20242025 | '
 'Mujeres',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil por distrito. Curso 20242025 | '
 'Sexo | Hombres',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil por distrito. Curso 20242025 | '
 'Titularidad del centro | Público',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil por distrito. Curso 20242025 | '
 'Privado',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'América del Sur',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'No consta',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'Asia y Oceanía',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'Total',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'Continente de Nacionalidad | Europa',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'Mujeres',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'América del Norte y Central',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'Privado',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'Sexo | Hombres',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'África',
 'Educacion | Características generales del alumnado de ESO de nacionalidad extranjera por distrito. Curso 20242025 | '
 'Titularidad del centro | Público',
 'Educacion | Centros y Unidades de ESO según titularidad del centro por distrito. Curso 20242025 | Privados',
 'Educacion | Centros y Unidades de ESO según titularidad del centro por distrito. Curso 20242025 | Centros | Total',
 'Educacion | Centros y Unidades de ESO según titularidad del centro por distrito. Curso 20242025 | Públicos',
 'Educacion | Centros y Unidades de ESO según titularidad del centro por distrito. Curso 20242025 | Alumnado por '
 'unidad | Total',
 'Educacion | Centros y Unidades de ESO según titularidad del centro por distrito. Curso 20242025 | Unidades | Total',
 'Educacion | Alumnado de ESO según titularidad del centro y curso por distrito. Curso 20242025 | Concertados',
 'Educacion | Alumnado de ESO según titularidad del centro y curso por distrito. Curso 20242025 | 1.º ESO | Total',
 'Educacion | Alumnado de ESO según titularidad del centro y curso por distrito. Curso 20242025 | Públicos',
 'Educacion | Alumnado de ESO según titularidad del centro y curso por distrito. Curso 20242025 | 2.º ESO | Total',
 'Educacion | Alumnado de ESO según titularidad del centro y curso por distrito. Curso 20242025 | 3.º ESO | Total',
 'Educacion | Alumnado de ESO según titularidad del centro y curso por distrito. Curso 20242025 | 4.º ESO | Total',
 'Educacion | Alumnado de ESO según titularidad del centro y curso por distrito. Curso 20242025 | Total alumnado',
 'Educacion | Características generales del alumnado de Bachillerato por distrito. Curso 20242025 | Total',
 'Educacion | Características generales del alumnado de Bachillerato por distrito. Curso 20242025 | Mujeres',
 'Educacion | Características generales del alumnado de Bachillerato por distrito. Curso 20242025 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Bachillerato por distrito. Curso 20242025 | Titularidad del '
 'centro | Público',
 'Educacion | Características generales del alumnado de Bachillerato por distrito. Curso 20242025 | Privado',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | América del Sur',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | Asia y Oceanía',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | Total',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | Continente Nacionalidad | Europa',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | Mujeres',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | América del Norte y Central',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | Privado',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | África',
 'Educacion | Características generales del alumnado de Bachillerato de nacionalidad extranjera por distrito. Curso '
 '20242025 | Titularidad del centro | Público',
 'Educacion | Centros y Unidades de Bachillerato según titularidad del centro por distrito. Curso 20242025 | Privados',
 'Educacion | Centros y Unidades de Bachillerato según titularidad del centro por distrito. Curso 20242025 | Centros | '
 'Total',
 'Educacion | Centros y Unidades de Bachillerato según titularidad del centro por distrito. Curso 20242025 | Públicos',
 'Educacion | Centros y Unidades de Bachillerato según titularidad del centro por distrito. Curso 20242025 | Públicas',
 'Educacion | Centros y Unidades de Bachillerato según titularidad del centro por distrito. Curso 20242025 | Alumnado '
 'por unidad | Total',
 'Educacion | Centros y Unidades de Bachillerato según titularidad del centro por distrito. Curso 20242025 | Unidades '
 '| Total',
 'Educacion | Alumnado de Bachillerato según titularidad del centro y curso por distrito. Curso 20242025 | Total '
 'alumnado',
 'Educacion | Alumnado de Bachillerato según titularidad del centro y curso por distrito. Curso 20242025 | Públicos',
 'Educacion | Alumnado de Bachillerato según titularidad del centro y curso por distrito. Curso 20242025 | 2.º '
 'Bachillerato LOGSE | Total',
 'Educacion | Alumnado de Bachillerato según titularidad del centro y curso por distrito. Curso 20242025 | 1.º '
 'Bachillerato LOGSE | Total',
 'Educacion | Alumnado de Bachillerato según titularidad del centro y curso por distrito. Curso 20242025 | Privados',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio por distrito. Curso 20242025 '
 '| Total',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio por distrito. Curso 20242025 '
 '| Mujeres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio por distrito. Curso 20242025 '
 '| Sexo | Hombres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio por distrito. Curso 20242025 '
 '| Titularidad del centro | Público',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio por distrito. Curso 20242025 '
 '| Privado',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | América del Sur',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | No consta',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | Asia y Oceanía',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | Total',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | Continente Nacionalidad | Europa',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | Mujeres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | América del Norte y Central',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | Privado',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | África',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Medio de nacionalidad extranjera '
 'por distrito. Curso 20242025 | Titularidad del centro | Público',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Medio según titularidad del centro por distrito. Curso '
 '20242025 | Privados',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Medio según titularidad del centro por distrito. Curso '
 '20242025 | Centros | Total',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Medio según titularidad del centro por distrito. Curso '
 '20242025 | Públicos',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Medio según titularidad del centro por distrito. Curso '
 '20242025 | Alumnado por unidad | Total',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Medio según titularidad del centro por distrito. Curso '
 '20242025 | Unidades | Total',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | América del Sur',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | No consta',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | Asia y Oceanía',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | Total',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | Continente Nacionalidad | Europa',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | Mujeres',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | América del Norte y Central',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | Privado',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | África',
 'Educacion | Características generales del alumnado de Preescolar Educación Infantil de nacionalidad extranjera por '
 'distrito. Curso 202425 | Titularidad del centro | Público',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Diferencia entre media expediente y '
 'media PAU',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Número de centros',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Media expediente de Bachillerato',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Alumnado presentado',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Media Nota de Acceso a la '
 'Universidad',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Porcentaje alumnado apto',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Alumnado matriculado',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Media PAU',
 'Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Alumnado apto',
 'Educacion | Alumnado de Ciclos Formativos de Grado Medio según titularidad del centro y curso por distrito. Curso '
 '20242025 | Total alumnado',
 'Educacion | Alumnado de Ciclos Formativos de Grado Medio según titularidad del centro y curso por distrito. Curso '
 '20242025 | Públicos',
 'Educacion | Alumnado de Ciclos Formativos de Grado Medio según titularidad del centro y curso por distrito. Curso '
 '20242025 | Segundo | Total',
 'Educacion | Alumnado de Ciclos Formativos de Grado Medio según titularidad del centro y curso por distrito. Curso '
 '20242025 | Primero | Total',
 'Educacion | Alumnado de Ciclos Formativos de Grado Medio según titularidad del centro y curso por distrito. Curso '
 '20242025 | Privados',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior por distrito. Curso '
 '20242025 | Total',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior por distrito. Curso '
 '20242025 | Mujeres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior por distrito. Curso '
 '20242025 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior por distrito. Curso '
 '20242025 | Titularidad del centro | Público',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior por distrito. Curso '
 '20242025 | Privado',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | América del Sur',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | Asia y Oceanía',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | Total',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | Continente Nacionalidad | Europa',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | Mujeres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | América del Norte y Central',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | Privado',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | África',
 'Educacion | Características generales del alumnado de Ciclos Formativos de Grado Superior de nacionalidad extranjera '
 'por distrito. Curso 20232023 | Titularidad del centro | Público',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Superior según titularidad del centro Distritos. Curso '
 '20242025 | Privados',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Superior según titularidad del centro Distritos. Curso '
 '20242025 | Centros | Total',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Superior según titularidad del centro Distritos. Curso '
 '20242025 | Públicos',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Superior según titularidad del centro Distritos. Curso '
 '20242025 | Alumnado por unidad | Total',
 'Educacion | Centros y Unidades de Ciclos Formativos de Grado Superior según titularidad del centro Distritos. Curso '
 '20242025 | Unidades | Total',
 'Educacion | Alumnado de Ciclos Formativos de Grado Superior según titularidad del centro y curso por distrito. Curso '
 '20242025 | Total Alumnado',
 'Educacion | Alumnado de Ciclos Formativos de Grado Superior según titularidad del centro y curso por distrito. Curso '
 '20242025 | Públicos',
 'Educacion | Alumnado de Ciclos Formativos de Grado Superior según titularidad del centro y curso por distrito. Curso '
 '20242025 | Segundo | Total',
 'Educacion | Alumnado de Ciclos Formativos de Grado Superior según titularidad del centro y curso por distrito. Curso '
 '20242025 | Primero | Total',
 'Educacion | Alumnado de Ciclos Formativos de Grado Superior según titularidad del centro y curso por distrito. Curso '
 '20242025 | Privados',
 'Educacion | Centros y Unidades de Preescolar Educación Infantil según tipo de centro por distrito. Curso 20242025 | '
 'Alumnado por unidad | Total',
 'Educacion | Centros y Unidades de Preescolar Educación Infantil según tipo de centro por distrito. Curso 20242025 | '
 'Privados Concertados',
 'Educacion | Centros y Unidades de Preescolar Educación Infantil según tipo de centro por distrito. Curso 20242025 | '
 'Públicos',
 'Educacion | Centros y Unidades de Preescolar Educación Infantil según tipo de centro por distrito. Curso 20242025 | '
 'Centros | Total',
 'Educacion | Centros y Unidades de Preescolar Educación Infantil según tipo de centro por distrito. Curso 20242025 | '
 'Privados no Concertados',
 'Educacion | Centros y Unidades de Preescolar Educación Infantil según tipo de centro por distrito. Curso 20242025 | '
 'Unidades | Total',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | '
 'Privados no Concertados',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | '
 '0-2 Años | Total',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | '
 'Públicos',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | 3 '
 'Años | Total',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | '
 'Privados Concertados',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | '
 'Unidades mixtas de segundo ciclo (3-5 Años) | Total',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | 5 '
 'Años | Total',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | '
 'Total alumnado',
 'Educacion | Alumnado de Preescolar Educación Infantil según tipo de centro y curso por distrito. Curso 20242025 | 4 '
 'Años | Total',
 'Educacion | Características generales del alumnado de Primaria por distrito. Curso 20242025 | Total',
 'Educacion | Características generales del alumnado de Primaria por distrito. Curso 20242025 | Mujeres',
 'Educacion | Características generales del alumnado de Primaria por distrito. Curso 20242025 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Primaria por distrito. Curso 20242025 | Titularidad del centro '
 '| Público',
 'Educacion | Características generales del alumnado de Primaria por distrito. Curso 20242025 | Privado',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | América del Sur',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | No consta',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | Asia y Oceanía',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | Total',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | Continente de Nacionalidad | Europa',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | Mujeres',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | América del Norte y Central',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | Privado',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | África',
 'Educacion | Características generales del alumnado de Primaria de nacionalidad extranjera por distrito. Curso '
 '20242025 | Titularidad del centro | Público',
 'Educacion | Centros y Unidades de Primaria según tipo de centro por distrito. Curso 20242025 | Privados',
 'Educacion | Centros y Unidades de Primaria según tipo de centro por distrito. Curso 20242025 | Centros | Total',
 'Educacion | Centros y Unidades de Primaria según tipo de centro por distrito. Curso 20242025 | Públicos',
 'Educacion | Centros y Unidades de Primaria según tipo de centro por distrito. Curso 20242025 | Alumnado por unidad | '
 'Total',
 'Educacion | Centros y Unidades de Primaria según tipo de centro por distrito. Curso 20242025 | Unidades | Total',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Concertados',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Primero | Total',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Públicos',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Segundo | Total',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Tercero | Total',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Sexto | Total',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Cuarto | Total',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Quinto | Total',
 'Educacion | Alumnado de Primaria según tipo de centro y curso por distrito. Curso 20242025 | Total alumnado',
 'Educacion | Características generales del alumnado de ESO por distrito. Curso 20242025 | Total',
 'Educacion | Características generales del alumnado de ESO por distrito. Curso 20242025 | Mujeres',
 'Educacion | Características generales del alumnado de ESO por distrito. Curso 20242025 | Sexo | Hombres',
 'Educacion | Características generales del alumnado de ESO por distrito. Curso 20242025 | Titularidad del centro | '
 'Público',
 'Educacion | Características generales del alumnado de ESO por distrito. Curso 20242025 | Privado']

NEW_EDUCACION_ALUMNADO_COLS = ['Educacion - Alumnado infantil [por_1000_hab]',
 'Educacion - Alumnado publico infantil [%]',
 'Educacion - Alumnado extranjero infantil [%]',
 'Educacion - Alumnado por unidad infantil [media]',
 'Educacion - Alumnado primaria [por_1000_hab]',
 'Educacion - Alumnado publico primaria [%]',
 'Educacion - Alumnado extranjero primaria [%]',
 'Educacion - Alumnado por unidad primaria [media]',
 'Educacion - Alumnado ESO [por_1000_hab]',
 'Educacion - Alumnado publico ESO [%]',
 'Educacion - Alumnado extranjero ESO [%]',
 'Educacion - Alumnado por unidad ESO [media]',
 'Educacion - Alumnado bachillerato [por_1000_hab]',
 'Educacion - Alumnado publico bachillerato [%]',
 'Educacion - Alumnado extranjero bachillerato [%]',
 'Educacion - Alumnado por unidad bachillerato [media]',
 'Educacion - Alumnado FP grado medio [por_1000_hab]',
 'Educacion - Alumnado publico FP grado medio [%]',
 'Educacion - Alumnado extranjero FP grado medio [%]',
 'Educacion - Alumnado por unidad FP grado medio [media]',
 'Educacion - Alumnado FP grado superior [por_1000_hab]',
 'Educacion - Alumnado publico FP grado superior [%]',
 'Educacion - Alumnado extranjero FP grado superior [%]',
 'Educacion - Alumnado por unidad FP grado superior [media]',
 'Educacion - PAU media [nota]',
 'Educacion - PAU alumnado apto [%]',
 'Educacion - PAU diferencia expediente-PAU [nota]',
 'Educacion - PAU alumnado presentado sobre matriculado [%]']

REPLACEMENT_GROUPS = [
    ("cadastral_pct_ca", CATALAN_CADASTRAL_PCT_DROP_COLS, []),
    ("educacion_drop", EDUCACION_DROP_COLS, []),
    ("educacion_alumnado", EDUCACION_ALUMNADO_DROP_COLS, NEW_EDUCACION_ALUMNADO_COLS),
    ("movilidad", MOVILIDAD_DROP_COLS, NEW_MOVILIDAD_COLS),
    ("bienestar", BIENESTAR_DROP_COLS, NEW_BIENESTAR_COLS),
    ("demografia", DEMOGRAFIA_DROP_COLS, NEW_DEMOGRAFIA_COLS),
    ("extranjeria", EXTRANJERIA_DROP_COLS, NEW_EXTRANJERIA_COLS),
    ("hechos", HECHOS_DROP_COLS, NEW_HECHOS_COLS),
    ("policia", POLICIA_DROP_COLS, NEW_POLICIA_COLS),
    ("bomberos", BOMBEROS_DROP_COLS, NEW_BOMBEROS_COLS),
    ("economia", ECONOMIA_DROP_COLS, NEW_ECONOMIA_COLS),
    ("tourism", TOURISM_DROP_COLS, NEW_TOURISM_COLS),
    ("medio_ambiente", MEDIO_AMBIENTE_DROP_COLS, NEW_MEDIO_AMBIENTE_COLS),
    ("sale_quarterly", SALE_QUARTERLY_DROP_COLS, NEW_SALE_QUARTERLY_COLS),
    ("sale_portal", SALE_PORTAL_DROP_COLS, []),
    ("rent_idealista", RENT_IDEALISTA_DROP_COLS, NEW_RENT_IDEALISTA_COLS),
    ("rent_fotocasa", RENT_FOTOCASA_DROP_COLS, []),
    ("rental_2023", RENTAL_2023_DROP_COLS, NEW_RENTAL_2023_COLS),
    ("housing_count", HOUSING_COUNT_DROP_COLS, NEW_HOUSING_COUNT_COLS),
    ("license_rehab", LICENSE_REHAB_DROP_COLS, NEW_LICENSE_REHAB_COLS),
    ("inmuebles_uso", INMUEBLES_USO_DROP_COLS, NEW_INMUEBLES_USO_COLS),
    ("antiguedad", ANTIGUEDAD_DROP_COLS, NEW_ANTIGUEDAD_COLS),
    ("valor_catastral_tramos", VALUE_CADASTRAL_TRAMOS_DROP_COLS, NEW_VALUE_CADASTRAL_TRAMOS_COLS),
    ("valor_catastral_medio_drop", VALUE_CADASTRAL_MEDIO_DROP_COLS, []),
]

CATEGORY_BY_NEW_COLUMN = {
    **{col: "Movilidad, seguridad y convivencia" for col in NEW_MOVILIDAD_COLS},
    **{col: "Educacion" for col in NEW_EDUCACION_ALUMNADO_COLS},
    **{col: "Sociedad y Bienestar" for col in NEW_BIENESTAR_COLS},
    **{col: "Sociedad y Bienestar" for col in NEW_DEMOGRAFIA_COLS},
    **{col: "Sociedad y Bienestar" for col in NEW_EXTRANJERIA_COLS},
    **{col: "Seguridad y convivencia" for col in NEW_HECHOS_COLS},
    **{col: "Seguridad y convivencia" for col in NEW_POLICIA_COLS},
    **{col: "Seguridad y convivencia" for col in NEW_BOMBEROS_COLS},
    **{col: "Economia" for col in NEW_ECONOMIA_COLS},
    **{col: "Economia" for col in NEW_TOURISM_COLS},
    **{col: "Medio Ambiente" for col in NEW_MEDIO_AMBIENTE_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_SALE_QUARTERLY_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_RENT_IDEALISTA_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_RENTAL_2023_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_HOUSING_COUNT_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_LICENSE_REHAB_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_INMUEBLES_USO_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_ANTIGUEDAD_COLS},
    **{col: "Urbanismo e infraestructuras" for col in NEW_VALUE_CADASTRAL_TRAMOS_COLS},
}


# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized.lower().strip()


def parse_es_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return float(value)
        except ValueError:
            return None
    text = str(value).strip()
    if not text:
        return None
    # Soporta tanto formato español original (30.510; 1.234,56)
    # como valores intermedios generados por pandas (30510.0).
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text:
        parts = text.split(".")
        if len(parts) > 1 and all(len(part) == 3 for part in parts[1:]):
            text = "".join(parts)
        # en otro caso se interpreta como decimal generado por pandas/Python
    try:
        return float(text)
    except ValueError:
        return None


def format_es_number(value: float | None) -> str:
    if value is None or pd.isna(value) or math.isnan(float(value)):
        return ""
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def safe_num(value: float | None) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(value)


def pct(part: float | None, total: float | None) -> float | None:
    if part is None or total is None or pd.isna(total) or total == 0:
        return None
    return (float(part) / float(total)) * 100.0


def rate_per_1000(part: float | None, population: float | None) -> float | None:
    if part is None or population is None or pd.isna(population) or population == 0:
        return None
    return (float(part) / float(population)) * 1000.0


def rate_per_km2(part: float | None, area_km2: float | None) -> float | None:
    if part is None or area_km2 is None or pd.isna(area_km2) or area_km2 == 0:
        return None
    return float(part) / float(area_km2)


def mean_non_null(values: list[float | None]) -> float | None:
    valid = [float(value) for value in values if value is not None and not pd.isna(value)]
    if not valid:
        return None
    return sum(valid) / len(valid)


def resolve_column(columns_by_norm: dict[str, str], normalized_name: str) -> str:
    try:
        return columns_by_norm[normalized_name]
    except KeyError as exc:
        raise KeyError(f"No se encontró la columna: {normalized_name}") from exc


def build_output_columns(original_columns: list[str]) -> list[str]:
    normalized_groups = [
        (name, {normalize_text(col) for col in drop_cols}, new_cols)
        for name, drop_cols, new_cols in REPLACEMENT_GROUPS
    ]

    output_columns: list[str] = []
    inserted_groups: set[str] = set()

    for column in original_columns:
        normalized_column = normalize_text(column)
        matched = False

        for group_name, drop_set, new_cols in normalized_groups:
            if normalized_column in drop_set:
                if new_cols and group_name not in inserted_groups:
                    output_columns.extend(new_cols)
                    inserted_groups.add(group_name)
                matched = True
                break

        if not matched:
            output_columns.append(column)

    return output_columns


# -----------------------------------------------------------------------------
# Construcción de la tabla derivada
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Reduccion adicional: consumo publico y servicios urbanos
# -----------------------------------------------------------------------------

CONSUMO_PUBLICO_DROP_COLS = [
    "Renta consumo precios 2024 agua | Facturacion [miles m3]",
    "Renta consumo precios 2024 agua | Litros facturados por habitante y dia",
    "Renta consumo precios 2024 alumbrado publico | Consumo electrico [kWh]",
    "Renta consumo precios 2024 alumbrado publico | Facturacion [EUR]",
    "Renta consumo precios 2024 pasos inferiores | Halogenos metalicos puntos [n]",
    "Renta consumo precios 2024 pasos inferiores | Otros puntos [n]",
    "Renta consumo precios 2024 pasos inferiores | Halogenos metalicos potencia [kW]",
    "Renta consumo precios 2024 pasos inferiores | Puntos alumbrado total [n]",
    "Renta consumo precios 2024 pasos inferiores | Vapor sodio puntos [n]",
    "Renta consumo precios 2024 pasos inferiores | Lamparas led potencia [kW]",
    "Renta consumo precios 2024 pasos inferiores | Potencia instalada total [kW]",
    "Renta consumo precios 2024 pasos inferiores | Lamparas led puntos [n]",
    "Renta consumo precios 2024 pasos inferiores | Vapor sodio potencia [kW]",
    "Renta consumo precios 2024 pasos inferiores | Otros potencia [kW]",
    "Renta consumo precios 2024 monumentos | Halogenos metalicos puntos [n]",
    "Renta consumo precios 2024 monumentos | Otros puntos [n]",
    "Renta consumo precios 2024 monumentos | Halogenos metalicos potencia [kW]",
    "Renta consumo precios 2024 monumentos | Puntos alumbrado total [n]",
    "Renta consumo precios 2024 monumentos | Vapor mercurio potencia [kW]",
    "Renta consumo precios 2024 monumentos | Vapor sodio puntos [n]",
    "Renta consumo precios 2024 monumentos | Lamparas led potencia [kW]",
    "Renta consumo precios 2024 monumentos | Vapor mercurio puntos [n]",
    "Renta consumo precios 2024 monumentos | Potencia instalada total [kW]",
    "Renta consumo precios 2024 monumentos | Lamparas led puntos [n]",
    "Renta consumo precios 2024 monumentos | Vapor sodio potencia [kW]",
    "Renta consumo precios 2024 monumentos | Otros potencia [kW]",
]

CONSUMO_PUBLICO_NEW_COLS = [
    "Consumo publico - Agua [litros_hab_dia]",
    "Consumo publico - Alumbrado publico [kWh_por_km2]",
    "Consumo publico - Pasos inferiores potencia instalada [kW_por_km2]",
    "Consumo publico - Monumentos potencia instalada [kW_por_km2]",
]


def reduce_consumo_publico(output_df: pd.DataFrame) -> pd.DataFrame:
    """Sustituye 26 columnas de consumo/precios por 4 indicadores sinteticos.

    La reduccion se aplica sobre la tabla ya construida para no interferir con
    el resto de transformaciones del script. Agua se conserva con su indicador
    ya normalizado por habitante y dia; alumbrado, pasos inferiores y monumentos
    se expresan por km2 porque son servicios/infrastructuras de cobertura
    territorial.
    """
    missing = [col for col in CONSUMO_PUBLICO_DROP_COLS if col not in output_df.columns]
    if missing:
        raise KeyError(f"Faltan columnas de consumo publico para depurar: {missing}")

    first_idx = min(output_df.columns.get_loc(col) for col in CONSUMO_PUBLICO_DROP_COLS)
    current_columns = output_df.columns.tolist()
    drop_set = set(CONSUMO_PUBLICO_DROP_COLS)
    final_columns: list[str] = []
    inserted = False
    for idx, column in enumerate(current_columns):
        if idx == first_idx and not inserted:
            final_columns.extend(CONSUMO_PUBLICO_NEW_COLS)
            inserted = True
        if column in drop_set:
            continue
        final_columns.append(column)

    def per_km2(value: float | None, area_km2: float | None) -> float | None:
        if value is None or area_km2 in (None, 0):
            return None
        return value / area_km2

    area_col = "Superficie distrito agregada [km2]"
    water_col = "Renta consumo precios 2024 agua | Litros facturados por habitante y dia"
    alumbrado_col = "Renta consumo precios 2024 alumbrado publico | Consumo electrico [kWh]"
    pasos_col = "Renta consumo precios 2024 pasos inferiores | Potencia instalada total [kW]"
    monumentos_col = "Renta consumo precios 2024 monumentos | Potencia instalada total [kW]"

    reduced_df = output_df.copy()
    for idx, row in reduced_df.iterrows():
        category_row = str(row.get("codigo", "")) == "__categoria__"
        if category_row:
            for column in CONSUMO_PUBLICO_NEW_COLS:
                reduced_df.at[idx, column] = "Medio Ambiente y servicios urbanos"
            continue

        area_km2 = parse_es_number(row.get(area_col))
        reduced_df.at[idx, "Consumo publico - Agua [litros_hab_dia]"] = format_es_number(
            parse_es_number(row.get(water_col))
        )
        reduced_df.at[idx, "Consumo publico - Alumbrado publico [kWh_por_km2]"] = format_es_number(
            per_km2(parse_es_number(row.get(alumbrado_col)), area_km2)
        )
        reduced_df.at[idx, "Consumo publico - Pasos inferiores potencia instalada [kW_por_km2]"] = format_es_number(
            per_km2(parse_es_number(row.get(pasos_col)), area_km2)
        )
        reduced_df.at[idx, "Consumo publico - Monumentos potencia instalada [kW_por_km2]"] = format_es_number(
            per_km2(parse_es_number(row.get(monumentos_col)), area_km2)
        )

    return reduced_df.loc[:, final_columns]



# -----------------------------------------------------------------------------
# Urbanismo e infraestructuras v12
# -----------------------------------------------------------------------------

URBANISMO_V12_RENAME_COLS = {
    "viviendas_protección_pública": "Viviendas proteccion publica [n]",
    "Percentatge d'habitatges de menys de 60 metres quadrats [2025]": "Vivienda - Viviendas de menos de 60 m2 [%]",
    "Percentatge d'habitatges de menys de 80 metres quadrats [2025]": "Vivienda - Viviendas de menos de 80 m2 [%]",
    "Superfície construïda mitjana dels habitatges [2025]": "Vivienda - Superficie construida media [m2]",
    "Valor cadastral mitjà per habitatge [2025]": "Vivienda - Valor catastral medio por vivienda [EUR]",
    "Valor cadastral mitjà per metre quadrat [2025]": "Vivienda - Valor catastral medio por m2 [EUR_m2]",
}

URBANISMO_V12_SIMPLE_DROP_COLS = [
    "Bancos en via publica [n]",
    "Manzanas catastrales [n]",
]

URBANISMO_V12_SOLARES_DROP_COLS = [
    "Superfície total de solars [2025]",
    "Edificacion vivienda 2025 solares | Numero [n]",
    "Edificacion vivienda 2025 solares | Superficie total [m2]",
    "Edificacion vivienda 2025 solares | Superficie media [m2]",
    "Edificacion vivienda 2025 solares | Valor total [EUR]",
    "Edificacion vivienda 2025 solares | Valor medio [EUR]",
    "Edificacion vivienda 2025 solares | Valor medio m2 [EUR]",
]

URBANISMO_V12_SOLARES_NEW_COLS = [
    "Urbanismo - Solares superficie [% superficie distrito]",
    "Urbanismo - Solares valor medio [EUR_m2]",
]

URBANISMO_V12_PAA_DROP_COLS = [
    "Programas de Actuacion Aislada [n]",
    "Programas de Actuacion Aislada - superficie total [m2]",
    "PAA - proyectos [por_km2]",
    "PAA - proyectos [por_1000_hab]",
]

URBANISMO_V12_PAA_NEW_COLS = [
    "Urbanismo - PAA proyectos [por_km2]",
    "Urbanismo - PAA superficie [% superficie distrito]",
]

URBANISMO_V12_RECURSOS_DROP_COLS = [
    "Recursos municipales 2025 edificios | Total [n]",
    "Recursos municipales 2025 edificios | Centros escolares municipales [n]",
    "Recursos municipales 2025 edificios | Suelo edificable [n]",
    "Recursos municipales 2025 edificios | Mercados [n]",
    "Recursos municipales 2025 edificios | Otros [n]",
    "Recursos municipales 2025 edificios | Edificios y locales publicos [n]",
    "Recursos municipales 2025 edificios | Fincas urbanas [n]",
    "Recursos municipales 2025 parcela edificios | Total [m2 parcela]",
    "Recursos municipales 2025 parcela edificios | Centros escolares municipales [m2 parcela]",
    "Recursos municipales 2025 parcela edificios | Suelo edificable [m2 parcela]",
    "Recursos municipales 2025 parcela edificios | Mercados [m2 parcela]",
    "Recursos municipales 2025 parcela edificios | Otros [m2 parcela]",
    "Recursos municipales 2025 parcela edificios | Edificios y locales publicos [m2 parcela]",
    "Recursos municipales 2025 parcela edificios | Fincas urbanas [m2 parcela]",
    "Recursos municipales 2025 edificios construidos | Total [m2 construidos]",
    "Recursos municipales 2025 edificios construidos | Centros escolares municipales [m2 construidos]",
    "Recursos municipales 2025 edificios construidos | Suelo edificable [m2 construidos]",
    "Recursos municipales 2025 edificios construidos | Mercados [m2 construidos]",
    "Recursos municipales 2025 edificios construidos | Otros [m2 construidos]",
    "Recursos municipales 2025 edificios construidos | Edificios y locales publicos [m2 construidos]",
    "Recursos municipales 2025 edificios construidos | Fincas urbanas [m2 construidos]",
    "Recursos municipales 2025 valor edificios | Total [EUR]",
    "Recursos municipales 2025 valor edificios | Centros escolares municipales [EUR]",
    "Recursos municipales 2025 valor edificios | Suelo edificable [EUR]",
    "Recursos municipales 2025 valor edificios | Mercados [EUR]",
    "Recursos municipales 2025 valor edificios | Otros [EUR]",
    "Recursos municipales 2025 valor edificios | Edificios y locales publicos [EUR]",
    "Recursos municipales 2025 valor edificios | Fincas urbanas [EUR]",
]

URBANISMO_V12_RECURSOS_NEW_COLS = [
    "Recursos municipales - Equipamientos basicos construidos [m2_por_1000_hab]",
    "Recursos municipales - Equipamientos basicos valor [EUR_por_1000_hab]",
    "Recursos municipales - Patrimonio y suelo municipal construidos [m2_por_1000_hab]",
    "Recursos municipales - Patrimonio y suelo municipal valor [EUR_por_1000_hab]",
    "Recursos municipales - Otros edificios construidos [m2_por_1000_hab]",
    "Recursos municipales - Otros edificios valor [EUR_por_1000_hab]",
]


def reduce_urbanismo_infraestructuras_v12(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Reduce y renombra parte del bloque de urbanismo e infraestructuras.

    La transformacion se aplica sobre la tabla ya depurada en fases previas.
    Sustituye recuentos absolutos de solares, PAA y recursos municipales por
    variables normalizadas y mas interpretables, y traduce nombres restantes del
    valenciano al castellano.
    """
    category = "Urbanismo e infraestructuras"

    def pct_local(part: float | None, total: float | None) -> float | None:
        if part is None or total in (None, 0):
            return None
        return (part / total) * 100.0

    def per_1000_local(part: float | None, population: float | None) -> float | None:
        if part is None or population in (None, 0):
            return None
        return (part / population) * 1000.0

    def safe_cell(row: pd.Series, col: str) -> float:
        return safe_num(parse_es_number(row.get(col)))

    def get_num(row: pd.Series, col: str) -> float | None:
        return parse_es_number(row.get(col)) if col in row.index else None

    # Añade filas de auditoria al reporte de correlaciones/redundancias.
    def append_report_rows() -> None:
        report_df = pd.read_csv(report_csv, dtype=str, encoding="utf-8") if report_csv.exists() else pd.DataFrame(
            columns=["bloque", "tipo_medida", "variable_1", "variable_2", "valor", "n_observaciones", "decision_metodologica"]
        )
        non_category_mask = output_df["codigo"].astype(str) != "__categoria__"
        rows: list[dict[str, str]] = []

        def fmt_report(value: float | None) -> str:
            if value is None or pd.isna(value):
                return ""
            return f"{float(value):.3f}".replace(".", ",")

        def add_corr(col_a: str, col_b: str, decision: str) -> None:
            if col_a not in output_df.columns or col_b not in output_df.columns:
                return
            pair_df = output_df.loc[non_category_mask, [col_a, col_b]].copy()
            pair_df[col_a] = pair_df[col_a].apply(parse_es_number)
            pair_df[col_b] = pair_df[col_b].apply(parse_es_number)
            pair_df = pair_df.dropna()
            corr_value = None if len(pair_df) < 2 else float(pair_df[col_a].corr(pair_df[col_b]))
            rows.append(
                {
                    "bloque": "Urbanismo e infraestructuras",
                    "tipo_medida": "correlacion_pearson",
                    "variable_1": col_a,
                    "variable_2": col_b,
                    "valor": fmt_report(corr_value),
                    "n_observaciones": str(len(pair_df)),
                    "decision_metodologica": decision,
                }
            )

        add_corr(
            "Edificacion vivienda 2025 superficie construida | Total [n]",
            "Edificacion vivienda 2025 residencial antiguedad | Total [n]",
            "La superficie construida por tramos clasifica el parque residencial por tamano; no se interpreta como solares ni parcelas urbanas.",
        )
        add_corr(
            "Edificacion vivienda 2025 superficie construida | Total [n]",
            "Edificacion vivienda 2025 solares | Numero [n]",
            "Se verifica que no es suma de solares; son dimensiones distintas.",
        )
        add_corr(
            "Edificacion vivienda 2025 parcelas urbanas | Total [n]",
            "Edificacion vivienda 2025 solares | Numero [n]",
            "Parcelas urbanas y solares son casi equivalentes en estos datos; se evita duplicar recuentos.",
        )
        add_corr(
            "Programas de Actuacion Aislada [n]",
            "PAA - proyectos [por_km2]",
            "Se conserva la densidad territorial de PAA y se elimina el recuento absoluto.",
        )
        add_corr(
            "Programas de Actuacion Aislada [n]",
            "PAA - proyectos [por_1000_hab]",
            "La tasa poblacional es derivada del mismo recuento; se prioriza la lectura territorial.",
        )
        add_corr(
            "Programas de Actuacion Aislada [n]",
            "Programas de Actuacion Aislada - superficie total [m2]",
            "Numero de PAA y superficie afectada no son equivalentes; se conserva tambien superficie normalizada.",
        )
        if rows:
            pd.concat([report_df, pd.DataFrame(rows)], ignore_index=True).to_csv(report_csv, index=False, encoding="utf-8")

    append_report_rows()

    all_drop = set(
        URBANISMO_V12_SIMPLE_DROP_COLS
        + URBANISMO_V12_SOLARES_DROP_COLS
        + URBANISMO_V12_PAA_DROP_COLS
        + URBANISMO_V12_RECURSOS_DROP_COLS
    )
    missing = [col for col in all_drop if col not in output_df.columns]
    if missing:
        raise KeyError(f"Faltan columnas de urbanismo para depurar: {missing}")

    final_columns: list[str] = []
    inserted_solares = False
    inserted_paa = False
    inserted_recursos = False
    for column in output_df.columns:
        if column in URBANISMO_V12_SOLARES_DROP_COLS:
            if not inserted_solares:
                final_columns.extend(URBANISMO_V12_SOLARES_NEW_COLS)
                inserted_solares = True
            continue
        if column in URBANISMO_V12_PAA_DROP_COLS:
            if not inserted_paa:
                final_columns.extend(URBANISMO_V12_PAA_NEW_COLS)
                inserted_paa = True
            continue
        if column in URBANISMO_V12_RECURSOS_DROP_COLS:
            if not inserted_recursos:
                final_columns.extend(URBANISMO_V12_RECURSOS_NEW_COLS)
                inserted_recursos = True
            continue
        if column in URBANISMO_V12_SIMPLE_DROP_COLS:
            continue
        final_columns.append(URBANISMO_V12_RENAME_COLS.get(column, column))

    reduced_df = output_df.copy()
    for idx, row in reduced_df.iterrows():
        category_row = str(row.get("codigo", "")) == "__categoria__"
        if category_row:
            for column in URBANISMO_V12_SOLARES_NEW_COLS + URBANISMO_V12_PAA_NEW_COLS + URBANISMO_V12_RECURSOS_NEW_COLS:
                reduced_df.at[idx, column] = category
            continue

        population = get_num(row, "Padron 2025 | Poblacion")
        area_ha = get_num(row, "Padron 2025 | Superficie [ha]")
        area_m2 = area_ha * 10000.0 if area_ha not in (None, 0) else get_num(row, "Superficie distrito agregada [m2]")

        solares_m2 = get_num(row, "Edificacion vivienda 2025 solares | Superficie total [m2]")
        if solares_m2 is None:
            solares_m2 = get_num(row, "Superfície total de solars [2025]")
        reduced_df.at[idx, "Urbanismo - Solares superficie [% superficie distrito]"] = format_es_number(pct_local(solares_m2, area_m2))
        reduced_df.at[idx, "Urbanismo - Solares valor medio [EUR_m2]"] = format_es_number(
            get_num(row, "Edificacion vivienda 2025 solares | Valor medio m2 [EUR]")
        )

        reduced_df.at[idx, "Urbanismo - PAA proyectos [por_km2]"] = format_es_number(get_num(row, "PAA - proyectos [por_km2]"))
        reduced_df.at[idx, "Urbanismo - PAA superficie [% superficie distrito]"] = format_es_number(
            pct_local(get_num(row, "Programas de Actuacion Aislada - superficie total [m2]"), area_m2)
        )

        equip_m2 = sum(
            safe_cell(row, col)
            for col in [
                "Recursos municipales 2025 edificios construidos | Centros escolares municipales [m2 construidos]",
                "Recursos municipales 2025 edificios construidos | Mercados [m2 construidos]",
                "Recursos municipales 2025 edificios construidos | Edificios y locales publicos [m2 construidos]",
            ]
        )
        equip_value = sum(
            safe_cell(row, col)
            for col in [
                "Recursos municipales 2025 valor edificios | Centros escolares municipales [EUR]",
                "Recursos municipales 2025 valor edificios | Mercados [EUR]",
                "Recursos municipales 2025 valor edificios | Edificios y locales publicos [EUR]",
            ]
        )
        patr_m2 = sum(
            safe_cell(row, col)
            for col in [
                "Recursos municipales 2025 edificios construidos | Suelo edificable [m2 construidos]",
                "Recursos municipales 2025 edificios construidos | Fincas urbanas [m2 construidos]",
            ]
        )
        patr_value = sum(
            safe_cell(row, col)
            for col in [
                "Recursos municipales 2025 valor edificios | Suelo edificable [EUR]",
                "Recursos municipales 2025 valor edificios | Fincas urbanas [EUR]",
            ]
        )
        otros_m2 = safe_cell(row, "Recursos municipales 2025 edificios construidos | Otros [m2 construidos]")
        otros_value = safe_cell(row, "Recursos municipales 2025 valor edificios | Otros [EUR]")

        for column, value in zip(
            URBANISMO_V12_RECURSOS_NEW_COLS,
            [
                per_1000_local(equip_m2, population),
                per_1000_local(equip_value, population),
                per_1000_local(patr_m2, population),
                per_1000_local(patr_value, population),
                per_1000_local(otros_m2, population),
                per_1000_local(otros_value, population),
            ],
        ):
            reduced_df.at[idx, column] = format_es_number(value)

    # Renombrado final de columnas en castellano.
    reduced_df = reduced_df.rename(columns=URBANISMO_V12_RENAME_COLS)
    return reduced_df.loc[:, final_columns]



# -----------------------------------------------------------------------------
# Urbanismo e infraestructuras v13
# -----------------------------------------------------------------------------

URBANISMO_V13_RECURSOS_RENAME_COLS = {
    "Recursos municipales - Equipamientos basicos construidos [m2_por_1000_hab]": "Recursos municipales - Centros escolares, mercados y locales publicos construidos [m2_por_1000_hab]",
    "Recursos municipales - Equipamientos basicos valor [EUR_por_1000_hab]": "Recursos municipales - Centros escolares, mercados y locales publicos valor [EUR_por_1000_hab]",
}

URBANISMO_V13_VPP_SOURCE_COL = "Viviendas proteccion publica [n]"
URBANISMO_V13_VPP_NEW_COLS = [
    "Vivienda - Viviendas proteccion publica [% viviendas]",
    "Vivienda - Viviendas proteccion publica [por_100_hab]",
]


def reduce_urbanismo_infraestructuras_v13(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Ajustes finales de urbanismo v13.

    - Cambia el nombre del grupo de recursos municipales para explicitar su
      contenido: centros escolares municipales, mercados y edificios/locales
      publicos.
    - Sustituye el recuento de viviendas de proteccion publica por dos medidas
      normalizadas: porcentaje sobre viviendas residenciales y tasa por 100
      habitantes.
    """
    category = "Urbanismo e infraestructuras"
    source_col = URBANISMO_V13_VPP_SOURCE_COL
    total_viviendas_col = "Edificacion vivienda 2025 superficie construida | Total [n]"
    population_col = "Padron 2025 | Poblacion"

    if source_col not in output_df.columns:
        raise KeyError(f"Falta la columna de viviendas de proteccion publica: {source_col}")
    if total_viviendas_col not in output_df.columns:
        raise KeyError(f"Falta la columna denominadora de viviendas: {total_viviendas_col}")
    if population_col not in output_df.columns:
        raise KeyError(f"Falta la columna denominadora de poblacion: {population_col}")

    def pct_local(part: float | None, total: float | None) -> float | None:
        if part is None or total in (None, 0):
            return None
        return (part / total) * 100.0

    def per_100_local(part: float | None, total: float | None) -> float | None:
        if part is None or total in (None, 0):
            return None
        return (part / total) * 100.0

    # Orden final: sustituye la columna [n] por las dos columnas nuevas.
    final_columns: list[str] = []
    for column in output_df.columns:
        if column == source_col:
            final_columns.extend(URBANISMO_V13_VPP_NEW_COLS)
            continue
        final_columns.append(URBANISMO_V13_RECURSOS_RENAME_COLS.get(column, column))

    reduced_df = output_df.copy()
    for idx, row in reduced_df.iterrows():
        category_row = str(row.get("codigo", "")) == "__categoria__"
        if category_row:
            for column in URBANISMO_V13_VPP_NEW_COLS:
                reduced_df.at[idx, column] = category
            continue

        vpp = parse_es_number(row.get(source_col))
        total_viviendas = parse_es_number(row.get(total_viviendas_col))
        population = parse_es_number(row.get(population_col))
        reduced_df.at[idx, "Vivienda - Viviendas proteccion publica [% viviendas]"] = format_es_number(
            pct_local(vpp, total_viviendas)
        )
        reduced_df.at[idx, "Vivienda - Viviendas proteccion publica [por_100_hab]"] = format_es_number(
            per_100_local(vpp, population)
        )

    # Añade una fila de auditoria sencilla al reporte.
    report_cols = ["bloque", "tipo_medida", "variable_1", "variable_2", "valor", "n_observaciones", "decision_metodologica"]
    report_df = pd.read_csv(report_csv, dtype=str, encoding="utf-8") if report_csv.exists() else pd.DataFrame(columns=report_cols)
    non_category_mask = reduced_df["codigo"].astype(str) != "__categoria__"
    valid_pairs = output_df.loc[non_category_mask, [source_col, total_viviendas_col]].copy()
    valid_pairs[source_col] = valid_pairs[source_col].apply(parse_es_number)
    valid_pairs[total_viviendas_col] = valid_pairs[total_viviendas_col].apply(parse_es_number)
    valid_pairs = valid_pairs.dropna()
    audit_row = {
        "bloque": "Urbanismo e infraestructuras",
        "tipo_medida": "normalizacion",
        "variable_1": source_col,
        "variable_2": total_viviendas_col + " / " + population_col,
        "valor": "",
        "n_observaciones": str(len(valid_pairs)),
        "decision_metodologica": "Se sustituye el recuento absoluto de viviendas de proteccion publica por porcentaje sobre viviendas residenciales y tasa por 100 habitantes.",
    }
    pd.concat([report_df, pd.DataFrame([audit_row])], ignore_index=True).to_csv(report_csv, index=False, encoding="utf-8")

    reduced_df = reduced_df.rename(columns=URBANISMO_V13_RECURSOS_RENAME_COLS)
    return reduced_df.loc[:, final_columns]


# -----------------------------------------------------------------------------
# Reducción v14: bloque Otros / política, participación y demografía residual
# -----------------------------------------------------------------------------

def reduce_bloque_otros_v15(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Reduce el bloque Otros: elecciones, votos, WiFi y demografía residual."""
    participation_cols = [
        "% Participació a les Eleccions Autonòmiques [2023]",
        "% Participació a les Eleccions Europees [2024]",
        "% Participació a les Eleccions Generals [2023]",
        "% Participació a les Eleccions Locals [2023]",
    ]
    demog_old = [
        "Creixement vegetatiu registrat al Padró [2024]",
        "Nombre mitjà de persones per full familiar [2025]",
        "Població emigrant [2024]",
        "Proporció de població major de 64 anys [2025]",
        "Superficie distrito agregada [m2]",
        "Superficie distrito agregada [km2]",
    ]
    wifi_drop = ["Puntos WiFi [n]"]
    suggestions_drop = ["Recursos municipales 2024 | Sugerencias quejas y reclamaciones [n]"]
    elect_admin = [
        "Elecciones 2023 autonomicas | Electorado",
        "Elecciones 2023 autonomicas | Votos Leídos",
        "Elecciones 2023 autonomicas | Votos Nulos",
        "Elecciones 2023 autonomicas | Votos en Blanco",
        "Elecciones 2023 autonomicas | Votos a Candidaturas",
        "Elecciones 2024 europeas | Electorado",
        "Elecciones 2024 europeas | Vots Leídos",
        "Elecciones 2024 europeas | Votos Nulos",
        "Elecciones 2024 europeas | Votos Válidos",
        "Elecciones 2024 europeas | Votos en Blanco",
        "Elecciones 2024 europeas | Votos a Candidaturas",
        "Elecciones 2023 generales | Electorado",
        "Elecciones 2023 generales | Votos Leídos",
        "Elecciones 2023 generales | Votos Nulos",
        "Elecciones 2023 generales | Votos Válidos",
        "Elecciones 2023 generales | Votos en Blanco",
        "Elecciones 2023 municipales | Electorado",
        "Elecciones 2023 municipales | Votos Leídos",
        "Elecciones 2023 municipales | Votos Nulos",
        "Elecciones 2023 municipales | Votos en Blanco",
        "Elecciones 2023 municipales | Votos a Candidaturas",
    ]
    vote_cols = [
        "Votos 2023 generales | PP [n]",
        "Votos 2023 generales | PSOE [n]",
        "Votos 2023 generales | SUMAR_COMPROMÍS [n]",
        "Votos 2023 generales | VOX [n]",
        "Votos 2023 generales | Otros [n]",
        "Votos 2023 autonomicas | PP [n]",
        "Votos 2023 autonomicas | PSOE [n]",
        "Votos 2023 autonomicas | COMPROMÍS [n]",
        "Votos 2023 autonomicas | VOX [n]",
        "Votos 2023 autonomicas | UNIDES_PODEM [n]",
        "Votos 2023 autonomicas | C's [n]",
        "Votos 2023 autonomicas | Otros [n]",
        "Votos 2024 europeas | PP [n]",
        "Votos 2024 europeas | PSOE [n]",
        "Votos 2024 europeas | VOX [n]",
        "Votos 2024 europeas | COMPROMÍS_SUMAR [n]",
        "Votos 2024 europeas | SE_ACABÓ_LA_FIESTA [n]",
        "Votos 2024 europeas | PODEMOS [n]",
        "Votos 2024 europeas | Otros [n]",
        "Votos 2023 municipales | PP [n]",
        "Votos 2023 municipales | COMPROMÍS_MUNICIPAL [n]",
        "Votos 2023 municipales | PSOE [n]",
        "Votos 2023 municipales | VOX [n]",
        "Votos 2023 municipales | PODEM___EUPV [n]",
        "Votos 2023 municipales | Cs [n]",
        "Votos 2023 municipales | Otros [n]",
    ]
    politics_new = [
        "Politica - Participacion electoral media [%]",
        "Politica - Votos nulos media [% votos emitidos]",
        "Politica - Votos en blanco media [% votos validos]",
        "Politica - Votos a candidaturas media [% votos validos]",
        "Politica - PP [% votos candidaturas media]",
        "Politica - PSOE [% votos candidaturas media]",
        "Politica - Compromis Sumar [% votos candidaturas media]",
        "Politica - VOX [% votos candidaturas media]",
        "Politica - Podemos Unides [% votos candidaturas media]",
        "Politica - Ciudadanos [% votos candidaturas media]",
        "Politica - Se Acabo La Fiesta [% votos candidaturas media]",
        "Politica - Otros partidos [% votos candidaturas media]",
        "Politica - Bloque izquierda PSOE_Compromis_Podemos [% votos candidaturas media]",
        "Politica - Bloque derecha PP_VOX_Cs_SALF [% votos candidaturas media]",
    ]
    demog_new = [
        "Demografia - Crecimiento vegetativo [por_1000_hab]",
        "Demografia - Personas por hogar [media]",
        "Demografia - Poblacion emigrante [% poblacion]",
    ]
    all_drop = set(participation_cols + demog_old + wifi_drop + suggestions_drop + elect_admin + vote_cols)
    existing_drop = [col for col in all_drop if col in output_df.columns]
    if not existing_drop:
        return output_df

    reduced_df = output_df.copy()
    category_mask = reduced_df["codigo"].astype(str) == "__categoria__"
    non_category_mask = ~category_mask
    population_col = "Padron 2025 | Poblacion"

    for col in politics_new:
        reduced_df[col] = ""
        reduced_df.loc[category_mask, col] = "Otros"
    for col in demog_new:
        reduced_df[col] = ""
        reduced_df.loc[category_mask, col] = "Sociedad y Bienestar"

    def row_number(row: pd.Series, column: str) -> float | None:
        return parse_es_number(row[column]) if column in row.index else None

    specs = {
        "autonomicas": {
            "part": "% Participació a les Eleccions Autonòmiques [2023]",
            "read": "Elecciones 2023 autonomicas | Votos Leídos",
            "nulos": "Elecciones 2023 autonomicas | Votos Nulos",
            "blanco": "Elecciones 2023 autonomicas | Votos en Blanco",
            "candidaturas": "Elecciones 2023 autonomicas | Votos a Candidaturas",
            "parties": {
                "PP": "Votos 2023 autonomicas | PP [n]",
                "PSOE": "Votos 2023 autonomicas | PSOE [n]",
                "COMP": "Votos 2023 autonomicas | COMPROMÍS [n]",
                "VOX": "Votos 2023 autonomicas | VOX [n]",
                "POD": "Votos 2023 autonomicas | UNIDES_PODEM [n]",
                "CS": "Votos 2023 autonomicas | C's [n]",
                "OTROS": "Votos 2023 autonomicas | Otros [n]",
            },
        },
        "europeas": {
            "part": "% Participació a les Eleccions Europees [2024]",
            "read": "Elecciones 2024 europeas | Vots Leídos",
            "nulos": "Elecciones 2024 europeas | Votos Nulos",
            "validos": "Elecciones 2024 europeas | Votos Válidos",
            "blanco": "Elecciones 2024 europeas | Votos en Blanco",
            "candidaturas": "Elecciones 2024 europeas | Votos a Candidaturas",
            "parties": {
                "PP": "Votos 2024 europeas | PP [n]",
                "PSOE": "Votos 2024 europeas | PSOE [n]",
                "VOX": "Votos 2024 europeas | VOX [n]",
                "COMP": "Votos 2024 europeas | COMPROMÍS_SUMAR [n]",
                "SALF": "Votos 2024 europeas | SE_ACABÓ_LA_FIESTA [n]",
                "POD": "Votos 2024 europeas | PODEMOS [n]",
                "OTROS": "Votos 2024 europeas | Otros [n]",
            },
        },
        "generales": {
            "part": "% Participació a les Eleccions Generals [2023]",
            "read": "Elecciones 2023 generales | Votos Leídos",
            "nulos": "Elecciones 2023 generales | Votos Nulos",
            "validos": "Elecciones 2023 generales | Votos Válidos",
            "blanco": "Elecciones 2023 generales | Votos en Blanco",
            "parties": {
                "PP": "Votos 2023 generales | PP [n]",
                "PSOE": "Votos 2023 generales | PSOE [n]",
                "COMP": "Votos 2023 generales | SUMAR_COMPROMÍS [n]",
                "VOX": "Votos 2023 generales | VOX [n]",
                "OTROS": "Votos 2023 generales | Otros [n]",
            },
        },
        "municipales": {
            "part": "% Participació a les Eleccions Locals [2023]",
            "read": "Elecciones 2023 municipales | Votos Leídos",
            "nulos": "Elecciones 2023 municipales | Votos Nulos",
            "blanco": "Elecciones 2023 municipales | Votos en Blanco",
            "candidaturas": "Elecciones 2023 municipales | Votos a Candidaturas",
            "parties": {
                "PP": "Votos 2023 municipales | PP [n]",
                "COMP": "Votos 2023 municipales | COMPROMÍS_MUNICIPAL [n]",
                "PSOE": "Votos 2023 municipales | PSOE [n]",
                "VOX": "Votos 2023 municipales | VOX [n]",
                "POD": "Votos 2023 municipales | PODEM___EUPV [n]",
                "CS": "Votos 2023 municipales | Cs [n]",
                "OTROS": "Votos 2023 municipales | Otros [n]",
            },
        },
    }

    for idx, row in reduced_df.loc[non_category_mask].iterrows():
        population = row_number(row, population_col)
        if demog_old[0] in reduced_df.columns:
            reduced_df.at[idx, demog_new[0]] = format_es_number(rate_per_1000(row_number(row, demog_old[0]), population))
        if demog_old[1] in reduced_df.columns:
            reduced_df.at[idx, demog_new[1]] = format_es_number(row_number(row, demog_old[1]))
        if demog_old[2] in reduced_df.columns:
            reduced_df.at[idx, demog_new[2]] = format_es_number(pct(row_number(row, demog_old[2]), population))

        participation_values: list[float | None] = []
        nulos_pct_values: list[float | None] = []
        blancos_pct_values: list[float | None] = []
        candidaturas_pct_values: list[float | None] = []
        shares: dict[str, list[float | None]] = {
            key: [] for key in ["PP", "PSOE", "COMP", "VOX", "POD", "CS", "SALF", "OTROS", "LEFT", "RIGHT"]
        }
        for spec in specs.values():
            participation_values.append(row_number(row, spec["part"]))
            read = row_number(row, spec.get("read", ""))
            nulos = row_number(row, spec.get("nulos", ""))
            blancos = row_number(row, spec.get("blanco", ""))
            candidaturas = row_number(row, spec.get("candidaturas", "")) if spec.get("candidaturas") else None
            validos = row_number(row, spec.get("validos", "")) if spec.get("validos") else None
            party_values = {key: row_number(row, col) for key, col in spec["parties"].items()}
            party_sum = sum(value for value in party_values.values() if value is not None)
            if candidaturas is None:
                candidaturas = party_sum if party_sum else ((validos - blancos) if validos is not None and blancos is not None else None)
            if validos is None and (candidaturas is not None or blancos is not None):
                validos = (candidaturas or 0.0) + (blancos or 0.0)

            nulos_pct_values.append(pct(nulos, read))
            blancos_pct_values.append(pct(blancos, validos))
            candidaturas_pct_values.append(pct(candidaturas, validos))
            denominator = candidaturas if candidaturas not in (None, 0) else party_sum
            for key, value in party_values.items():
                shares[key].append(pct(value, denominator))
            left_votes = sum((party_values.get(key) or 0.0) for key in ["PSOE", "COMP", "POD"])
            right_votes = sum((party_values.get(key) or 0.0) for key in ["PP", "VOX", "CS", "SALF"])
            shares["LEFT"].append(pct(left_votes, denominator))
            shares["RIGHT"].append(pct(right_votes, denominator))

        values_by_column = {
            politics_new[0]: mean_non_null(participation_values),
            politics_new[1]: mean_non_null(nulos_pct_values),
            politics_new[2]: mean_non_null(blancos_pct_values),
            politics_new[3]: mean_non_null(candidaturas_pct_values),
            politics_new[4]: mean_non_null(shares["PP"]),
            politics_new[5]: mean_non_null(shares["PSOE"]),
            politics_new[6]: mean_non_null(shares["COMP"]),
            politics_new[7]: mean_non_null(shares["VOX"]),
            politics_new[8]: mean_non_null(shares["POD"]),
            politics_new[9]: mean_non_null(shares["CS"]),
            politics_new[10]: mean_non_null(shares["SALF"]),
            politics_new[11]: mean_non_null(shares["OTROS"]),
            politics_new[12]: mean_non_null(shares["LEFT"]),
            politics_new[13]: mean_non_null(shares["RIGHT"]),
        }
        for column, value in values_by_column.items():
            reduced_df.at[idx, column] = format_es_number(value)

    output_columns: list[str] = []
    inserted_politics = False
    inserted_demography = False
    for column in output_df.columns:
        if column in all_drop:
            if column in participation_cols + elect_admin + vote_cols:
                if not inserted_politics:
                    output_columns.extend(politics_new)
                    inserted_politics = True
            elif column in demog_old:
                if not inserted_demography:
                    output_columns.extend(demog_new)
                    inserted_demography = True
            continue
        output_columns.append(column)
    reduced_df = reduced_df[output_columns].copy()

    audit_rows = []
    non_category_mask = reduced_df["codigo"].astype(str) != "__categoria__"
    for column in politics_new + demog_new:
        values = [parse_es_number(value) for value in reduced_df.loc[non_category_mask, column].tolist()]
        values = [value for value in values if value is not None]
        audit_rows.append(
            {
                "bloque": "Otros / politica y demografia residual",
                "decision": column,
                "criterio": "variable derivada v15; media distrital orientativa",
                "valor": format_es_number(sum(values) / len(values) if values else None),
            }
        )
    if audit_rows:
        report_df = pd.read_csv(report_csv, encoding="utf-8", dtype=str) if report_csv.exists() else pd.DataFrame()
        audit_df = pd.DataFrame(audit_rows)
        if not report_df.empty:
            for column in report_df.columns:
                if column not in audit_df.columns:
                    audit_df[column] = ""
            for column in audit_df.columns:
                if column not in report_df.columns:
                    report_df[column] = ""
            report_df = pd.concat([report_df, audit_df[report_df.columns]], ignore_index=True)
        else:
            report_df = audit_df
        report_df.to_csv(report_csv, index=False, encoding="utf-8")

    return reduced_df


def reduce_sociedad_demografia_secundaria_v16(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Traduce y reduce demografía secundaria, hogares, fecundidad, migración e innovación social."""
    category_mask = output_df["codigo"].astype(str) == "__categoria__"
    non_category_mask = ~category_mask
    population_col = "Padron 2025 | Poblacion"

    def row_number(row: pd.Series, column: str) -> float | None:
        return parse_es_number(row[column]) if column in row.index else None

    def source_value(column: str):
        return lambda row: row_number(row, column)

    def rate_source_value(column: str):
        return lambda row: rate_per_1000(row_number(row, column), row_number(row, population_col))

    new_specs: list[tuple[str, object]] = [
        ("Demografia - Indice de aloctonia estatal [2025]", source_value("Índex d'aloctonia estatal [2025]")),
        ("Demografia - Indice de sobre-envejecimiento [2025]", source_value("Índex de sobrenvelliment [2025]")),
        ("Demografia - Indice demografico de dependencia [2025]", source_value("Índex demogràfic de dependència global [2025]")),
        ("Demografia - Indice de envejecimiento [2025]", source_value("Índex d'envelliment [2025]")),
        ("Demografia - Hogares con dos menores de 18 anos [%]", source_value("Percentatge de fulls familiars amb dos menors de 18 anys [2025]")),
        ("Demografia - Hogares con tres o mas menores de 18 anos [%]", source_value("Percentatge de fulls familiars amb tres o més menors de 18 anys [2025]")),
        ("Demografia - Hogares de 2 personas [%]", source_value("Percentatge de fulls familiars de 2 persones [2025]")),
        ("Demografia - Hogares de 5 o mas personas [%]", source_value("Percentatge de fulls familiars de 5 o més persones [2025]")),
        ("Demografia - Hogares solo personas mayores de 64 anos [%]", source_value("Percentatge de fulls familiars de només persones majors de 64 anys [2025]")),
        ("Demografia - Hogares solo personas mayores de 79 anos [%]", source_value("Percentatge de fulls familiars de només persones majors de 79 anys [2025]")),
        ("Demografia - Hogares unipersonales [%]", source_value("Percentatge de fulls familiars unipersonals [2025]")),
        ("Demografia - Poblacion inmigrante [% poblacion]", lambda row: pct(row_number(row, "Població immigrant [2024]"), row_number(row, population_col))),
        ("Demografia - Saldo neto [n]", source_value("Saldo net [2024]")),
        ("Demografia - Tasa general de fecundidad [2024]", source_value("Taxa global de fecunditat registrada al Padró [2024]")),
        ("Demografia - Personas solteras [%]", source_value("Anuario 2021 estado civil | solteras [% distrito]")),
        ("Demografia - Personas casadas [%]", source_value("Anuario 2021 estado civil | casadas [% distrito]")),
        ("Demografia - Personas viudas [%]", source_value("Anuario 2021 estado civil | viudas [% distrito]")),
        ("Demografia - Personas separadas o divorciadas [%]", source_value("Anuario 2021 estado civil | separadas o divorciadas [% distrito]")),
        ("Demografia - Tasa bruta de natalidad [2024]", source_value("Encuesta demografica 2024 | Tasa bruta de natalidad")),
        ("Demografia - Tasa bruta de inmigracion intraurbana [2024]", source_value("Encuesta demografica 2024 | Tasa bruta de inmigracion intraurbana")),
        ("Demografia - Tasa bruta de inmigracion interurbana [2024]", source_value("Encuesta demografica 2024 | Tasa bruta de inmigracion interurbana")),
        ("Demografia - Tasa bruta de mortalidad [2024]", source_value("Encuesta demografica 2024 | Tasa bruta de mortalidad")),
        ("Demografia - Tasa bruta de emigracion intraurbana [2024]", source_value("Encuesta demografica 2024 | Tasa bruta de emigracion intraurbana")),
        ("Demografia - Tasa bruta de emigracion interurbana [2024]", source_value("Encuesta demografica 2024 | Tasa bruta de emigracion interurbana")),
        ("Demografia - Relacion de masculinidad [hombres_por_100_mujeres]", source_value("Encuesta demografica 2025 | Relacion de masculinidad")),
        ("Demografia - Razon de progresividad demografica [2025]", source_value("Encuesta demografica 2025 | Razon de progresividad demografica")),
        ("Innovacion social - Proyectos [por_km2]", source_value("Proyectos de innovacion social [por_km2]")),
        ("Innovacion social - Proyectos [por_1000_hab]", source_value("Proyectos de innovacion social [por_1000_hab]")),
    ]

    old_columns = [
        "Índex d'aloctonia estatal [2025]",
        "Índex de sobrenvelliment [2025]",
        "Índex demogràfic de dependència global [2025]",
        "Índex d'envelliment [2025]",
        "Majors de 64 anys en fulls familiars unipersonals [2025]",
        "Naixements registrats al Padró [2024]",
        "Percentatge de fulls familiars amb dos menors de 18 anys [2025]",
        "Percentatge de fulls familiars amb tres o més menors de 18 anys [2025]",
        "Percentatge de fulls familiars de 2 persones [2025]",
        "Percentatge de fulls familiars de 5 o més persones [2025]",
        "Percentatge de fulls familiars de només persones majors de 64 anys [2025]",
        "Percentatge de fulls familiars de només persones majors de 79 anys [2025]",
        "Percentatge de fulls familiars unipersonals [2025]",
        "Població immigrant [2024]",
        "Saldo net [2024]",
        "Taxa global de fecunditat registrada al Padró [2024]",
        "Proyectos de innovacion social [n]",
        "Proyectos de innovacion social [por_km2]",
        "Proyectos de innovacion social [por_1000_hab]",
        "INE 2023 demograficos | Porcentaje de hogares unipersonales [distrito]",
        "INE 2023 demograficos | Tamaño medio del hogar [distrito]",
        "Anuario 2021 estado civil | solteras [% distrito]",
        "Anuario 2021 estado civil | casadas [% distrito]",
        "Anuario 2021 estado civil | viudas [% distrito]",
        "Anuario 2021 estado civil | separadas o divorciadas [% distrito]",
        "Encuesta demografica 2024 | Tasa bruta de natalidad",
        "Encuesta demografica 2024 | Tasa bruta de inmigracion intraurbana",
        "Encuesta demografica 2024 | Tasa bruta de inmigracion interurbana",
        "Encuesta demografica 2024 | Tasa bruta de mortalidad",
        "Encuesta demografica 2024 | Tasa bruta de emigracion intraurbana",
        "Encuesta demografica 2024 | Tasa bruta de emigracion interurbana",
        "Encuesta demografica 2024 | Tasa general de fecundidad",
        "Encuesta demografica 2025 | Relacion de masculinidad",
        "Encuesta demografica 2025 | Indice de envejecimiento",
        "Encuesta demografica 2025 | Indice de sobre-envejecimiento",
        "Encuesta demografica 2025 | Indice demografico de dependencia",
        "Encuesta demografica 2025 | Razon de progresividad demografica",
    ]
    old_set = {column for column in old_columns if column in output_df.columns}
    if not old_set:
        return output_df

    reduced_df = output_df.copy()
    new_columns = [name for name, _ in new_specs]
    for name, function in new_specs:
        reduced_df[name] = ""
        reduced_df.loc[category_mask, name] = "Sociedad y Bienestar"
        for idx, row in reduced_df.loc[non_category_mask].iterrows():
            try:
                reduced_df.at[idx, name] = format_es_number(function(row))
            except KeyError:
                reduced_df.at[idx, name] = ""

    output_columns: list[str] = []
    inserted = False
    for column in reduced_df.columns:
        if column in old_set:
            if not inserted:
                output_columns.extend(new_columns)
                inserted = True
            continue
        if column in new_columns:
            continue
        output_columns.append(column)
    if not inserted:
        output_columns.extend(new_columns)
    reduced_df = reduced_df[output_columns].copy()

    audit_rows = []
    for name in new_columns:
        values = [parse_es_number(value) for value in reduced_df.loc[non_category_mask, name].tolist()]
        values = [value for value in values if value is not None]
        audit_rows.append(
            {
                "bloque": "Sociedad y Bienestar / demografia secundaria",
                "decision": name,
                "criterio": "variable traducida, normalizada o seleccionada frente a duplicados v17",
                "valor": format_es_number(sum(values) / len(values) if values else None),
            }
        )
    for old in [
        "Majors de 64 anys en fulls familiars unipersonals [2025]",
        "Naixements registrats al Padró [2024]",
        "INE 2023 demograficos | Porcentaje de hogares unipersonales [distrito]",
        "Encuesta demografica 2024 | Tasa general de fecundidad",
        "Encuesta demografica 2025 | Indice de envejecimiento",
        "Encuesta demografica 2025 | Indice de sobre-envejecimiento",
        "Encuesta demografica 2025 | Indice demografico de dependencia",
        "Proyectos de innovacion social [n]",
    ]:
        audit_rows.append(
            {
                "bloque": "Sociedad y Bienestar / demografia secundaria",
                "decision": old,
                "criterio": "eliminada por duplicidad, antiguedad de fuente, recuento absoluto o menor interpretabilidad",
                "valor": "",
            }
        )
    if audit_rows:
        report_df = pd.read_csv(report_csv, encoding="utf-8", dtype=str) if report_csv.exists() else pd.DataFrame()
        audit_df = pd.DataFrame(audit_rows)
        if not report_df.empty:
            for column in report_df.columns:
                if column not in audit_df.columns:
                    audit_df[column] = ""
            for column in audit_df.columns:
                if column not in report_df.columns:
                    report_df[column] = ""
            report_df = pd.concat([report_df, audit_df[report_df.columns]], ignore_index=True)
        else:
            report_df = audit_df
        report_df.to_csv(report_csv, index=False, encoding="utf-8")

    return reduced_df



# -----------------------------------------------------------------------------
# Medio ambiente secundario v18
# -----------------------------------------------------------------------------

MEDIO_AMBIENTE_SECUNDARIO_V18_DROP_COLS = [
    "Zonas de juegos infantiles [n]",
    "Zonas de juegos infantiles [por_km2]",
    "Zonas de juegos infantiles [por_1000_hab]",
    "Fuentes [n]",
    "Fuentes agua filtrada y refrigerada [n]",
    "Zonas acÃºsticamente saturadas [n]",
    "Fuentes [por_km2]",
    "Fuentes [por_1000_hab]",
    "Fuentes agua filtrada y refrigerada [por_km2]",
    "Fuentes agua filtrada y refrigerada [por_1000_hab]",
    "Zonas acusticamente saturadas [por_km2]",
    "Zonas acusticamente saturadas [por_1000_hab]",
    "Medio ambiente 2024 | Juegos infantiles zonas [n]",
    "Medio ambiente 2024 | Juegos infantiles elementos [n]",
    "Medio ambiente 2024 | Juegos infantiles superficie [m2]",
    "Medio ambiente 2024 | Escombros contenedores total [n]",
    "Medio ambiente 2024 | Escombros contenedores enero [n]",
    "Medio ambiente 2024 | Escombros contenedores febrero [n]",
    "Medio ambiente 2024 | Escombros contenedores marzo [n]",
    "Medio ambiente 2024 | Escombros contenedores abril [n]",
    "Medio ambiente 2024 | Escombros contenedores mayo [n]",
    "Medio ambiente 2024 | Escombros contenedores junio [n]",
    "Medio ambiente 2024 | Escombros contenedores julio [n]",
    "Medio ambiente 2024 | Escombros contenedores agosto [n]",
    "Medio ambiente 2024 | Escombros contenedores septiembre [n]",
    "Medio ambiente 2024 | Escombros contenedores octubre [n]",
    "Medio ambiente 2024 | Escombros contenedores noviembre [n]",
    "Medio ambiente 2024 | Escombros contenedores diciembre [n]",
]

MEDIO_AMBIENTE_SECUNDARIO_V18_NEW_COLS = [
    "Medio ambiente - Juegos infantiles superficie [m2_por_km2]",
    "Medio ambiente - Fuentes [por_km2]",
    "Medio ambiente - Fuentes agua filtrada y refrigerada [por_km2]",
    "Medio ambiente - Zonas acusticamente saturadas [por_km2]",
    "Medio ambiente - Contenedores escombros [por_1000_hab]",
]


def reduce_medio_ambiente_secundario_v18(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Reduce juegos infantiles, fuentes, zonas acústicas y contenedores de escombros.

    Criterio:
    - Juegos infantiles, fuentes y zonas acústicas se expresan por km2, porque son
      equipamientos o impactos de proximidad espacial.
    - Escombros se expresa por 1.000 habitantes, porque aproxima intensidad de
      demanda/servicio respecto a la población.
    - Se eliminan recuentos absolutos y los meses de escombros, manteniendo el total anual normalizado.
    """
    missing = [col for col in MEDIO_AMBIENTE_SECUNDARIO_V18_DROP_COLS if col not in output_df.columns]
    if missing:
        raise KeyError(f"Faltan columnas de medio ambiente secundario para depurar: {missing}")

    first_idx = min(output_df.columns.get_loc(col) for col in MEDIO_AMBIENTE_SECUNDARIO_V18_DROP_COLS)
    drop_set = set(MEDIO_AMBIENTE_SECUNDARIO_V18_DROP_COLS)
    final_columns: list[str] = []
    inserted = False
    for idx, column in enumerate(output_df.columns):
        if idx == first_idx and not inserted:
            final_columns.extend(MEDIO_AMBIENTE_SECUNDARIO_V18_NEW_COLS)
            inserted = True
        if column in drop_set:
            continue
        final_columns.append(column)

    def per_km2(value: float | None, surface_ha: float | None) -> float | None:
        if value is None or surface_ha in (None, 0):
            return None
        return value / (surface_ha / 100.0)

    reduced_df = output_df.copy()

    for idx, row in reduced_df.iterrows():
        category_row = str(row.get("codigo", "")) == "__categoria__"
        if category_row:
            for column in MEDIO_AMBIENTE_SECUNDARIO_V18_NEW_COLS:
                reduced_df.at[idx, column] = "Medio Ambiente"
            continue

        surface_ha = parse_es_number(row.get("Padron 2025 | Superficie [ha]"))
        population = parse_es_number(row.get("Padron 2025 | Poblacion"))

        reduced_df.at[idx, "Medio ambiente - Juegos infantiles superficie [m2_por_km2]"] = format_es_number(
            per_km2(parse_es_number(row.get("Medio ambiente 2024 | Juegos infantiles superficie [m2]")), surface_ha)
        )
        reduced_df.at[idx, "Medio ambiente - Fuentes [por_km2]"] = format_es_number(
            parse_es_number(row.get("Fuentes [por_km2]"))
        )
        reduced_df.at[idx, "Medio ambiente - Fuentes agua filtrada y refrigerada [por_km2]"] = format_es_number(
            parse_es_number(row.get("Fuentes agua filtrada y refrigerada [por_km2]"))
        )
        reduced_df.at[idx, "Medio ambiente - Zonas acusticamente saturadas [por_km2]"] = format_es_number(
            parse_es_number(row.get("Zonas acusticamente saturadas [por_km2]"))
        )
        reduced_df.at[idx, "Medio ambiente - Contenedores escombros [por_1000_hab]"] = format_es_number(
            rate_per_1000(parse_es_number(row.get("Medio ambiente 2024 | Escombros contenedores total [n]")), population)
        )

    def corr_and_n(c1: str, c2: str) -> tuple[float | None, int]:
        x = reduced_df.loc[reduced_df["codigo"].astype(str) != "__categoria__", c1].apply(parse_es_number)
        y = reduced_df.loc[reduced_df["codigo"].astype(str) != "__categoria__", c2].apply(parse_es_number)
        valid = x.notna() & y.notna()
        if valid.sum() < 2:
            return None, int(valid.sum())
        return float(x[valid].corr(y[valid])), int(valid.sum())

    report_cols = [
        "bloque",
        "tipo_medida",
        "variable_1",
        "variable_2",
        "valor",
        "n_observaciones",
        "decision_metodologica",
        "decision",
        "criterio",
    ]
    report_df = pd.read_csv(report_csv, dtype=str, encoding="utf-8") if report_csv.exists() else pd.DataFrame(columns=report_cols)

    audit_rows: list[dict[str, str]] = []
    pairs = [
        (
            "Zonas de juegos infantiles [n]",
            "Medio ambiente 2024 | Juegos infantiles zonas [n]",
            "Las dos fuentes miden zonas infantiles, pero no coinciden exactamente; se prioriza la fuente 2024 y se usa su superficie normalizada por km2.",
        ),
        (
            "Medio ambiente 2024 | Juegos infantiles zonas [n]",
            "Medio ambiente 2024 | Juegos infantiles elementos [n]",
            "Zonas y elementos estan muy correlacionados; se evita duplicidad manteniendo superficie de zonas infantiles por km2.",
        ),
        (
            "Medio ambiente 2024 | Juegos infantiles zonas [n]",
            "Medio ambiente 2024 | Juegos infantiles superficie [m2]",
            "La superficie aporta una dimension fisica mas interpretable que el recuento de zonas.",
        ),
    ]
    for c1, c2, decision in pairs:
        value, n_obs = corr_and_n(c1, c2)
        audit_rows.append({
            "bloque": "Medio Ambiente / equipamientos secundarios",
            "tipo_medida": "correlacion_pearson",
            "variable_1": c1,
            "variable_2": c2,
            "valor": format_es_number(value),
            "n_observaciones": str(n_obs),
            "decision_metodologica": decision,
            "decision": "",
            "criterio": "",
        })

    for column in MEDIO_AMBIENTE_SECUNDARIO_V18_DROP_COLS:
        audit_rows.append({
            "bloque": "Medio Ambiente / equipamientos secundarios",
            "tipo_medida": "",
            "variable_1": "",
            "variable_2": "",
            "valor": "",
            "n_observaciones": "",
            "decision_metodologica": "",
            "decision": column,
            "criterio": "eliminada por redundancia, recuento absoluto, mensualidad excesiva o unidad menos interpretable",
        })

    pd.concat([report_df, pd.DataFrame(audit_rows, columns=report_cols)], ignore_index=True).to_csv(
        report_csv, index=False, encoding="utf-8"
    )

    return reduced_df.loc[:, final_columns]




def reduce_movilidad_transporte_v19(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Integra Movilidad y Transporte y reduce el bloque de transporte.

    Criterio:
    - Se eliminan vehículos totales por solapamiento con turismos ya normalizados.
    - Se conserva la velocidad máxima media como rasgo de estructura viaria.
    - Ocupación de vía pública se conserva por km2, por su lógica territorial.
    - ValenBisi se conserva en anclajes por km2 y por 1000 hab, porque miden
      cobertura espacial y oferta relativa para la población.
    """
    category_row = output_df["codigo"].astype(str) == "__categoria__"
    original_output_df = output_df.copy()

    transport_drop_cols = [
        "Distribució percentual del nombre de vehicles [2025]",
        "Nombre de vehicles [2025]",
        "Velocidad maxima calles [media km_h]",
        "Ocupacion via publica - incidencias [n]",
        "Ocupacion via publica - duracion media [dias]",
        "Ocupacion via publica - acera [n]",
        "Ocupacion via publica - estacionamiento [n]",
        "Ocupacion via publica - calzada [n]",
        "Ocupacion via publica - peatonal [n]",
        "Ocupacion via publica - incidencias [por_km2]",
        "Ocupacion via publica - incidencias [por_1000_hab]",
        "Ocupacion via publica - acera [por_km2]",
        "Ocupacion via publica - acera [por_1000_hab]",
        "Ocupacion via publica - estacionamiento [por_km2]",
        "Ocupacion via publica - estacionamiento [por_1000_hab]",
        "Ocupacion via publica - calzada [por_km2]",
        "Ocupacion via publica - calzada [por_1000_hab]",
        "Ocupacion via publica - peatonal [por_km2]",
        "Ocupacion via publica - peatonal [por_1000_hab]",
        "ValenBisi - estaciones [n]",
        "ValenBisi - anclajes totales [n]",
        "ValenBisi - bicis disponibles [media]",
        "ValenBisi - anclajes libres [media]",
        "ValenBisi - estaciones [por_km2]",
        "ValenBisi - estaciones [por_1000_hab]",
        "ValenBisi - anclajes totales [por_km2]",
        "ValenBisi - anclajes totales [por_1000_hab]",
    ]

    new_cols = [
        "Movilidad y transporte - Velocidad maxima media calles [km_h]",
        "Movilidad y transporte - Ocupacion via publica incidencias [por_km2]",
        "Movilidad y transporte - Ocupacion via publica duracion media [dias]",
        "Movilidad y transporte - Ocupacion via publica acera [por_km2]",
        "Movilidad y transporte - Ocupacion via publica estacionamiento [por_km2]",
        "Movilidad y transporte - Ocupacion via publica calzada [por_km2]",
        "Movilidad y transporte - Ocupacion via publica peatonal [por_km2]",
        "Movilidad y transporte - ValenBisi anclajes [por_km2]",
        "Movilidad y transporte - ValenBisi anclajes [por_1000_hab]",
    ]

    source_to_new = {
        "Velocidad maxima calles [media km_h]": new_cols[0],
        "Ocupacion via publica - incidencias [por_km2]": new_cols[1],
        "Ocupacion via publica - duracion media [dias]": new_cols[2],
        "Ocupacion via publica - acera [por_km2]": new_cols[3],
        "Ocupacion via publica - estacionamiento [por_km2]": new_cols[4],
        "Ocupacion via publica - calzada [por_km2]": new_cols[5],
        "Ocupacion via publica - peatonal [por_km2]": new_cols[6],
        "ValenBisi - anclajes totales [por_km2]": new_cols[7],
        "ValenBisi - anclajes totales [por_1000_hab]": new_cols[8],
    }

    for source_col, new_col in source_to_new.items():
        if source_col in output_df.columns:
            output_df[new_col] = output_df[source_col]
            output_df.loc[category_row, new_col] = "Movilidad y transporte"

    # Renombrar las variables de movilidad ya depuradas para que el bloque quede integrado.
    rename_movilidad_cols = {
        "Movilidad - Paradas EMT [por_km2]": "Movilidad y transporte - Paradas EMT [por_km2]",
        "Movilidad - Turismos [por_1000_hab]": "Movilidad y transporte - Turismos [por_1000_hab]",
        "Movilidad - Edad media turismos particulares [anos]": "Movilidad y transporte - Edad media turismos particulares [anos]",
        "Movilidad - Superficie aparcamiento por vivienda [m2_vivienda]": "Movilidad y transporte - Superficie aparcamiento por vivienda [m2_vivienda]",
        "Movilidad - Superficie aparcamiento por turismo [m2_turismo]": "Movilidad y transporte - Superficie aparcamiento por turismo [m2_turismo]",
        "Movilidad - Aparcamiento publico o de rotacion [por_1000_hab]": "Movilidad y transporte - Aparcamiento publico o de rotacion [por_1000_hab]",
        "Movilidad - Aparcamiento asociado a vados [por_1000_hab]": "Movilidad y transporte - Aparcamiento asociado a vados [por_1000_hab]",
        "Movilidad - Itinerarios ciclistas [m_por_km2]": "Movilidad y transporte - Itinerarios ciclistas [m_por_km2]",
        "Movilidad - Intensidad media de trafico IMV [actual]": "Movilidad y transporte - Intensidad media de trafico IMV [actual]",
    }
    output_df = output_df.rename(columns={k: v for k, v in rename_movilidad_cols.items() if k in output_df.columns})

    # Cambiar la categoría solo de las columnas de movilidad/transporte, no de seguridad, policía, bomberos o hechos discriminatorios.
    for col in output_df.columns:
        if col.startswith("Movilidad y transporte -"):
            output_df.loc[category_row, col] = "Movilidad y transporte"

    # Insertar las nuevas columnas en la posición donde estaba el primer bloque de transporte.
    existing_cols = list(output_df.columns)
    first_transport_idx = min(
        [existing_cols.index(col) for col in transport_drop_cols if col in existing_cols],
        default=len(existing_cols),
    )

    # Quitar columnas originales de transporte.
    output_df = output_df.drop(columns=[col for col in transport_drop_cols if col in output_df.columns])

    # Reordenar para colocar el bloque nuevo donde estaba transporte.
    cols_after_drop = list(output_df.columns)
    cols_without_new = [col for col in cols_after_drop if col not in new_cols]
    first_transport_idx = min(first_transport_idx, len(cols_without_new))
    reordered_cols = cols_without_new[:first_transport_idx] + new_cols + cols_without_new[first_transport_idx:]
    output_df = output_df[reordered_cols]

    # Añadir filas de auditoria al reporte.
    report_cols = [
        "bloque", "tipo_medida", "variable_1", "variable_2", "valor",
        "n_observaciones", "decision_metodologica", "decision", "criterio",
    ]
    report_df = pd.read_csv(report_csv, dtype=str, encoding="utf-8") if report_csv.exists() else pd.DataFrame(columns=report_cols)

    def corr_pair(col1: str, col2: str) -> tuple[str, int]:
        if col1 not in original_output_df.columns or col2 not in original_output_df.columns:
            return "", 0
        mask = original_output_df["codigo"].astype(str) != "__categoria__"
        x = original_output_df.loc[mask, col1].apply(parse_es_number)
        y = original_output_df.loc[mask, col2].apply(parse_es_number)
        valid = x.notna() & y.notna()
        if valid.sum() < 3:
            return "", int(valid.sum())
        return format_es_number(float(x[valid].corr(y[valid]))), int(valid.sum())

    audit_pairs = [
        (
            "Transporte",
            "correlacion_pearson",
            "Distribució percentual del nombre de vehicles [2025]",
            "Nombre de vehicles [2025]",
            "Se eliminan vehiculos totales por solapamiento con turismos ya normalizados en movilidad.",
        ),
        (
            "Transporte - ValenBisi",
            "correlacion_pearson",
            "ValenBisi - estaciones [por_km2]",
            "ValenBisi - anclajes totales [por_km2]",
            "Se conservan anclajes en lugar de estaciones porque miden mejor la capacidad de la red.",
        ),
        (
            "Transporte - ValenBisi",
            "correlacion_pearson",
            "ValenBisi - estaciones [por_1000_hab]",
            "ValenBisi - anclajes totales [por_1000_hab]",
            "Se conserva la oferta de anclajes por poblacion y cobertura territorial por km2.",
        ),
    ]

    # Para calcular estas correlaciones necesitamos usar columnas antes de eliminarlas; si ya no están,
    # se calcula sobre una copia temporal conservada en variables del output original no disponible.
    # Por eso se registra la decision metodologica aunque el valor quede vacio cuando se ejecute tras el drop.
    rows = []
    for bloque, tipo, col1, col2, decision in audit_pairs:
        valor, n = corr_pair(col1, col2)
        rows.append({
            "bloque": bloque,
            "tipo_medida": tipo,
            "variable_1": col1,
            "variable_2": col2,
            "valor": valor,
            "n_observaciones": str(n),
            "decision_metodologica": decision,
            "decision": "",
            "criterio": "",
        })
    pd.concat([report_df, pd.DataFrame(rows)], ignore_index=True).to_csv(report_csv, index=False, encoding="utf-8")

    return output_df


def reduce_cultura_ocio_v20(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Reduce el bloque Cultura y Ocio.

    Criterio:
    - Zonas de actividades se conserva por km2 porque mide presencia territorial.
    - Clubs federados se transforma a por 1000 hab porque se interpreta como
      disponibilidad/tejido deportivo relativo a la poblacion.
    - Se eliminan recuentos absolutos y duplicados por poblacion/superficie.
    """
    category_row = output_df["codigo"].astype(str) == "__categoria__"
    original_output_df = output_df.copy()

    zonas_original = "Zonas de actividades [por_km2]"
    zonas_new = "Cultura y ocio - Zonas de actividades [por_km2]"
    clubs_original = "Cultura y Ocio 2025 | Clubs federados [n]"
    clubs_new = "Cultura y ocio - Clubs federados [por_1000_hab]"
    population_col = "Padron 2025 | Poblacion"

    old_cols = [
        "Zonas de actividades [n]",
        "Zonas de actividades [por_km2]",
        "Zonas de actividades [por_1000_hab]",
        "Cultura y Ocio 2025 | Clubs federados [n]",
    ]

    existing_cols = list(output_df.columns)
    first_idx = min([existing_cols.index(col) for col in old_cols if col in existing_cols], default=len(existing_cols))

    if zonas_original in output_df.columns:
        output_df[zonas_new] = output_df[zonas_original]
        output_df.loc[category_row, zonas_new] = "Cultura y Ocio"

    if clubs_original in output_df.columns and population_col in output_df.columns:
        values = []
        for _, row in output_df.iterrows():
            if str(row.get("codigo", "")) == "__categoria__":
                values.append("Cultura y Ocio")
                continue
            clubs = parse_es_number(row.get(clubs_original))
            population = parse_es_number(row.get(population_col))
            values.append(format_es_number(rate_per_1000(clubs, population)))
        output_df[clubs_new] = values

    output_df = output_df.drop(columns=[col for col in old_cols if col in output_df.columns])

    new_cols = [col for col in [zonas_new, clubs_new] if col in output_df.columns]
    cols_without_new = [col for col in output_df.columns if col not in new_cols]
    first_idx = min(first_idx, len(cols_without_new))
    output_df = output_df[cols_without_new[:first_idx] + new_cols + cols_without_new[first_idx:]]

    report_cols = [
        "bloque", "tipo_medida", "variable_1", "variable_2", "valor",
        "n_observaciones", "decision_metodologica", "decision", "criterio",
    ]
    report_df = pd.read_csv(report_csv, dtype=str, encoding="utf-8") if report_csv.exists() else pd.DataFrame(columns=report_cols)
    rows = [
        {
            "bloque": "Cultura y Ocio",
            "tipo_medida": "decision_transformacion",
            "variable_1": "Zonas de actividades [por_km2]",
            "variable_2": "Zonas de actividades [n]; Zonas de actividades [por_1000_hab]",
            "valor": "",
            "n_observaciones": "",
            "decision_metodologica": "Se conserva por km2 porque las zonas de actividades se interpretan como dotacion territorial.",
            "decision": "Conservar por km2 y eliminar recuento absoluto/por poblacion.",
            "criterio": "Cobertura territorial.",
        },
        {
            "bloque": "Cultura y Ocio",
            "tipo_medida": "decision_transformacion",
            "variable_1": "Cultura y Ocio 2025 | Clubs federados [n]",
            "variable_2": "Padron 2025 | Poblacion",
            "valor": "",
            "n_observaciones": "",
            "decision_metodologica": "Los clubs federados se expresan por cada 1.000 habitantes para medir tejido deportivo relativo a la poblacion.",
            "decision": "Crear Clubs federados por 1000 habitantes.",
            "criterio": "Disponibilidad relativa / participacion social.",
        },
    ]
    pd.concat([report_df, pd.DataFrame(rows)], ignore_index=True).to_csv(report_csv, index=False, encoding="utf-8")
    return output_df


def reagrupar_seguridad_convivencia_v22(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Unifica las columnas de seguridad, convivencia y emergencias bajo una categoria tematica unica.

    No elimina columnas; solo cambia la fila __categoria__ para facilitar la lectura de la tabla.
    """
    category_rows = output_df.index[output_df["codigo"] == "__categoria__"]
    if len(category_rows) == 0:
        return output_df
    category_row = category_rows[0]
    security_categories = {"Seguridad", "Movilidad, seguridad y convivencia"}
    for col in output_df.columns:
        if output_df.loc[category_row, col] in security_categories:
            output_df.loc[category_row, col] = "Seguridad y convivencia"

    row = {
        "bloque": "Seguridad y convivencia",
        "tipo_medida": "Reagrupacion tematica",
        "variable_1": "Seguridad",
        "variable_2": "Movilidad, seguridad y convivencia",
        "valor": "",
        "n_observaciones": "",
        "decision_metodologica": "Unificar bajo una categoria comun",
        "decision": "renombrar_categoria",
        "criterio": (
            "Se unifican las columnas previamente categorizadas como Seguridad "
            "y Movilidad, seguridad y convivencia bajo Seguridad y convivencia. "
            "En este paso no se eliminan columnas."
        ),
    }
    if report_csv.exists():
        report_df = pd.read_csv(report_csv, encoding="utf-8", dtype=str)
        report_df = pd.concat([report_df, pd.DataFrame([row])], ignore_index=True)
    else:
        report_df = pd.DataFrame([row])
    report_df.to_csv(report_csv, index=False, encoding="utf-8")
    return output_df


def reduce_seguridad_convivencia_v23(output_df: pd.DataFrame, report_csv: Path) -> pd.DataFrame:
    """Depura las variables de hidrantes y elimina codigos policiales categoricos.

    Conserva hidrantes por km2 como infraestructura territorial de emergencia.
    Elimina barrio/distrito policial por ser variables categoricas administrativas y
    elimina hidrantes en recuento absoluto y por poblacion por redundancia.
    """
    old_hidrantes = "Hidrantes [por_km2]"
    new_hidrantes = "Seguridad y convivencia - Hidrantes [por_km2]"
    rename_map = {old_hidrantes: new_hidrantes}
    output_df = output_df.rename(columns={k: v for k, v in rename_map.items() if k in output_df.columns})

    drop_cols = [
        "Barrio policial",
        "Distrito policial",
        "Hidrantes [n]",
        "Hidrantes [por_1000_hab]",
    ]
    existing_drop_cols = [col for col in drop_cols if col in output_df.columns]
    if existing_drop_cols:
        output_df = output_df.drop(columns=existing_drop_cols)

    category_rows = output_df.index[output_df["codigo"] == "__categoria__"]
    if len(category_rows) > 0 and new_hidrantes in output_df.columns:
        output_df.loc[category_rows[0], new_hidrantes] = "Seguridad y convivencia"

    row = {
        "bloque": "Seguridad y convivencia",
        "tipo_medida": "decision_transformacion",
        "variable_1": "Hidrantes [por_km2]",
        "variable_2": "Barrio policial; Distrito policial; Hidrantes [n]; Hidrantes [por_1000_hab]",
        "valor": "",
        "n_observaciones": "",
        "decision_metodologica": (
            "Se conservan los hidrantes por km2 porque son infraestructura territorial de emergencia. "
            "Se eliminan el recuento absoluto y la tasa por poblacion por redundancia, y se eliminan barrio/distrito policial "
            "por ser variables categoricas administrativas no adecuadas como variables activas de PCA/clustering."
        ),
        "decision": "Conservar hidrantes por km2 y eliminar variables categoricas/duplicadas.",
        "criterio": "Infraestructura territorial y eliminacion de variables no continuas.",
    }
    if report_csv.exists():
        report_df = pd.read_csv(report_csv, encoding="utf-8", dtype=str)
        report_df = pd.concat([report_df, pd.DataFrame([row])], ignore_index=True)
    else:
        report_df = pd.DataFrame([row])
    report_df.to_csv(report_csv, index=False, encoding="utf-8")
    return output_df


def build_tabla_depurada() -> pd.DataFrame:
    input_csv = find_input_csv()
    output_csv = resolve_output_path(OUTPUT_NAME, input_csv)
    report_csv = resolve_output_path(REPORT_NAME, input_csv)
    audit_csv = resolve_output_path(AUDIT_REPORT_NAME, input_csv)

    df = pd.read_csv(input_csv, encoding="utf-8", dtype=str)
    original_columns = df.columns.tolist()
    output_columns = build_output_columns(original_columns)
    columns_by_norm = {normalize_text(col): col for col in df.columns}

    codigo_col = resolve_column(columns_by_norm, "codigo")
    poblacion_col = resolve_column(columns_by_norm, "padron 2025 | poblacion")
    superficie_km2_col = resolve_column(columns_by_norm, "superficie distrito agregada [km2]")
    # Demografía general
    demog_densidad_col = resolve_column(columns_by_norm, "padron 2025 | densidad poblacion [hab/km2]")
    demog_variacion_col = resolve_column(columns_by_norm, "padron 2025 | variacion interanual poblacion [%]")
    demog_edad_media_col = resolve_column(columns_by_norm, "encuesta demografica 2025 | edad media [total]")
    demog_esperanza_col = resolve_column(columns_by_norm, "encuesta demografica 2024 | esperanza de vida al nacimiento [total]")
    demog_indice_estructura_col = resolve_column(columns_by_norm, "encuesta demografica 2025 | indice de estructura de la poblacion activa")
    demog_edad_0_14_col = resolve_column(columns_by_norm, "padron 2025 edad | 0-14 [%]")
    demog_edad_15_64_col = resolve_column(columns_by_norm, "padron 2025 edad | 15-64 [%]")
    demog_edad_65_col = resolve_column(columns_by_norm, "padron 2025 edad | 65+ [%]")
    demog_nac_valencia_col = resolve_column(columns_by_norm, "padron 2025 nacimiento | valencia [%]")
    demog_nac_extranjero_col = resolve_column(columns_by_norm, "padron 2025 nacimiento | extranjero [%]")


    # Movilidad
    paradas_emt_col = resolve_column(columns_by_norm, "paradas emt [n]")
    turismos_col = resolve_column(columns_by_norm, "nombre de turismes [2025]")
    edad_turismos_col = resolve_column(columns_by_norm, "edat mitjana dels turismes particulars [2025]")
    superficie_aparc_hab_col = resolve_column(columns_by_norm, "superficie d'aparcament per habitatge [2025]")
    superficie_aparc_turismo_col = resolve_column(columns_by_norm, "superficie d'aparcament per turisme [2025]")
    trafico_imv_col = resolve_column(columns_by_norm, "trafico tramos - imv media [actual]")
    itinerarios_ciclistas_m_col = resolve_column(columns_by_norm, "itinerarios ciclistas - longitud total [m]")
    aparcamientos_libres_col = resolve_column(columns_by_norm, "aparcamientos libres [n]")
    aparcamientos_ora_col = resolve_column(columns_by_norm, "aparcamientos ora [n]")
    aparcamientos_vados_col = resolve_column(columns_by_norm, "aparcamientos vados [n]")
    aparcamientos_parkings_col = resolve_column(columns_by_norm, "aparcamientos parkings [n]")
    turismos_10_mas_col = resolve_column(columns_by_norm, "percentatge de turismes particulars de 10 i mes anys [2025]")
    turismos_16_cv_col = resolve_column(columns_by_norm, "percentatge de turismes particulars de 16 i mes cv [2025]")

    # Bienestar social: vulnerabilidad, asociaciones, recursos, cheques y pobreza
    vulnerabilidad_equipamientos_col = resolve_column(columns_by_norm, "vulnerabilidad equipamientos [indice]")
    vulnerabilidad_demografia_col = resolve_column(columns_by_norm, "vulnerabilidad demografia [indice]")
    vulnerabilidad_economia_col = resolve_column(columns_by_norm, "vulnerabilidad economia [indice]")
    vulnerabilidad_global_col = resolve_column(columns_by_norm, "vulnerabilidad global [indice]")

    asoc_discapacidad_col = resolve_column(columns_by_norm, "asociaciones ayuda social discapacidad [n]")
    asoc_enfermedad_mental_col = resolve_column(columns_by_norm, "asociaciones ayuda social enfermedad mental [n]")
    asoc_mayores_col = resolve_column(columns_by_norm, "asociaciones ayuda social mayores [n]")
    asoc_sintecho_col = resolve_column(columns_by_norm, "asociaciones ayuda social sintecho [n]")
    asoc_etnicas_col = resolve_column(columns_by_norm, "asociaciones ayuda social etnicas [n]")
    asoc_poblacion_general_col = resolve_column(columns_by_norm, "asociaciones ayuda social poblacion general [n]")
    asoc_adicciones_col = resolve_column(columns_by_norm, "asociaciones ayuda adicciones [n]")
    asoc_otras_participacion_col = resolve_column(columns_by_norm, "bienestar social | asociaciones segun distrito y tipo. 2024 | otras participacion social")
    asoc_profesionales_col = resolve_column(columns_by_norm, "bienestar social | asociaciones segun distrito y tipo. 2024 | profesionales y economicas")
    asoc_culturales_col = resolve_column(columns_by_norm, "bienestar social | asociaciones segun distrito y tipo. 2024 | culturales")
    asoc_deportivas_col = resolve_column(columns_by_norm, "bienestar social | asociaciones segun distrito y tipo. 2024 | deportivas")
    asoc_fiestas_col = resolve_column(columns_by_norm, "bienestar social | asociaciones segun distrito y tipo. 2024 | otras fiestas y recreativas")
    asoc_asistencia_social_col = resolve_column(columns_by_norm, "bienestar social | asociaciones segun distrito y tipo. 2024 | asistencia social")

    recursos_discapacidad_fisica_col = resolve_column(columns_by_norm, "recursos sociales discapacidad fisica [n]")
    recursos_toda_poblacion_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | toda la poblacion")
    recursos_conductas_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | conductas adictivas")
    recursos_familia_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | familia, menores y adopciones")
    recursos_inmigracion_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | inmigracion")
    recursos_enfermedad_mental_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | enfermedad mental")
    recursos_dependencia_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | dependencia")
    recursos_discapacidad_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | discapacidad")
    recursos_mayores_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | mayores")
    recursos_personas_presas_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | personas presas y exreclusas")
    recursos_juventud_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | juventud")
    recursos_sin_techo_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | sin techo")
    recursos_mujeres_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | mujeres")
    recursos_total_col = resolve_column(columns_by_norm, "bienestar social | recursos por distrito y sector de poblacion. 2025 | total")

    cheques_poblacion_0_5_col = resolve_column(columns_by_norm, "bienestar social | distribucion de concesiones de cheques escolares segun cobertura. distritos. curso 202425 | poblacion 0 a 5 anos")
    cheques_concedidos_cobertura_col = resolve_column(columns_by_norm, "bienestar social | distribucion de concesiones de cheques escolares segun cobertura. distritos. curso 202425 | cheques concedidos")
    cheques_pct_col = resolve_column(columns_by_norm, "bienestar social | distribucion de concesiones de cheques escolares segun cobertura. distritos. curso 202425 | %")
    cheques_cobertura_col = resolve_column(columns_by_norm, "bienestar social | distribucion de concesiones de cheques escolares segun cobertura. distritos. curso 202425 | cobertura")
    cheques_solicitantes_col = resolve_column(columns_by_norm, "bienestar social | distribucion de solicitudes de cheques escolares, concesiones y renta familiar media. distritos. curso 202425 | solicitantes")
    cheques_concedidos_solicitudes_col = resolve_column(columns_by_norm, "bienestar social | distribucion de solicitudes de cheques escolares, concesiones y renta familiar media. distritos. curso 202425 | concedidos")
    cheques_renta_col = resolve_column(columns_by_norm, "bienestar social | distribucion de solicitudes de cheques escolares, concesiones y renta familiar media. distritos. curso 202425 | renta familiar media")
    cheques_porcentaje_concedidos_col = resolve_column(columns_by_norm, "bienestar social | distribucion de solicitudes de cheques escolares, concesiones y renta familiar media. distritos. curso 202425 | porcentaje de concedidos")

    pobreza_movil_no_col = resolve_column(columns_by_norm, "pobreza 2025 movil | no [%]")
    pobreza_imprevisto_no_col = resolve_column(columns_by_norm, "pobreza 2025 imprevisto 650 eur | no [%]")
    pobreza_comer_fuera_no_col = resolve_column(columns_by_norm, "pobreza 2025 comer fuera mensual | no [%]")
    pobreza_lavadora_no_col = resolve_column(columns_by_norm, "pobreza 2025 lavadora | no [%]")
    pobreza_infantil_tasa_col = resolve_column(columns_by_norm, "pobreza infantil 2021 | tasa distrito [%]")


    # Educación: alumnado por etapa y PAU
    edu_infantil_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de preescolar educacion infantil por distrito. curso 20242025 | total")
    edu_infantil_publico_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de preescolar educacion infantil por distrito. curso 20242025 | titularidad del centro | publico")
    edu_infantil_extranjero_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de preescolar educacion infantil de nacionalidad extranjera por distrito. curso 202425 | total")
    edu_infantil_unidad_col = resolve_column(columns_by_norm, "educacion | centros y unidades de preescolar educacion infantil segun tipo de centro por distrito. curso 20242025 | alumnado por unidad | total")

    edu_primaria_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de primaria por distrito. curso 20242025 | total")
    edu_primaria_publico_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de primaria por distrito. curso 20242025 | titularidad del centro | publico")
    edu_primaria_extranjero_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de primaria de nacionalidad extranjera por distrito. curso 20242025 | total")
    edu_primaria_unidad_col = resolve_column(columns_by_norm, "educacion | centros y unidades de primaria segun tipo de centro por distrito. curso 20242025 | alumnado por unidad | total")

    edu_eso_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de eso por distrito. curso 20242025 | total")
    edu_eso_publico_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de eso por distrito. curso 20242025 | titularidad del centro | publico")
    edu_eso_extranjero_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de eso de nacionalidad extranjera por distrito. curso 20242025 | total")
    edu_eso_unidad_col = resolve_column(columns_by_norm, "educacion | centros y unidades de eso segun titularidad del centro por distrito. curso 20242025 | alumnado por unidad | total")

    edu_bach_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de bachillerato por distrito. curso 20242025 | total")
    edu_bach_publico_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de bachillerato por distrito. curso 20242025 | titularidad del centro | publico")
    edu_bach_extranjero_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de bachillerato de nacionalidad extranjera por distrito. curso 20242025 | total")
    edu_bach_unidad_col = resolve_column(columns_by_norm, "educacion | centros y unidades de bachillerato segun titularidad del centro por distrito. curso 20242025 | alumnado por unidad | total")

    edu_fpgm_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de ciclos formativos de grado medio por distrito. curso 20242025 | total")
    edu_fpgm_publico_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de ciclos formativos de grado medio por distrito. curso 20242025 | titularidad del centro | publico")
    edu_fpgm_extranjero_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de ciclos formativos de grado medio de nacionalidad extranjera por distrito. curso 20242025 | total")
    edu_fpgm_unidad_col = resolve_column(columns_by_norm, "educacion | centros y unidades de ciclos formativos de grado medio segun titularidad del centro por distrito. curso 20242025 | alumnado por unidad | total")

    edu_fpgs_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de ciclos formativos de grado superior por distrito. curso 20242025 | total")
    edu_fpgs_publico_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de ciclos formativos de grado superior por distrito. curso 20242025 | titularidad del centro | publico")
    edu_fpgs_extranjero_total_col = resolve_column(columns_by_norm, "educacion | caracteristicas generales del alumnado de ciclos formativos de grado superior de nacionalidad extranjera por distrito. curso 20232023 | total")
    edu_fpgs_unidad_col = resolve_column(columns_by_norm, "educacion | centros y unidades de ciclos formativos de grado superior segun titularidad del centro distritos. curso 20242025 | alumnado por unidad | total")

    pau_diferencia_col = resolve_column(columns_by_norm, "educacion | resultados de bachillerato y notas pau por distrito. curso 202425 | diferencia entre media expediente y media pau")
    pau_presentado_col = resolve_column(columns_by_norm, "educacion | resultados de bachillerato y notas pau por distrito. curso 202425 | alumnado presentado")
    pau_matriculado_col = resolve_column(columns_by_norm, "educacion | resultados de bachillerato y notas pau por distrito. curso 202425 | alumnado matriculado")
    pau_media_col = resolve_column(columns_by_norm, "educacion | resultados de bachillerato y notas pau por distrito. curso 202425 | media pau")
    pau_apto_pct_col = resolve_column(columns_by_norm, "educacion | resultados de bachillerato y notas pau por distrito. curso 202425 | porcentaje alumnado apto")
    pau_apto_n_col = resolve_column(columns_by_norm, "educacion | resultados de bachillerato y notas pau por distrito. curso 202425 | alumnado apto")
    pau_expediente_col = resolve_column(columns_by_norm, "educacion | resultados de bachillerato y notas pau por distrito. curso 202425 | media expediente de bachillerato")

    edu_padron_bach_fp2_pct_col = resolve_column(columns_by_norm, "padron 2025 titulacion 18+ | bachiller fp2 o superior [%]")
    edu_censo_superior_pct_col = resolve_column(columns_by_norm, "educacion superior [% distrito, mayores 15, censo 2022]")

    # Medio ambiente
    zonas_verdes_superficie_col = resolve_column(columns_by_norm, "superficie zonas verdes [m2]")
    arbolado_col = resolve_column(columns_by_norm, "arbolado [n]")
    ruido_lden_media_col = resolve_column(columns_by_norm, "ruido lden [media]")
    contaminacion_no2_col = resolve_column(columns_by_norm, "contaminacion - no2(�g/m�) [media]")
    contaminacion_pm10_col = resolve_column(columns_by_norm, "contaminacion - pm10(�g/m�) [media]")
    contaminacion_pm25_col = resolve_column(columns_by_norm, "contaminacion - pm2.5(�g/m�) [media]")
    contaminacion_ozono_col = resolve_column(columns_by_norm, "contaminacion - ozono(�g/m�) [media]")
    contaminacion_no_col = resolve_column(columns_by_norm, "contaminacion - no(�g/m�) [media]")
    contaminacion_nox_col = resolve_column(columns_by_norm, "contaminacion - nox(�g/m�) [media]")
    contaminacion_so2_col = resolve_column(columns_by_norm, "contaminacion - so2(�g/m�) [media]")

    # Extranjería
    total_extr_col = resolve_column(columns_by_norm, "padron 2025 extranjera | total [n]")
    edad_extranjera_col = resolve_column(columns_by_norm, "edat mitjana de la poblacio estrangera [2025]")
    ue27_col = resolve_column(columns_by_norm, "padron 2025 extranjera | ue27 [n]")
    resto_europa_col = resolve_column(columns_by_norm, "padron 2025 extranjera | resto europa [n]")
    africa_col = resolve_column(columns_by_norm, "padron 2025 extranjera | africa [n]")
    america_norte_col = resolve_column(columns_by_norm, "padron 2025 extranjera | america norte [n]")
    america_central_col = resolve_column(columns_by_norm, "padron 2025 extranjera | america central [n]")
    america_sur_col = resolve_column(columns_by_norm, "padron 2025 extranjera | america sur [n]")
    asia_col = resolve_column(columns_by_norm, "padron 2025 extranjera | asia [n]")
    otros_col = resolve_column(columns_by_norm, "padron 2025 extranjera | otros [n]")

    # Hechos discriminatorios
    hechos_total_col = resolve_column(columns_by_norm, "hechos discriminatorios [n]")
    racismo_col = resolve_column(columns_by_norm, "hechos discriminatorios - racismo [n]")
    romafobia_col = resolve_column(columns_by_norm, "hechos discriminatorios - romafobia [n]")
    antisemitismo_col = resolve_column(columns_by_norm, "hechos discriminatorios - antisemitismo [n]")
    lengua_cultura_col = resolve_column(columns_by_norm, "hechos discriminatorios - lengua y cultura [n]")
    religion_col = resolve_column(columns_by_norm, "hechos discriminatorios - religion [n]")
    islamofobia_col = resolve_column(columns_by_norm, "hechos discriminatorios - islamofobia [n]")
    disfobia_col = resolve_column(columns_by_norm, "hechos discriminatorios - disfobia [n]")
    malalties_col = resolve_column(columns_by_norm, "hechos discriminatorios - malalties rares i fisics no normatius [n]")
    genero_col = resolve_column(columns_by_norm, "hechos discriminatorios - genero [n]")
    lgtbi_col = resolve_column(columns_by_norm, "hechos discriminatorios - lgtbifobia [n]")
    aporofobia_col = resolve_column(columns_by_norm, "hechos discriminatorios - aporofobia [n]")
    ideologia_col = resolve_column(columns_by_norm, "hechos discriminatorios - ideologia [n]")
    interseccional_col = resolve_column(columns_by_norm, "hechos discriminatorios - interseccional [n]")
    edadismo_col = resolve_column(columns_by_norm, "hechos discriminatorios - edadismo [n]")

    # Policía local
    trafico_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | servicios trafico [n]")
    seguridad_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | seguridad ciudadana [n]")
    vigilancias_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | vigilancias [n]")
    administrativa_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | policia administrativa [n]")
    actos_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | actos via publica [n]")
    informacion_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | informacion [n]")
    incidencias_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | incidencias [n]")
    humanitarios_col = resolve_column(columns_by_norm, "recursos municipales 2024 policia local | humanitarios y riesgos [n]")

    # Bomberos
    salvamentos_col = resolve_column(columns_by_norm, "recursos municipales 2024 bomberos | salvamentos [n]")
    asistencia_col = resolve_column(columns_by_norm, "recursos municipales 2024 bomberos | asistencia tecnica [n]")
    incendios_col = resolve_column(columns_by_norm, "recursos municipales 2024 bomberos | incendios [n]")
    falsas_alarmas_col = resolve_column(columns_by_norm, "recursos municipales 2024 bomberos | falsas alarmas [n]")
    mercancias_col = resolve_column(columns_by_norm, "recursos municipales 2024 bomberos | mercancias peligrosas [n]")

    # Turismo
    hoteles_plazas_col = resolve_column(columns_by_norm, "economia 2024 | hoteles [plazas]")
    hostales_plazas_col = resolve_column(columns_by_norm, "economia 2024 | hostales y pensiones [plazas]")
    albergues_plazas_col = resolve_column(columns_by_norm, "economia 2024 | albergues urbanos [plazas]")
    viviendas_tur_plazas_col = resolve_column(columns_by_norm, "economia 2024 | viviendas turisticas [plazas]")
    viviendas_tur_pct_col = resolve_column(columns_by_norm, "economia 2024 | viviendas turisticas [% viviendas]")

    # Economia: renta, mercado laboral, empresas, turismo economico y fiscalidad depurada
    economia_renta_persona_col = resolve_column(columns_by_norm, "ine - renta media por persona [eur distrito]")
    economia_mediana_unidad_col = resolve_column(columns_by_norm, "ine - mediana renta por unidad de consumo [eur distrito]")
    economia_renta_hogar_col = resolve_column(columns_by_norm, "ine - renta media por hogar [eur distrito]")
    economia_media_unidad_col = resolve_column(columns_by_norm, "ine - media renta por unidad de consumo [eur distrito]")
    economia_gini_col = resolve_column(columns_by_norm, "ine 2023 desigualdad | indice de gini [distrito]")
    economia_p80p20_col = resolve_column(columns_by_norm, "ine 2023 desigualdad | distribucion de la renta p80/p20 [distrito]")
    economia_ingresos_salario_col = resolve_column(columns_by_norm, "ine - fuente ingresos salario [% distrito]")
    economia_ingresos_pensiones_col = resolve_column(columns_by_norm, "ine - fuente ingresos pensiones [% distrito]")
    economia_ingresos_desempleo_col = resolve_column(columns_by_norm, "ine - fuente ingresos prestaciones desempleo [% distrito]")
    economia_ocupada_col = resolve_column(columns_by_norm, "anuario 2021 actividad | ocupada [% distrito 16+]")
    economia_parada_col = resolve_column(columns_by_norm, "anuario 2021 actividad | parada [% distrito 16+]")
    economia_jubilacion_col = resolve_column(columns_by_norm, "anuario 2021 actividad | jubilacion o prejubilacion [% distrito 16+]")
    economia_cuenta_propia_col = resolve_column(columns_by_norm, "anuario 2021 situacion profesional | cuenta propia [% ocupadas distrito]")
    economia_cuenta_ajena_temporal_col = resolve_column(columns_by_norm, "anuario 2021 situacion profesional | cuenta ajena temporal [% ocupadas distrito]")
    economia_trabaja_mismo_municipio_col = resolve_column(columns_by_norm, "anuario 2021 lugar trabajo | mismo municipio [% ocupadas distrito]")
    economia_actividades_por_1000_col = resolve_column(columns_by_norm, "activitats economiques per 1.000 habitants [2025]")
    economia_terciarizacion_col = resolve_column(columns_by_norm, "grau de terciaritzacio economica [2025]")
    economia_oficinas_bancarias_col = resolve_column(columns_by_norm, "economia 2025 | oficinas bancarias [por_10000_hab]")
    economia_terrazas_n_col = resolve_column(columns_by_norm, "economia 2024 | terrazas hosteleria [n]")
    economia_terrazas_superficie_col = resolve_column(columns_by_norm, "economia 2024 | terrazas hosteleria [superficie_m2]")
    economia_actividades_industriales_col = resolve_column(columns_by_norm, "economia 2025 | actividades industriales [n]")
    economia_coop_territorial_col = resolve_column(columns_by_norm, "economia 2024 | sociedades cooperativas registro territorial [n]")
    economia_coop_central_col = resolve_column(columns_by_norm, "economia 2024 | sociedades cooperativas registro central [n]")
    economia_sociedades_laborales_col = resolve_column(columns_by_norm, "economia 2024 | sociedades laborales [n]")
    economia_empresas_total_col = resolve_column(columns_by_norm, "economia 2024 | empresas activas [n]")
    economia_empresas_persona_juridica_col = resolve_column(columns_by_norm, "economia 2024 | empresas activas persona juridica [n]")
    economia_empresas_industria_col = resolve_column(columns_by_norm, "economia 2024 | empresas activas industria [n]")
    economia_empresas_construccion_col = resolve_column(columns_by_norm, "economia 2024 | empresas activas construccion [n]")
    economia_empresas_servicios_col = resolve_column(columns_by_norm, "economia 2024 | empresas activas servicios [n]")
    ibi_num_total_col = resolve_column(columns_by_norm, "ibi - media num. recibos totales")
    ibi_importe_total_col = resolve_column(columns_by_norm, "ibi - media importe recibos totales")
    iae_num_total_col = resolve_column(columns_by_norm, "iae - media numero recibos totales")
    iae_importe_total_col = resolve_column(columns_by_norm, "iae - media importe recibos totales")
    ivtm_recibos_total_col = resolve_column(columns_by_norm, "ivtm - media recibos totales")
    ivtm_importe_total_col = resolve_column(columns_by_norm, "ivtm - media importe rec, totales")

    # Vivienda: precios y alquiler
    venta_trimestral_precio_cols = [
        resolve_column(columns_by_norm, f"edificacion vivienda 2024 venta trimestral | precio medio venta {quarter} [eur_m2]")
        for quarter in ("t1", "t2", "t3", "t4")
    ]
    venta_trimestral_esfuerzo_cols = [
        resolve_column(columns_by_norm, f"edificacion vivienda 2024 venta trimestral | esfuerzo financiero {quarter} [%]")
        for quarter in ("t1", "t2", "t3", "t4")
    ]
    venta_trimestral_crecimiento_cols = [
        resolve_column(columns_by_norm, f"edificacion vivienda 2024 venta trimestral | crecimiento anual compuesto {quarter} [%]")
        for quarter in ("t1", "t2", "t3", "t4")
    ]
    alquiler_idealista_cols = [
        resolve_column(columns_by_norm, f"edificacion vivienda 2024 alquiler idealista | {month} [eur_m2_mes]")
        for month in ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre")
    ]
    alquiler_total_col = resolve_column(columns_by_norm, "edificacion vivienda 2023 alquiler | viviendas alquiladas total [n]")

    # Vivienda: licencias, rehabilitación, inmuebles por uso, antigüedad y valor catastral
    lic_viviendas_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 licencias construccion | viviendas [n]")
    lic_aparcamientos_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 licencias construccion | aparcamientos [n]")
    lic_industrial_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 licencias construccion | industrial_comercial [n]")
    lic_edificios_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 licencias construccion | edificios [n]")
    lic_viviendas_con_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 licencias construccion | viviendas con licencia [n]")
    lic_garajes_con_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 licencias construccion | garajes con licencia [n]")
    rehab_integral_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 rehabilitacion | integral [n]")
    rehab_parcial_col = resolve_column(columns_by_norm, "edificacion vivienda 2024 rehabilitacion | parcial [n]")

    uso_residencial_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 inmuebles uso | residencial [n]")
    uso_almacen_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 inmuebles uso | almacen_aparcamiento [n]")
    uso_comercial_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 inmuebles uso | comercial [n]")
    uso_oficinas_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 inmuebles uso | oficinas [n]")
    uso_industrial_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 inmuebles uso | industrial [n]")
    uso_resto_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 inmuebles uso | resto [n]")

    pct_menos_5_col = resolve_column(columns_by_norm, "percentatge d'habitatges amb menys de 5 anys [2025]")
    pct_menos_10_col = resolve_column(columns_by_norm, "percentatge d'habitatges amb menys de 10 anys [2025]")
    pct_mas_50_col = resolve_column(columns_by_norm, "percentatge d'habitatges amb mes de 50 anys [2025]")
    antig_total_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | total [n]")
    antig_1800_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | <=1800 [n]")
    antig_1801_1900_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 1801_1900 [n]")
    antig_1901_1920_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 1901_1920 [n]")
    antig_1921_1940_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 1921_1940 [n]")
    antig_1941_1960_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 1941_1960 [n]")
    antig_1961_1980_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 1961_1980 [n]")
    antig_1981_2000_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 1981_2000 [n]")
    antig_2001_2010_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 2001_2010 [n]")
    antig_2011_2024_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 residencial antiguedad | 2011_2024 [n]")

    valor_total_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | total [n]")
    valor_12_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | <=12k [n]")
    valor_12_18_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | 12_18k [n]")
    valor_18_24_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | 18_24k [n]")
    valor_24_30_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | 24_30k [n]")
    valor_30_36_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | 30_36k [n]")
    valor_36_48_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | 36_48k [n]")
    valor_48_60_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | 48_60k [n]")
    valor_60_72_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | 60_72k [n]")
    valor_72_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | >72k [n]")
    valor_no_consta_col = resolve_column(columns_by_norm, "edificacion vivienda 2025 valor catastral tramos | no consta [n]")

    numeric_source_cols = [
        poblacion_col,
        superficie_km2_col,
        demog_densidad_col,
        demog_variacion_col,
        demog_edad_media_col,
        demog_esperanza_col,
        demog_indice_estructura_col,
        demog_edad_0_14_col,
        demog_edad_15_64_col,
        demog_edad_65_col,
        demog_nac_valencia_col,
        demog_nac_extranjero_col,
        paradas_emt_col,
        turismos_col,
        edad_turismos_col,
        superficie_aparc_hab_col,
        superficie_aparc_turismo_col,
        trafico_imv_col,
        itinerarios_ciclistas_m_col,
        aparcamientos_libres_col,
        aparcamientos_ora_col,
        aparcamientos_vados_col,
        aparcamientos_parkings_col,
        turismos_10_mas_col,
        turismos_16_cv_col,
        vulnerabilidad_equipamientos_col,
        vulnerabilidad_demografia_col,
        vulnerabilidad_economia_col,
        vulnerabilidad_global_col,
        asoc_discapacidad_col,
        asoc_enfermedad_mental_col,
        asoc_mayores_col,
        asoc_sintecho_col,
        asoc_etnicas_col,
        asoc_poblacion_general_col,
        asoc_adicciones_col,
        asoc_otras_participacion_col,
        asoc_profesionales_col,
        asoc_culturales_col,
        asoc_deportivas_col,
        asoc_fiestas_col,
        asoc_asistencia_social_col,
        recursos_discapacidad_fisica_col,
        recursos_toda_poblacion_col,
        recursos_conductas_col,
        recursos_familia_col,
        recursos_inmigracion_col,
        recursos_enfermedad_mental_col,
        recursos_dependencia_col,
        recursos_discapacidad_col,
        recursos_mayores_col,
        recursos_personas_presas_col,
        recursos_juventud_col,
        recursos_sin_techo_col,
        recursos_mujeres_col,
        recursos_total_col,
        cheques_poblacion_0_5_col,
        cheques_concedidos_cobertura_col,
        cheques_pct_col,
        cheques_cobertura_col,
        cheques_solicitantes_col,
        cheques_concedidos_solicitudes_col,
        cheques_renta_col,
        cheques_porcentaje_concedidos_col,
        pobreza_movil_no_col,
        pobreza_imprevisto_no_col,
        pobreza_comer_fuera_no_col,
        pobreza_lavadora_no_col,
        pobreza_infantil_tasa_col,

        edu_infantil_total_col,
        edu_infantil_publico_col,
        edu_infantil_extranjero_total_col,
        edu_infantil_unidad_col,
        edu_primaria_total_col,
        edu_primaria_publico_col,
        edu_primaria_extranjero_total_col,
        edu_primaria_unidad_col,
        edu_eso_total_col,
        edu_eso_publico_col,
        edu_eso_extranjero_total_col,
        edu_eso_unidad_col,
        edu_bach_total_col,
        edu_bach_publico_col,
        edu_bach_extranjero_total_col,
        edu_bach_unidad_col,
        edu_fpgm_total_col,
        edu_fpgm_publico_col,
        edu_fpgm_extranjero_total_col,
        edu_fpgm_unidad_col,
        edu_fpgs_total_col,
        edu_fpgs_publico_col,
        edu_fpgs_extranjero_total_col,
        edu_fpgs_unidad_col,
        pau_diferencia_col,
        pau_presentado_col,
        pau_matriculado_col,
        pau_media_col,
        pau_apto_pct_col,
        pau_apto_n_col,
        pau_expediente_col,
        edu_censo_superior_pct_col,
        zonas_verdes_superficie_col,
        arbolado_col,
        ruido_lden_media_col,
        contaminacion_no2_col,
        contaminacion_pm10_col,
        contaminacion_pm25_col,
        contaminacion_ozono_col,
        contaminacion_no_col,
        contaminacion_nox_col,
        contaminacion_so2_col,
        total_extr_col,
        edad_extranjera_col,
        ue27_col,
        resto_europa_col,
        africa_col,
        america_norte_col,
        america_central_col,
        america_sur_col,
        asia_col,
        otros_col,
        hechos_total_col,
        racismo_col,
        romafobia_col,
        antisemitismo_col,
        lengua_cultura_col,
        religion_col,
        islamofobia_col,
        disfobia_col,
        malalties_col,
        genero_col,
        lgtbi_col,
        aporofobia_col,
        ideologia_col,
        interseccional_col,
        edadismo_col,
        trafico_col,
        seguridad_col,
        vigilancias_col,
        administrativa_col,
        actos_col,
        informacion_col,
        incidencias_col,
        humanitarios_col,
        salvamentos_col,
        asistencia_col,
        incendios_col,
        falsas_alarmas_col,
        mercancias_col,
        hoteles_plazas_col,
        hostales_plazas_col,
        albergues_plazas_col,
        viviendas_tur_plazas_col,
        viviendas_tur_pct_col,
        economia_renta_persona_col,
        economia_mediana_unidad_col,
        economia_renta_hogar_col,
        economia_media_unidad_col,
        economia_gini_col,
        economia_p80p20_col,
        economia_ingresos_salario_col,
        economia_ingresos_pensiones_col,
        economia_ingresos_desempleo_col,
        economia_ocupada_col,
        economia_parada_col,
        economia_jubilacion_col,
        economia_cuenta_propia_col,
        economia_cuenta_ajena_temporal_col,
        economia_trabaja_mismo_municipio_col,
        economia_actividades_por_1000_col,
        economia_terciarizacion_col,
        economia_oficinas_bancarias_col,
        economia_terrazas_n_col,
        economia_terrazas_superficie_col,
        economia_actividades_industriales_col,
        economia_coop_territorial_col,
        economia_coop_central_col,
        economia_sociedades_laborales_col,
        economia_empresas_total_col,
        economia_empresas_persona_juridica_col,
        economia_empresas_industria_col,
        economia_empresas_construccion_col,
        economia_empresas_servicios_col,
        ibi_num_total_col,
        ibi_importe_total_col,
        iae_num_total_col,
        iae_importe_total_col,
        ivtm_recibos_total_col,
        ivtm_importe_total_col,
        *venta_trimestral_precio_cols,
        *venta_trimestral_esfuerzo_cols,
        *venta_trimestral_crecimiento_cols,
        *alquiler_idealista_cols,
        alquiler_total_col,
        lic_viviendas_col,
        lic_aparcamientos_col,
        lic_industrial_col,
        lic_edificios_col,
        lic_viviendas_con_col,
        lic_garajes_con_col,
        rehab_integral_col,
        rehab_parcial_col,
        uso_residencial_col,
        uso_almacen_col,
        uso_comercial_col,
        uso_oficinas_col,
        uso_industrial_col,
        uso_resto_col,
        pct_menos_5_col,
        pct_menos_10_col,
        pct_mas_50_col,
        antig_total_col,
        antig_1800_col,
        antig_1801_1900_col,
        antig_1901_1920_col,
        antig_1921_1940_col,
        antig_1941_1960_col,
        antig_1961_1980_col,
        antig_1981_2000_col,
        antig_2001_2010_col,
        antig_2011_2024_col,
        valor_total_col,
        valor_12_col,
        valor_12_18_col,
        valor_18_24_col,
        valor_24_30_col,
        valor_30_36_col,
        valor_36_48_col,
        valor_48_60_col,
        valor_60_72_col,
        valor_72_col,
        valor_no_consta_col,
    ]
    for col in numeric_source_cols:
        df[col] = df[col].apply(parse_es_number)

    non_category_mask = df[codigo_col].astype(str) != "__categoria__"

    def z_score(value: float | None, mean_value: float, std_value: float) -> float | None:
        if value is None or pd.isna(value) or std_value == 0 or pd.isna(std_value):
            return None
        return (float(value) - mean_value) / std_value

    pm10_mean = df.loc[non_category_mask, contaminacion_pm10_col].mean()
    pm10_std = df.loc[non_category_mask, contaminacion_pm10_col].std(ddof=0)
    pm25_mean = df.loc[non_category_mask, contaminacion_pm25_col].mean()
    pm25_std = df.loc[non_category_mask, contaminacion_pm25_col].std(ddof=0)

    particulas_index_by_row: dict[int, float | None] = {}
    for idx, source_row in df.iterrows():
        z_values = [
            z_score(source_row[contaminacion_pm10_col], pm10_mean, pm10_std),
            z_score(source_row[contaminacion_pm25_col], pm25_mean, pm25_std),
        ]
        valid_z_values = [value for value in z_values if value is not None and not pd.isna(value)]
        particulas_index_by_row[idx] = mean_non_null(valid_z_values)

    # -------------------------------------------------------------------------
    # Auditoria de redundancias y correlaciones
    # -------------------------------------------------------------------------
    # Este bloque no modifica la tabla final. Genera un CSV auxiliar con las
    # correlaciones de Pearson y pesos porcentuales que han ayudado a justificar
    # algunas de las fusiones o eliminaciones de columnas.
    report_rows: list[dict[str, str]] = []

    def fmt_report(value: float | None) -> str:
        if value is None or pd.isna(value):
            return ""
        return f"{float(value):.3f}".replace(".", ",")

    def add_corr(block: str, col_a: str, col_b: str, decision: str) -> None:
        pair_df = df.loc[non_category_mask, [col_a, col_b]].copy()
        pair_df[col_a] = pair_df[col_a].apply(parse_es_number)
        pair_df[col_b] = pair_df[col_b].apply(parse_es_number)
        pair_df = pair_df.dropna()
        corr_value = None if len(pair_df) < 2 else float(pair_df[col_a].corr(pair_df[col_b]))
        report_rows.append(
            {
                "bloque": block,
                "tipo_medida": "correlacion_pearson",
                "variable_1": col_a,
                "variable_2": col_b,
                "valor": fmt_report(corr_value),
                "n_observaciones": str(len(pair_df)),
                "decision_metodologica": decision,
            }
        )

    def add_share(block: str, label: str, value: float, total: float, decision: str) -> None:
        share_value = None if total == 0 else (float(value) / float(total)) * 100.0
        report_rows.append(
            {
                "bloque": block,
                "tipo_medida": "peso_sobre_total_ciudad_%",
                "variable_1": label,
                "variable_2": "total del bloque",
                "valor": fmt_report(share_value),
                "n_observaciones": str(int(non_category_mask.sum())),
                "decision_metodologica": decision,
            }
        )

    add_corr(
        "Hechos discriminatorios",
        genero_col,
        lgtbi_col,
        "Fusionadas como discriminacion por sexo-genero y diversidad sexual.",
    )
    add_corr(
        "Medio ambiente",
        contaminacion_pm10_col,
        contaminacion_pm25_col,
        "PM10 y PM2.5 se integran en un indice estandarizado de particulas.",
    )
    add_corr(
        "Medio ambiente",
        contaminacion_pm10_col,
        contaminacion_ozono_col,
        "Ozono se mantiene separado porque su comportamiento territorial es distinto al de las particulas.",
    )
    add_corr(
        "Medio ambiente",
        contaminacion_pm25_col,
        contaminacion_ozono_col,
        "Ozono se mantiene separado porque no mide material particulado.",
    )
    add_corr(
        "Medio ambiente",
        contaminacion_no_col,
        contaminacion_nox_col,
        "NO, NO2 y NOx son muy redundantes; se conserva NO2 como indicador mas interpretable de trafico urbano.",
    )
    add_corr(
        "Medio ambiente",
        contaminacion_no2_col,
        contaminacion_nox_col,
        "NOx se elimina por redundancia con NO2.",
    )
    add_corr(
        "Medio ambiente",
        contaminacion_no_col,
        contaminacion_no2_col,
        "NO se elimina por redundancia con NO2.",
    )
    add_corr(
        "Medio ambiente",
        contaminacion_so2_col,
        contaminacion_ozono_col,
        "SO2 se elimina; se conserva un conjunto de contaminantes mas interpretable.",
    )
    add_corr(
        "Movilidad",
        edad_turismos_col,
        turismos_10_mas_col,
        "Se conserva la edad media de los turismos y se elimina el porcentaje de turismos de 10 o mas anos.",
    )
    add_corr(
        "Movilidad",
        edad_turismos_col,
        turismos_16_cv_col,
        "Se elimina el porcentaje de turismos de 16 o mas CV para reducir detalle no esencial.",
    )


    add_corr(
        "Bienestar social - vulnerabilidad",
        vulnerabilidad_global_col,
        vulnerabilidad_economia_col,
        "Se conservan ambos indices: el global resume la vulnerabilidad general y economia mantiene una dimension especifica.",
    )
    add_corr(
        "Bienestar social - vulnerabilidad",
        vulnerabilidad_global_col,
        vulnerabilidad_demografia_col,
        "Se conservan los indices porque cada uno representa una dimension distinta de vulnerabilidad.",
    )
    add_corr(
        "Bienestar social - cheques escolares",
        cheques_concedidos_cobertura_col,
        cheques_concedidos_solicitudes_col,
        "Los concedidos aparecen duplicados en dos tablas fuente; se conserva la cobertura y el porcentaje concedido sobre solicitudes.",
    )
    add_corr(
        "Bienestar social - cheques escolares",
        cheques_cobertura_col,
        cheques_porcentaje_concedidos_col,
        "Cobertura y porcentaje concedido sobre solicitudes miden aspectos relacionados pero no identicos, por eso se mantienen separadas.",
    )
    add_corr(
        "Pobreza",
        pobreza_movil_no_col,
        pobreza_lavadora_no_col,
        "Se conservan ambas carencias seleccionadas por su interpretacion material directa.",
    )


    add_corr(
        "Educacion - titulacion",
        edu_padron_bach_fp2_pct_col,
        edu_censo_superior_pct_col,
        "Se conserva Padron 2025 en porcentajes y se eliminan indicadores de censo 2022 por solapamiento temporal y conceptual.",
    )
    add_corr(
        "Educacion - PAU",
        pau_matriculado_col,
        pau_presentado_col,
        "No se conserva el recuento absoluto de presentados; se transforma en porcentaje sobre alumnado matriculado.",
    )
    add_corr(
        "Educacion - PAU",
        pau_expediente_col,
        pau_media_col,
        "Se conserva la media PAU y la diferencia expediente-PAU como medida complementaria de brecha entre evaluacion interna y externa.",
    )
    add_corr(
        "Educacion - PAU",
        pau_presentado_col,
        pau_apto_n_col,
        "El porcentaje de aptos resume el resultado academico evitando conservar recuentos absolutos.",
    )

    asociaciones_total_reducido = sum(
        safe_num(df.loc[non_category_mask, col].sum())
        for col in [
            asoc_discapacidad_col,
            asoc_enfermedad_mental_col,
            asoc_adicciones_col,
            asoc_mayores_col,
            asoc_sintecho_col,
            asoc_etnicas_col,
            asoc_poblacion_general_col,
            asoc_otras_participacion_col,
            asoc_culturales_col,
            asoc_deportivas_col,
            asoc_fiestas_col,
            asoc_profesionales_col,
        ]
    )
    for label, value in [
        ("Discapacidad + enfermedad mental", df.loc[non_category_mask, asoc_discapacidad_col].sum() + df.loc[non_category_mask, asoc_enfermedad_mental_col].sum()),
        ("Adicciones", df.loc[non_category_mask, asoc_adicciones_col].sum()),
        ("Mayores", df.loc[non_category_mask, asoc_mayores_col].sum()),
        ("Sintecho", df.loc[non_category_mask, asoc_sintecho_col].sum()),
        ("Etnicas", df.loc[non_category_mask, asoc_etnicas_col].sum()),
        ("Poblacion general + otras participacion social", df.loc[non_category_mask, asoc_poblacion_general_col].sum() + df.loc[non_category_mask, asoc_otras_participacion_col].sum()),
        ("Culturales + deportivas + fiestas/recreativas", df.loc[non_category_mask, asoc_culturales_col].sum() + df.loc[non_category_mask, asoc_deportivas_col].sum() + df.loc[non_category_mask, asoc_fiestas_col].sum()),
        ("Profesionales y economicas", df.loc[non_category_mask, asoc_profesionales_col].sum()),
    ]:
        add_share("Bienestar social - asociaciones", label, safe_num(value), asociaciones_total_reducido, "Reduccion del tejido asociativo a dimensiones interpretables por cada 1.000 habitantes.")

    policia_total = sum(safe_num(df.loc[non_category_mask, col].sum()) for col in [trafico_col, seguridad_col, vigilancias_col, administrativa_col, actos_col, informacion_col, incidencias_col, humanitarios_col])
    for label, value in [
        ("Servicios trafico", df.loc[non_category_mask, trafico_col].sum()),
        ("Seguridad ciudadana", df.loc[non_category_mask, seguridad_col].sum()),
        ("Vigilancias", df.loc[non_category_mask, vigilancias_col].sum()),
        ("Policia administrativa", df.loc[non_category_mask, administrativa_col].sum()),
        ("Actos via publica", df.loc[non_category_mask, actos_col].sum()),
        ("Informacion", df.loc[non_category_mask, informacion_col].sum()),
        ("Incidencias", df.loc[non_category_mask, incidencias_col].sum()),
        ("Humanitarios y riesgos", df.loc[non_category_mask, humanitarios_col].sum()),
    ]:
        add_share("Policia local", label, safe_num(value), policia_total, "Agrupacion de subtipos en cuatro bloques funcionales por cada 1.000 habitantes.")

    bomberos_total = sum(safe_num(df.loc[non_category_mask, col].sum()) for col in [salvamentos_col, asistencia_col, incendios_col, falsas_alarmas_col, mercancias_col])
    for label, value in [
        ("Salvamentos", df.loc[non_category_mask, salvamentos_col].sum()),
        ("Asistencia tecnica", df.loc[non_category_mask, asistencia_col].sum()),
        ("Incendios", df.loc[non_category_mask, incendios_col].sum()),
        ("Falsas alarmas", df.loc[non_category_mask, falsas_alarmas_col].sum()),
        ("Mercancias peligrosas", df.loc[non_category_mask, mercancias_col].sum()),
    ]:
        add_share("Bomberos", label, safe_num(value), bomberos_total, "Agrupacion en rescate/asistencia e incendios/alertas de riesgo.")

    aparcamientos_total = sum(safe_num(df.loc[non_category_mask, col].sum()) for col in [aparcamientos_libres_col, aparcamientos_ora_col, aparcamientos_vados_col, aparcamientos_parkings_col])
    for label, value in [
        ("Aparcamientos libres", df.loc[non_category_mask, aparcamientos_libres_col].sum()),
        ("Aparcamientos ORA", df.loc[non_category_mask, aparcamientos_ora_col].sum()),
        ("Aparcamientos vados", df.loc[non_category_mask, aparcamientos_vados_col].sum()),
        ("Aparcamientos parkings", df.loc[non_category_mask, aparcamientos_parkings_col].sum()),
    ]:
        add_share("Movilidad - aparcamientos", label, safe_num(value), aparcamientos_total, "Fusion de libres, ORA y parkings como aparcamiento publico/de rotacion; vados queda separado.")

    add_corr(
        "Economia",
        economia_renta_persona_col,
        economia_renta_hogar_col,
        "Rentas por persona y por hogar presentan solapamiento; se conserva renta por persona como indicador principal.",
    )
    add_corr(
        "Economia",
        economia_renta_persona_col,
        economia_media_unidad_col,
        "Las distintas medidas medias de renta son muy próximas; se conserva renta por persona y mediana por unidad de consumo.",
    )
    add_corr(
        "Economia",
        economia_gini_col,
        economia_p80p20_col,
        "Gini y P80/P20 miden desigualdad; se conserva Gini como indicador sintetico.",
    )
    add_corr(
        "Economia",
        ibi_num_total_col,
        ibi_importe_total_col,
        "IBI se elimina del bloque final por su caracter fiscal-administrativo y su solapamiento con valor catastral/renta.",
    )
    add_corr(
        "Economia",
        iae_num_total_col,
        iae_importe_total_col,
        "IAE se elimina del bloque final porque la actividad economica queda resumida por empresas y actividades por habitante.",
    )
    add_corr(
        "Economia",
        ivtm_recibos_total_col,
        ivtm_importe_total_col,
        "IVTM se elimina del bloque final porque duplica informacion fiscal ligada al parque de vehiculos ya tratado en movilidad.",
    )

    add_corr(
        "Consumo publico",
        "Renta consumo precios 2024 alumbrado publico | Consumo electrico [kWh]",
        "Renta consumo precios 2024 alumbrado publico | Facturacion [EUR]",
        "Se conserva consumo electrico normalizado por km2 y se elimina facturacion absoluta.",
    )
    add_corr(
        "Consumo publico",
        "Renta consumo precios 2024 pasos inferiores | Puntos alumbrado total [n]",
        "Renta consumo precios 2024 pasos inferiores | Potencia instalada total [kW]",
        "Se conserva potencia instalada total por km2 y se eliminan puntos y tecnologias desagregadas.",
    )
    add_corr(
        "Consumo publico",
        "Renta consumo precios 2024 monumentos | Puntos alumbrado total [n]",
        "Renta consumo precios 2024 monumentos | Potencia instalada total [kW]",
        "Se conserva potencia instalada total por km2 y se eliminan puntos y tecnologias desagregadas.",
    )

    pd.DataFrame(report_rows).to_csv(report_csv, index=False, encoding="utf-8")

    out_rows: list[dict[str, str]] = []

    for _, row in df.iterrows():
        out_row: dict[str, str] = {}
        category_row = str(row[codigo_col]) == "__categoria__"
        population = row[poblacion_col]
        area_km2 = row[superficie_km2_col]
        total_extr = row[total_extr_col]

        etnico_racial = sum(safe_num(row[col]) for col in [racismo_col, romafobia_col, antisemitismo_col, lengua_cultura_col])
        intolerancia_religiosa = sum(safe_num(row[col]) for col in [religion_col, islamofobia_col])
        capacitismo = sum(safe_num(row[col]) for col in [disfobia_col, malalties_col])
        sexo_genero_div = sum(safe_num(row[col]) for col in [genero_col, lgtbi_col])

        policia_seg_vig = sum(safe_num(row[col]) for col in [seguridad_col, vigilancias_col])
        policia_control = sum(safe_num(row[col]) for col in [administrativa_col, actos_col])
        policia_hum = sum(safe_num(row[col]) for col in [informacion_col, incidencias_col, humanitarios_col])

        bomberos_rescate = sum(safe_num(row[col]) for col in [salvamentos_col, asistencia_col])
        bomberos_alerta = sum(safe_num(row[col]) for col in [incendios_col, falsas_alarmas_col, mercancias_col])


        edu_stage_sources = {
            "infantil": (row[edu_infantil_total_col], row[edu_infantil_publico_col], row[edu_infantil_extranjero_total_col], row[edu_infantil_unidad_col]),
            "primaria": (row[edu_primaria_total_col], row[edu_primaria_publico_col], row[edu_primaria_extranjero_total_col], row[edu_primaria_unidad_col]),
            "ESO": (row[edu_eso_total_col], row[edu_eso_publico_col], row[edu_eso_extranjero_total_col], row[edu_eso_unidad_col]),
            "bachillerato": (row[edu_bach_total_col], row[edu_bach_publico_col], row[edu_bach_extranjero_total_col], row[edu_bach_unidad_col]),
            "FP grado medio": (row[edu_fpgm_total_col], row[edu_fpgm_publico_col], row[edu_fpgm_extranjero_total_col], row[edu_fpgm_unidad_col]),
            "FP grado superior": (row[edu_fpgs_total_col], row[edu_fpgs_publico_col], row[edu_fpgs_extranjero_total_col], row[edu_fpgs_unidad_col]),
        }

        venta_precio_anual = mean_non_null([row[col] for col in venta_trimestral_precio_cols])
        venta_esfuerzo_anual = mean_non_null([row[col] for col in venta_trimestral_esfuerzo_cols])
        venta_crecimiento_anual = mean_non_null([row[col] for col in venta_trimestral_crecimiento_cols])
        alquiler_idealista_anual = mean_non_null([row[col] for col in alquiler_idealista_cols])

        antig_total = row[antig_total_col]
        antig_menos_25 = sum(safe_num(row[col]) for col in [antig_2001_2010_col, antig_2011_2024_col])
        # Aproximación: en el tramo 1981-2000, se asigna 14/20 a viviendas construidas en 1981-1994.
        antig_mas_30_aprox = sum(
            safe_num(row[col])
            for col in [
                antig_1800_col,
                antig_1801_1900_col,
                antig_1901_1920_col,
                antig_1921_1940_col,
                antig_1941_1960_col,
                antig_1961_1980_col,
            ]
        ) + safe_num(row[antig_1981_2000_col]) * (14 / 20)
        # Aproximación: en el tramo 1921-1940, se asigna 4/20 a viviendas construidas en 1921-1924.
        antig_mas_100_aprox = sum(
            safe_num(row[col]) for col in [antig_1800_col, antig_1801_1900_col, antig_1901_1920_col]
        ) + safe_num(row[antig_1921_1940_col]) * (4 / 20)
        antig_mas_220_aprox = safe_num(row[antig_1800_col])

        valor_total = row[valor_total_col]
        valor_known = None
        if valor_total is not None and not pd.isna(valor_total):
            valor_known = max(float(valor_total) - safe_num(row[valor_no_consta_col]), 0.0)
        valor_bajo = sum(safe_num(row[col]) for col in [valor_12_col, valor_12_18_col])
        valor_medio = sum(safe_num(row[col]) for col in [valor_18_24_col, valor_24_30_col, valor_30_36_col])
        valor_medio_alto = sum(safe_num(row[col]) for col in [valor_36_48_col, valor_48_60_col])
        valor_alto = sum(safe_num(row[col]) for col in [valor_60_72_col, valor_72_col])

        asociaciones_discapacidad_salud_mental = sum(safe_num(row[col]) for col in [asoc_discapacidad_col, asoc_enfermedad_mental_col])
        asociaciones_general_participacion = sum(safe_num(row[col]) for col in [asoc_poblacion_general_col, asoc_otras_participacion_col])
        asociaciones_cultura_deporte_recreativas = sum(safe_num(row[col]) for col in [asoc_culturales_col, asoc_deportivas_col, asoc_fiestas_col])

        plazas_alojamiento_reglado = sum(safe_num(row[col]) for col in [hoteles_plazas_col, hostales_plazas_col, albergues_plazas_col])
        economia_social = sum(safe_num(row[col]) for col in [economia_coop_territorial_col, economia_coop_central_col, economia_sociedades_laborales_col])

        new_values = {
            # Movilidad
            "Movilidad - Paradas EMT [por_km2]": rate_per_km2(row[paradas_emt_col], area_km2),
            "Movilidad - Turismos [por_1000_hab]": rate_per_1000(row[turismos_col], population),
            "Movilidad - Edad media turismos particulares [anos]": row[edad_turismos_col],
            "Movilidad - Superficie aparcamiento por vivienda [m2_vivienda]": row[superficie_aparc_hab_col],
            "Movilidad - Superficie aparcamiento por turismo [m2_turismo]": row[superficie_aparc_turismo_col],
            "Movilidad - Aparcamiento publico o de rotacion [por_1000_hab]": rate_per_1000(
                safe_num(row[aparcamientos_libres_col]) + safe_num(row[aparcamientos_ora_col]) + safe_num(row[aparcamientos_parkings_col]),
                population,
            ),
            "Movilidad - Aparcamiento asociado a vados [por_1000_hab]": rate_per_1000(row[aparcamientos_vados_col], population),
            "Movilidad - Itinerarios ciclistas [m_por_km2]": rate_per_km2(row[itinerarios_ciclistas_m_col], area_km2),
            "Movilidad - Intensidad media de trafico IMV [actual]": row[trafico_imv_col],
            # Bienestar social: vulnerabilidad, asociaciones, recursos, cheques y pobreza
            "Bienestar social - Vulnerabilidad equipamientos [indice]": row[vulnerabilidad_equipamientos_col],
            "Bienestar social - Vulnerabilidad demografia [indice]": row[vulnerabilidad_demografia_col],
            "Bienestar social - Vulnerabilidad economia [indice]": row[vulnerabilidad_economia_col],
            "Bienestar social - Vulnerabilidad global [indice]": row[vulnerabilidad_global_col],
            "Bienestar social - Asociaciones discapacidad y enfermedad mental [por_1000_hab]": rate_per_1000(asociaciones_discapacidad_salud_mental, population),
            "Bienestar social - Asociaciones adicciones [por_1000_hab]": rate_per_1000(row[asoc_adicciones_col], population),
            "Bienestar social - Asociaciones mayores [por_1000_hab]": rate_per_1000(row[asoc_mayores_col], population),
            "Bienestar social - Asociaciones sintecho [por_1000_hab]": rate_per_1000(row[asoc_sintecho_col], population),
            "Bienestar social - Asociaciones etnicas [por_1000_hab]": rate_per_1000(row[asoc_etnicas_col], population),
            "Bienestar social - Asociaciones poblacion general y participacion social [por_1000_hab]": rate_per_1000(asociaciones_general_participacion, population),
            "Bienestar social - Asociaciones culturales, deportivas y recreativas [por_1000_hab]": rate_per_1000(asociaciones_cultura_deporte_recreativas, population),
            "Bienestar social - Asociaciones profesionales y economicas [por_1000_hab]": rate_per_1000(row[asoc_profesionales_col], population),
            "Bienestar social - Recursos discapacidad fisica [por_1000_hab]": rate_per_1000(row[recursos_discapacidad_fisica_col], population),
            "Bienestar social - Recursos toda la poblacion [por_1000_hab]": rate_per_1000(row[recursos_toda_poblacion_col], population),
            "Bienestar social - Recursos conductas adictivas [por_1000_hab]": rate_per_1000(row[recursos_conductas_col], population),
            "Bienestar social - Recursos familia menores y adopciones [por_1000_hab]": rate_per_1000(row[recursos_familia_col], population),
            "Bienestar social - Recursos inmigracion [por_1000_hab]": rate_per_1000(row[recursos_inmigracion_col], population),
            "Bienestar social - Recursos enfermedad mental [por_1000_hab]": rate_per_1000(row[recursos_enfermedad_mental_col], population),
            "Bienestar social - Recursos dependencia [por_1000_hab]": rate_per_1000(row[recursos_dependencia_col], population),
            "Bienestar social - Recursos discapacidad [por_1000_hab]": rate_per_1000(row[recursos_discapacidad_col], population),
            "Bienestar social - Recursos mayores [por_1000_hab]": rate_per_1000(row[recursos_mayores_col], population),
            "Bienestar social - Recursos personas presas y exreclusas [por_1000_hab]": rate_per_1000(row[recursos_personas_presas_col], population),
            "Bienestar social - Recursos juventud [por_1000_hab]": rate_per_1000(row[recursos_juventud_col], population),
            "Bienestar social - Recursos sin techo [por_1000_hab]": rate_per_1000(row[recursos_sin_techo_col], population),
            "Bienestar social - Recursos mujeres [por_1000_hab]": rate_per_1000(row[recursos_mujeres_col], population),
            "Bienestar social - Cheques escolares cobertura poblacion de 0 a 5 anos [%]": row[cheques_cobertura_col],
            "Bienestar social - Cheques escolares solicitantes [por_1000_hab]": rate_per_1000(row[cheques_solicitantes_col], population),
            "Bienestar social - Cheques escolares concedidos sobre solicitudes [%]": row[cheques_porcentaje_concedidos_col],
            "Bienestar social - Renta familiar media solicitantes cheques escolares [EUR]": row[cheques_renta_col],
            "Pobreza - No puede permitirse movil [%]": row[pobreza_movil_no_col],
            "Pobreza - No puede afrontar imprevisto 650 EUR [%]": row[pobreza_imprevisto_no_col],
            "Pobreza - No tiene lavadora [%]": row[pobreza_lavadora_no_col],
            "Pobreza - Infantil (2021) Tasa distrito [%]": row[pobreza_infantil_tasa_col],
            # Educación: alumnado por etapa y PAU
            "Educacion - Alumnado infantil [por_1000_hab]": rate_per_1000(edu_stage_sources["infantil"][0], population),
            "Educacion - Alumnado publico infantil [%]": pct(edu_stage_sources["infantil"][1], edu_stage_sources["infantil"][0]),
            "Educacion - Alumnado extranjero infantil [%]": pct(edu_stage_sources["infantil"][2], edu_stage_sources["infantil"][0]),
            "Educacion - Alumnado por unidad infantil [media]": edu_stage_sources["infantil"][3],
            "Educacion - Alumnado primaria [por_1000_hab]": rate_per_1000(edu_stage_sources["primaria"][0], population),
            "Educacion - Alumnado publico primaria [%]": pct(edu_stage_sources["primaria"][1], edu_stage_sources["primaria"][0]),
            "Educacion - Alumnado extranjero primaria [%]": pct(edu_stage_sources["primaria"][2], edu_stage_sources["primaria"][0]),
            "Educacion - Alumnado por unidad primaria [media]": edu_stage_sources["primaria"][3],
            "Educacion - Alumnado ESO [por_1000_hab]": rate_per_1000(edu_stage_sources["ESO"][0], population),
            "Educacion - Alumnado publico ESO [%]": pct(edu_stage_sources["ESO"][1], edu_stage_sources["ESO"][0]),
            "Educacion - Alumnado extranjero ESO [%]": pct(edu_stage_sources["ESO"][2], edu_stage_sources["ESO"][0]),
            "Educacion - Alumnado por unidad ESO [media]": edu_stage_sources["ESO"][3],
            "Educacion - Alumnado bachillerato [por_1000_hab]": rate_per_1000(edu_stage_sources["bachillerato"][0], population),
            "Educacion - Alumnado publico bachillerato [%]": pct(edu_stage_sources["bachillerato"][1], edu_stage_sources["bachillerato"][0]),
            "Educacion - Alumnado extranjero bachillerato [%]": pct(edu_stage_sources["bachillerato"][2], edu_stage_sources["bachillerato"][0]),
            "Educacion - Alumnado por unidad bachillerato [media]": edu_stage_sources["bachillerato"][3],
            "Educacion - Alumnado FP grado medio [por_1000_hab]": rate_per_1000(edu_stage_sources["FP grado medio"][0], population),
            "Educacion - Alumnado publico FP grado medio [%]": pct(edu_stage_sources["FP grado medio"][1], edu_stage_sources["FP grado medio"][0]),
            "Educacion - Alumnado extranjero FP grado medio [%]": pct(edu_stage_sources["FP grado medio"][2], edu_stage_sources["FP grado medio"][0]),
            "Educacion - Alumnado por unidad FP grado medio [media]": edu_stage_sources["FP grado medio"][3],
            "Educacion - Alumnado FP grado superior [por_1000_hab]": rate_per_1000(edu_stage_sources["FP grado superior"][0], population),
            "Educacion - Alumnado publico FP grado superior [%]": pct(edu_stage_sources["FP grado superior"][1], edu_stage_sources["FP grado superior"][0]),
            "Educacion - Alumnado extranjero FP grado superior [%]": pct(edu_stage_sources["FP grado superior"][2], edu_stage_sources["FP grado superior"][0]),
            "Educacion - Alumnado por unidad FP grado superior [media]": edu_stage_sources["FP grado superior"][3],
            "Educacion - PAU media [nota]": row[pau_media_col],
            "Educacion - PAU alumnado apto [%]": row[pau_apto_pct_col],
            "Educacion - PAU diferencia expediente-PAU [nota]": row[pau_diferencia_col],
            "Educacion - PAU alumnado presentado sobre matriculado [%]": pct(row[pau_presentado_col], row[pau_matriculado_col]),
            # Medio ambiente
            "Medio ambiente - Superficie zonas verdes [m2_hab]": None if population is None or pd.isna(population) or population == 0 else float(row[zonas_verdes_superficie_col]) / float(population),
            "Medio ambiente - Arbolado [por_1000_hab]": rate_per_1000(row[arbolado_col], population),
            "Medio ambiente - Ruido ambiental Lden [media]": row[ruido_lden_media_col],
            "Medio ambiente - NO2 (trafico) [ug_m3_media]": row[contaminacion_no2_col],
            "Medio ambiente - Contaminacion por particulas PM10_PM2.5 [indice_z]": particulas_index_by_row.get(row.name),
            "Medio ambiente - Ozono (contaminante secundario) [ug_m3_media]": row[contaminacion_ozono_col],
            # Demografía general
            "Demografia - Densidad poblacion [hab_km2]": row[demog_densidad_col],
            "Demografia - Variacion interanual poblacion [%]": row[demog_variacion_col],
            "Demografia - Edad media [anos]": row[demog_edad_media_col],
            "Demografia - Esperanza de vida al nacimiento [anos]": row[demog_esperanza_col],
            "Demografia - Indice estructura poblacion activa": row[demog_indice_estructura_col],
            "Demografia - Poblacion 0-14 [%]": row[demog_edad_0_14_col],
            "Demografia - Poblacion 15-64 [%]": row[demog_edad_15_64_col],
            "Demografia - Poblacion 65+ [%]": row[demog_edad_65_col],
            "Demografia - Nacidos en Valencia [%]": row[demog_nac_valencia_col],
            "Demografia - Nacidos en el extranjero [%]": row[demog_nac_extranjero_col],
            # Extranjería residencial
            "Demografia - Poblacion extranjera [% poblacion]": pct(row[total_extr_col], population),
            "Demografia - Edad media poblacion extranjera [anos]": row[edad_extranjera_col],
            "Demografia - Poblacion extranjera UE27 [% extranjera]": pct(row[ue27_col], total_extr),
            "Demografia - Poblacion extranjera resto Europa [% extranjera]": pct(row[resto_europa_col], total_extr),
            "Demografia - Poblacion extranjera Africa [% extranjera]": pct(row[africa_col], total_extr),
            "Demografia - Poblacion extranjera America Norte [% extranjera]": pct(row[america_norte_col], total_extr),
            "Demografia - Poblacion extranjera America Central [% extranjera]": pct(row[america_central_col], total_extr),
            "Demografia - Poblacion extranjera America Sur [% extranjera]": pct(row[america_sur_col], total_extr),
            "Demografia - Poblacion extranjera Asia [% extranjera]": pct(row[asia_col], total_extr),
            "Demografia - Poblacion extranjera otros origenes [% extranjera]": pct(row[otros_col], total_extr),
            # Hechos discriminatorios
            "Hechos discriminatorios [por_1000_hab]": rate_per_1000(row[hechos_total_col], population),
            "Hechos discriminatorios - Discriminación étnico-cultural y racial [por_1000_hab]": rate_per_1000(etnico_racial, population),
            "Hechos discriminatorios - Intolerancia religiosa [por_1000_hab]": rate_per_1000(intolerancia_religiosa, population),
            "Hechos discriminatorios - Capacitismo [por_1000_hab]": rate_per_1000(capacitismo, population),
            "Hechos discriminatorios - Discriminación por sexo-género y diversidad sexual [por_1000_hab]": rate_per_1000(sexo_genero_div, population),
            "Hechos discriminatorios - Aporofobia [por_1000_hab]": rate_per_1000(row[aporofobia_col], population),
            "Hechos discriminatorios - Ideologia [por_1000_hab]": rate_per_1000(row[ideologia_col], population),
            "Hechos discriminatorios - Interseccional [por_1000_hab]": rate_per_1000(row[interseccional_col], population),
            "Hechos discriminatorios - Edadismo [por_1000_hab]": rate_per_1000(row[edadismo_col], population),
            # Policía y bomberos
            "Policia local - Trafico y movilidad [por_1000_hab]": rate_per_1000(row[trafico_col], population),
            "Policia local - Seguridad y vigilancia [por_1000_hab]": rate_per_1000(policia_seg_vig, population),
            "Policia local - Control administrativo y espacio publico [por_1000_hab]": rate_per_1000(policia_control, population),
            "Policia local - Atencion e incidencias humanitario-riesgo [por_1000_hab]": rate_per_1000(policia_hum, population),
            "Bomberos - Rescate y asistencia [por_1000_hab]": rate_per_1000(bomberos_rescate, population),
            "Bomberos - Incendios y alertas de riesgo [por_1000_hab]": rate_per_1000(bomberos_alerta, population),
            # Economia
            "Economia - Renta neta media por persona [EUR]": row[economia_renta_persona_col],
            "Economia - Mediana renta por unidad de consumo [EUR]": row[economia_mediana_unidad_col],
            "Economia - Desigualdad renta Gini [indice]": row[economia_gini_col],
            "Economia - Fuente ingresos salario [%]": row[economia_ingresos_salario_col],
            "Economia - Fuente ingresos pensiones [%]": row[economia_ingresos_pensiones_col],
            "Economia - Fuente ingresos prestaciones desempleo [%]": row[economia_ingresos_desempleo_col],
            "Economia - Poblacion ocupada [% 16+]": row[economia_ocupada_col],
            "Economia - Poblacion parada [% 16+]": row[economia_parada_col],
            "Economia - Jubilacion o prejubilacion [% 16+]": row[economia_jubilacion_col],
            "Economia - Ocupados por cuenta propia [% ocupados]": row[economia_cuenta_propia_col],
            "Economia - Ocupados cuenta ajena temporal [% ocupados]": row[economia_cuenta_ajena_temporal_col],
            "Economia - Trabaja en el mismo municipio [% ocupados]": row[economia_trabaja_mismo_municipio_col],
            "Economia - Actividades economicas [por_1000_hab]": row[economia_actividades_por_1000_col],
            "Economia - Empresas activas [por_1000_hab]": rate_per_1000(row[economia_empresas_total_col], population),
            "Economia - Empresas persona juridica [% empresas]": pct(row[economia_empresas_persona_juridica_col], row[economia_empresas_total_col]),
            "Economia - Empresas industria [% empresas]": pct(row[economia_empresas_industria_col], row[economia_empresas_total_col]),
            "Economia - Empresas construccion [% empresas]": pct(row[economia_empresas_construccion_col], row[economia_empresas_total_col]),
            "Economia - Empresas servicios [% empresas]": pct(row[economia_empresas_servicios_col], row[economia_empresas_total_col]),
            "Economia - Actividades industriales [por_1000_hab]": rate_per_1000(row[economia_actividades_industriales_col], population),
            "Economia - Grado de terciarizacion economica [%]": row[economia_terciarizacion_col],
            "Economia - Plazas alojamiento turistico reglado [por_1000_hab]": rate_per_1000(plazas_alojamiento_reglado, population),
            "Economia - Viviendas turisticas [plazas_por_1000_hab]": rate_per_1000(row[viviendas_tur_plazas_col], population),
            "Economia - Viviendas turisticas [% viviendas]": row[viviendas_tur_pct_col],
            "Economia - Oficinas bancarias [por_10000_hab]": row[economia_oficinas_bancarias_col],
            "Economia - Terrazas hosteleria [por_1000_hab]": rate_per_1000(row[economia_terrazas_n_col], population),
            "Economia - Terrazas hosteleria superficie [m2_por_1000_hab]": rate_per_1000(row[economia_terrazas_superficie_col], population),
            "Economia - Economia social cooperativas y sociedades laborales [por_1000_hab]": rate_per_1000(economia_social, population),
            # Turismo antiguo sustituido por las variables sinteticas de economia anteriores
            "Economia 2024 | Hoteles [plazas_por_1000_hab]": rate_per_1000(row[hoteles_plazas_col], population),
            "Economia 2024 | Hostales y pensiones [plazas_por_1000_hab]": rate_per_1000(row[hostales_plazas_col], population),
            "Economia 2024 | Albergues urbanos [plazas_por_1000_hab]": rate_per_1000(row[albergues_plazas_col], population),
            "Economia 2024 | Viviendas turisticas [plazas_por_1000_hab]": rate_per_1000(row[viviendas_tur_plazas_col], population),
            # Vivienda: precios, alquiler e intensidad residencial
            "Edificacion vivienda 2024 venta trimestral | Precio medio anual [EUR_m2]": venta_precio_anual,
            "Edificacion vivienda 2024 venta trimestral | Esfuerzo financiero medio [%]": venta_esfuerzo_anual,
            "Edificacion vivienda 2024 venta trimestral | Crecimiento anual compuesto medio [%]": venta_crecimiento_anual,
            "Edificacion vivienda 2024 alquiler idealista | Precio medio anual [EUR_m2_mes]": alquiler_idealista_anual,
            "Edificacion vivienda 2023 alquiler | Viviendas alquiladas [por_1000_hab]": rate_per_1000(row[alquiler_total_col], population),
            "Edificacion vivienda 2025 residencial | Viviendas [por_1000_hab]": rate_per_1000(row[antig_total_col], population),
            # Vivienda: licencias y rehabilitación
            "Edificacion vivienda 2024 licencias construccion | Viviendas [por_1000_hab]": rate_per_1000(row[lic_viviendas_col], population),
            "Edificacion vivienda 2024 licencias construccion | Aparcamientos [por_1000_hab]": rate_per_1000(row[lic_aparcamientos_col], population),
            "Edificacion vivienda 2024 licencias construccion | Industrial/comercial [por_1000_hab]": rate_per_1000(row[lic_industrial_col], population),
            "Edificacion vivienda 2024 licencias construccion | Edificios [por_1000_hab]": rate_per_1000(row[lic_edificios_col], population),
            "Edificacion vivienda 2024 licencias construccion | Viviendas con licencia [por_1000_hab]": rate_per_1000(row[lic_viviendas_con_col], population),
            "Edificacion vivienda 2024 licencias construccion | Garajes con licencia [por_1000_hab]": rate_per_1000(row[lic_garajes_con_col], population),
            "Edificacion vivienda 2024 rehabilitacion | Integral [por_1000_hab]": rate_per_1000(row[rehab_integral_col], population),
            "Edificacion vivienda 2024 rehabilitacion | Parcial [por_1000_hab]": rate_per_1000(row[rehab_parcial_col], population),
            # Vivienda: inmuebles por uso
            "Edificacion vivienda 2025 inmuebles uso | Residencial [por_1000_hab]": rate_per_1000(row[uso_residencial_col], population),
            "Edificacion vivienda 2025 inmuebles uso | Almacen/aparcamiento [por_1000_hab]": rate_per_1000(row[uso_almacen_col], population),
            "Edificacion vivienda 2025 inmuebles uso | Comercial [por_1000_hab]": rate_per_1000(row[uso_comercial_col], population),
            "Edificacion vivienda 2025 inmuebles uso | Oficinas [por_1000_hab]": rate_per_1000(row[uso_oficinas_col], population),
            "Edificacion vivienda 2025 inmuebles uso | Industrial [por_1000_hab]": rate_per_1000(row[uso_industrial_col], population),
            "Edificacion vivienda 2025 inmuebles uso | Resto [por_1000_hab]": rate_per_1000(row[uso_resto_col], population),
            # Vivienda: antigüedad residencial
            "Edificacion vivienda 2025 residencial antiguedad | Menos de 5 anos [%]": row[pct_menos_5_col],
            "Edificacion vivienda 2025 residencial antiguedad | Menos de 10 anos [%]": row[pct_menos_10_col],
            "Edificacion vivienda 2025 residencial antiguedad | Menos de 25 anos [%]": pct(antig_menos_25, antig_total),
            "Edificacion vivienda 2025 residencial antiguedad | Mas de 30 anos aprox [%]": pct(antig_mas_30_aprox, antig_total),
            "Edificacion vivienda 2025 residencial antiguedad | Mas de 50 anos [%]": row[pct_mas_50_col],
            "Edificacion vivienda 2025 residencial antiguedad | Mas de 100 anos aprox [%]": pct(antig_mas_100_aprox, antig_total),
            "Edificacion vivienda 2025 residencial antiguedad | Mas de 220 anos aprox [%]": pct(antig_mas_220_aprox, antig_total),
            # Vivienda: valor catastral por tramos
            "Edificacion vivienda 2025 valor catastral tramos | Bajo <=18k [%]": pct(valor_bajo, valor_known),
            "Edificacion vivienda 2025 valor catastral tramos | Medio 18_36k [%]": pct(valor_medio, valor_known),
            "Edificacion vivienda 2025 valor catastral tramos | Medio-alto 36_60k [%]": pct(valor_medio_alto, valor_known),
            "Edificacion vivienda 2025 valor catastral tramos | Alto >60k [%]": pct(valor_alto, valor_known),
        }

        for column in output_columns:
            if column in new_values:
                out_row[column] = CATEGORY_BY_NEW_COLUMN[column] if category_row else format_es_number(new_values[column])
            else:
                out_row[column] = row.get(column, "")

        out_rows.append(out_row)

    output_df = pd.DataFrame(out_rows, columns=output_columns)
    output_df = reduce_consumo_publico(output_df)
    output_df = reduce_urbanismo_infraestructuras_v12(output_df, report_csv)
    output_df = reduce_urbanismo_infraestructuras_v13(output_df, report_csv)
    output_df = reduce_bloque_otros_v15(output_df, report_csv)
    output_df = reduce_sociedad_demografia_secundaria_v16(output_df, report_csv)
    output_df = reduce_medio_ambiente_secundario_v18(output_df, report_csv)
    output_df = reduce_movilidad_transporte_v19(output_df, report_csv)
    output_df = reduce_cultura_ocio_v20(output_df, report_csv)
    output_df = reagrupar_seguridad_convivencia_v22(output_df, report_csv)
    output_df = reduce_seguridad_convivencia_v23(output_df, report_csv)
    output_df = aplicar_cambios_v24_a_v30(output_df, report_csv, audit_csv)
    output_df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Archivo generado: {output_csv}")
    print(f"Reporte de correlaciones y redundancias: {report_csv}")
    print(f"Reporte de auditoria resumida: {audit_csv}")
    print(f"Columnas originales: {len(original_columns)}")
    print(f"Columnas finales: {len(output_df.columns)}")


def _to_float_v30(value: object) -> float | None:
    return parse_es_number(value)


def _format_v30(value: float | None) -> str:
    return format_es_number(value)


def _drop_cols_v30(output_df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return output_df.drop(columns=[c for c in cols if c in output_df.columns])


def _insert_after_v30(output_df: pd.DataFrame, after_col: str, new_cols: list[str]) -> pd.DataFrame:
    current = [c for c in output_df.columns if c not in new_cols]
    if after_col in current:
        pos = current.index(after_col) + 1
    else:
        pos = len(current)
    for i, col in enumerate(new_cols):
        if col in output_df.columns:
            current.insert(pos + i, col)
    return output_df[current]


def aplicar_cambios_v24_a_v30(output_df: pd.DataFrame, report_csv: Path, audit_csv: Path) -> pd.DataFrame:
    """Aplica en una sola rutina canónica los cambios posteriores a v23.

    Esta función evita que la construcción final dependa de CSV intermedios
    v24, v25, ..., v29: parte de la tabla ya generada desde el CSV maestro
    original y aplica aquí todos los ajustes finales.
    """
    df = output_df.copy()
    cat = df.iloc[0].copy()
    data = df.iloc[1:].copy().reset_index(drop=True)

    def n(col: str) -> pd.Series:
        return data[col].map(_to_float_v30)

    def set_col(col: str, values, categoria: str) -> None:
        data[col] = [_format_v30(v) for v in values]
        cat[col] = categoria

    def pct_series(part, total):
        out = []
        for p, t in zip(part, total):
            if p is None or t is None or pd.isna(p) or pd.isna(t) or t == 0:
                out.append(None)
            else:
                out.append((p / t) * 100.0)
        return out

    def rate_1000_series(value, pop):
        out = []
        for v, p in zip(value, pop):
            if v is None or p is None or pd.isna(v) or pd.isna(p) or p == 0:
                out.append(None)
            else:
                out.append((v / p) * 1000.0)
        return out

    def rate_100_series(value, pop):
        out = []
        for v, p in zip(value, pop):
            if v is None or p is None or pd.isna(v) or pd.isna(p) or p == 0:
                out.append(None)
            else:
                out.append((v / p) * 100.0)
        return out

    # ------------------------------------------------------------------
    # v24: reducción adicional de urbanismo/vivienda
    # ------------------------------------------------------------------
    cat_urb = "Urbanismo e infraestructuras"
    population = n("Padron 2025 | Poblacion")
    superficie_ha = n("Padron 2025 | Superficie [ha]")

    # Recuperar superficie territorial antes de eliminar la columna auxiliar.
    set_col("Territorio - Superficie distrito [km2]", [v / 100.0 if v is not None and not pd.isna(v) else None for v in superficie_ha], cat_urb)

    set_col("Vivienda - Viviendas super recientes menos de 10 anos [%]", n("Edificacion vivienda 2025 residencial antiguedad | Menos de 10 anos [%]"), cat_urb)
    set_col("Vivienda - Viviendas recientes menos de 25 anos [%]", n("Edificacion vivienda 2025 residencial antiguedad | Menos de 25 anos [%]"), cat_urb)
    set_col("Vivienda - Viviendas antiguas mas de 50 anos [%]", n("Edificacion vivienda 2025 residencial antiguedad | Mas de 50 anos [%]"), cat_urb)
    set_col("Vivienda - Viviendas historicas mas de 100 anos aprox [%]", n("Edificacion vivienda 2025 residencial antiguedad | Mas de 100 anos aprox [%]"), cat_urb)

    sup_total = n("Edificacion vivienda 2025 superficie construida | Total [n]")
    small60 = n("Edificacion vivienda 2025 superficie construida | <=60m2 [n]")
    mid_61_120 = n("Edificacion vivienda 2025 superficie construida | 61_80m2 [n]") + n("Edificacion vivienda 2025 superficie construida | 81_100m2 [n]") + n("Edificacion vivienda 2025 superficie construida | 101_120m2 [n]")
    large_121_200 = n("Edificacion vivienda 2025 superficie construida | 121_150m2 [n]") + n("Edificacion vivienda 2025 superficie construida | 151_200m2 [n]")
    very_large_200 = n("Edificacion vivienda 2025 superficie construida | >200m2 [n]")
    set_col("Vivienda - Superficie construida muy pequena <=60m2 [%]", pct_series(small60, sup_total), cat_urb)
    set_col("Vivienda - Superficie construida media 61_120m2 [%]", pct_series(mid_61_120, sup_total), cat_urb)
    set_col("Vivienda - Superficie construida grande 121_200m2 [%]", pct_series(large_121_200, sup_total), cat_urb)
    set_col("Vivienda - Superficie construida muy grande >200m2 [%]", pct_series(very_large_200, sup_total), cat_urb)

    actividad_no_res = n("Edificacion vivienda 2025 inmuebles uso | Comercial [por_1000_hab]") + n("Edificacion vivienda 2025 inmuebles uso | Oficinas [por_1000_hab]") + n("Edificacion vivienda 2025 inmuebles uso | Industrial [por_1000_hab]") + n("Edificacion vivienda 2025 inmuebles uso | Resto [por_1000_hab]")
    set_col("Edificacion vivienda 2025 inmuebles uso | Actividad economica no residencial [por_1000_hab]", actividad_no_res, cat_urb)

    p_small = n("Edificacion vivienda 2025 parcelas urbanas | <=100m2 [n]") + n("Edificacion vivienda 2025 parcelas urbanas | 101_500m2 [n]")
    p_mid = n("Edificacion vivienda 2025 parcelas urbanas | 501_1000m2 [n]") + n("Edificacion vivienda 2025 parcelas urbanas | 1001_10000m2 [n]")
    p_big = n("Edificacion vivienda 2025 parcelas urbanas | >10000m2 [n]")
    p_surf = n("Edificacion vivienda 2025 parcelas urbanas | Superficie total [m2]")
    set_col("Urbanismo - Parcelas urbanas pequenas <=500m2 [por_100_hab]", rate_100_series(p_small, population), cat_urb)
    set_col("Urbanismo - Parcelas urbanas medianas 501_10000m2 [por_100_hab]", rate_100_series(p_mid, population), cat_urb)
    set_col("Urbanismo - Parcelas urbanas grandes >10000m2 [por_100_hab]", rate_100_series(p_big, population), cat_urb)
    set_col("Urbanismo - Parcelas urbanas superficie [m2_hab]", [s / p if s is not None and p is not None and not pd.isna(s) and not pd.isna(p) and p != 0 else None for s, p in zip(p_surf, population)], cat_urb)

    set_col("Vivienda - Peso del valor del suelo sobre valor catastral total [%]", pct_series(n("Edificacion vivienda 2025 valor catastral medio | Valor suelo medio [EUR]"), n("Edificacion vivienda 2025 valor catastral medio | Valor total medio [EUR]")), cat_urb)

    # ------------------------------------------------------------------
    # v26: demografía y bienestar
    # ------------------------------------------------------------------
    inmigracion = n("Demografia - Poblacion inmigrante [% poblacion]") * population / 100.0
    emigracion = n("Demografia - Poblacion emigrante [% poblacion]") * population / 100.0
    saldo_neto_n = n("Demografia - Saldo neto [n]")
    set_col("Demografia - Movilidad residencial total entradas+salidas [por_1000_hab]", rate_1000_series(inmigracion + emigracion, population), "Demografia")
    set_col("Demografia - Balance residencial neto entradas-salidas [por_1000_hab]", rate_1000_series(saldo_neto_n, population), "Demografia")
    recursos_exclusion = n("Bienestar social - Recursos sin techo [por_1000_hab]") + n("Bienestar social - Recursos personas presas y exreclusas [por_1000_hab]")
    set_col("Bienestar social - Recursos exclusion social y reinsercion [por_1000_hab]", recursos_exclusion, "Sociedad y Bienestar")

    # ------------------------------------------------------------------
    # v29: recursos municipales agregados
    # ------------------------------------------------------------------
    m2_cols = [
        "Recursos municipales - Centros escolares, mercados y locales publicos construidos [m2_por_1000_hab]",
        "Recursos municipales - Patrimonio y suelo municipal construidos [m2_por_1000_hab]",
        "Recursos municipales - Otros edificios construidos [m2_por_1000_hab]",
    ]
    val_cols = [
        "Recursos municipales - Centros escolares, mercados y locales publicos valor [EUR_por_1000_hab]",
        "Recursos municipales - Patrimonio y suelo municipal valor [EUR_por_1000_hab]",
        "Recursos municipales - Otros edificios valor [EUR_por_1000_hab]",
    ]
    m2_sum = sum(n(c) for c in m2_cols)
    val_sum = sum(n(c) for c in val_cols)
    set_col("Recursos municipales - Dotacion municipal construida [m2_por_1000_hab]", m2_sum, cat_urb)
    set_col("Recursos municipales - Valor patrimonial municipal [EUR_por_1000_hab]", val_sum, cat_urb)

    # ------------------------------------------------------------------
    # Reorganización de bloques y renombrados finales
    # ------------------------------------------------------------------
    # Se renombra juegos infantiles y se mueve a Sociedad y Bienestar.
    if "Medio ambiente - Juegos infantiles superficie [m2_por_km2]" in data.columns:
        data = data.rename(columns={"Medio ambiente - Juegos infantiles superficie [m2_por_km2]": "Cultura y ocio - Juegos infantiles superficie [m2_por_km2]"})
        cat = cat.rename(index={"Medio ambiente - Juegos infantiles superficie [m2_por_km2]": "Cultura y ocio - Juegos infantiles superficie [m2_por_km2]"})
    cat["Cultura y ocio - Juegos infantiles superficie [m2_por_km2]"] = "Sociedad y Bienestar"

    # Categorías finales.
    for c in data.columns:
        if c not in cat.index:
            continue
        if cat[c] == "Movilidad, seguridad y convivencia":
            cat[c] = "Seguridad y convivencia"
        if cat[c] == "Movilidad":
            cat[c] = "Movilidad y transporte"
        if cat[c] == "Medio Ambiente y servicios urbanos":
            cat[c] = "Medio Ambiente"
        if cat[c] == "Cultura y Ocio":
            cat[c] = "Sociedad y Bienestar"
        if cat[c] == "Otros":
            cat[c] = "Politica"

    for c in ["Puntos WiFi [por_km2]", "Puntos WiFi [por_1000_hab]", "Recursos municipales 2024 | Sugerencias quejas y reclamaciones [%]"]:
        if c in data.columns:
            cat[c] = "Sociedad y Bienestar"

    # Separación final de Demografía y Sociedad/Bienestar.
    # Muchas variables demográficas proceden de un bloque antiguo de sociedad;
    # se reasignan por prefijo para que la fila de categorías sea consistente.
    for c in data.columns:
        if c.startswith("Demografia -"):
            cat[c] = "Demografia"
        elif c.startswith("Bienestar social -") or c.startswith("Pobreza -") or c.startswith("Innovacion social -"):
            cat[c] = "Sociedad y Bienestar"
        elif c.startswith("Cultura y ocio -"):
            cat[c] = "Sociedad y Bienestar"
        elif c.startswith("Politica -"):
            cat[c] = "Politica"

    # Restaurar el contrato de fila temática usado en las versiones previas:
    # la fila de categorías se identifica con codigo == "__categoria__".
    # Así los pipelines que excluyen la fila temática siguen funcionando.
    cat["codigo"] = "__categoria__"
    cat["nombre"] = "CATEGORIA"
    cat["Padron 2025 | Poblacion"] = "Auxiliar"

    # ------------------------------------------------------------------
    # Columnas eliminadas por v24-v30
    # ------------------------------------------------------------------
    cols_drop = [
        # v24
        "Calificaciones urbanisticas [n]",
        "Encuesta superficie distrito [ha]",
        "Encuesta superficie distrito [m2]",
        "Encuesta superficie distrito [km2]",
        "Edificacion vivienda 2025 residencial antiguedad | Menos de 5 anos [%]",
        "Edificacion vivienda 2025 residencial antiguedad | Menos de 10 anos [%]",
        "Edificacion vivienda 2025 residencial antiguedad | Menos de 25 anos [%]",
        "Edificacion vivienda 2025 residencial antiguedad | Mas de 30 anos aprox [%]",
        "Edificacion vivienda 2025 residencial antiguedad | Mas de 50 anos [%]",
        "Edificacion vivienda 2025 residencial antiguedad | Mas de 100 anos aprox [%]",
        "Edificacion vivienda 2025 residencial antiguedad | Mas de 220 anos aprox [%]",
        "Vivienda - Viviendas de menos de 60 m2 [%]",
        "Vivienda - Viviendas de menos de 80 m2 [%]",
        "Edificacion vivienda 2025 superficie construida | Total [n]",
        "Edificacion vivienda 2025 superficie construida | <=60m2 [n]",
        "Edificacion vivienda 2025 superficie construida | 61_80m2 [n]",
        "Edificacion vivienda 2025 superficie construida | 81_100m2 [n]",
        "Edificacion vivienda 2025 superficie construida | 101_120m2 [n]",
        "Edificacion vivienda 2025 superficie construida | 121_150m2 [n]",
        "Edificacion vivienda 2025 superficie construida | 151_200m2 [n]",
        "Edificacion vivienda 2025 superficie construida | >200m2 [n]",
        "Edificacion vivienda 2025 inmuebles uso | Comercial [por_1000_hab]",
        "Edificacion vivienda 2025 inmuebles uso | Oficinas [por_1000_hab]",
        "Edificacion vivienda 2025 inmuebles uso | Industrial [por_1000_hab]",
        "Edificacion vivienda 2025 inmuebles uso | Resto [por_1000_hab]",
        "Edificacion vivienda 2025 parcelas urbanas | Total [n]",
        "Edificacion vivienda 2025 parcelas urbanas | <=100m2 [n]",
        "Edificacion vivienda 2025 parcelas urbanas | 101_500m2 [n]",
        "Edificacion vivienda 2025 parcelas urbanas | 501_1000m2 [n]",
        "Edificacion vivienda 2025 parcelas urbanas | 1001_10000m2 [n]",
        "Edificacion vivienda 2025 parcelas urbanas | >10000m2 [n]",
        "Edificacion vivienda 2025 parcelas urbanas | Superficie total [m2]",
        "Edificacion vivienda 2025 valor catastral medio | Valor suelo medio [EUR]",
        "Edificacion vivienda 2025 valor catastral medio | Valor construccion medio [EUR]",
        "Edificacion vivienda 2025 valor catastral medio | Valor total medio [EUR]",
        "Edificacion vivienda 2025 valor catastral medio | Valor medio m2 [EUR]",
        # v25
        "Edificacion vivienda 2025 inmuebles uso | Residencial [por_1000_hab]",
        "Vivienda - Viviendas proteccion publica [por_100_hab]",
        # v26
        "Demografia - Nacidos en el extranjero [%]",
        "Demografia - Indice de aloctonia estatal [2025]",
        "Demografia - Poblacion inmigrante [% poblacion]",
        "Demografia - Poblacion emigrante [% poblacion]",
        "Demografia - Saldo neto [n]",
        "Demografia - Poblacion 15-64 [%]",
        "Demografia - Indice demografico de dependencia [2025]",
        "Demografia - Tasa bruta de natalidad [2024]",
        "Bienestar social - Recursos personas presas y exreclusas [por_1000_hab]",
        "Bienestar social - Recursos sin techo [por_1000_hab]",
        "Padron 2025 | Superficie [ha]",
        # v28
        "Bancos en via publica [por_1000_hab]",
        "Manzanas catastrales [por_1000_hab]",
        "Vivienda - Superficie construida media 61_120m2 [%]",
        "Vivienda - Superficie construida grande 121_200m2 [%]",
        "Edificacion vivienda 2025 valor catastral tramos | Medio 18_36k [%]",
        "Edificacion vivienda 2025 valor catastral tramos | Medio-alto 36_60k [%]",
        "Anuario 2021 vivienda | superficie por ocupante 20-40m2 [% distrito]",
        # v29
        *m2_cols,
        *val_cols,
        # v30 politica exacta derivable
        "Politica - Votos a candidaturas media [% votos validos]",
    ]

    # Orden de columnas: partir del orden actual e insertar nuevas columnas donde corresponde.
    preferred_order = list(data.columns)
    insertions = {
        "nombre": ["Territorio - Superficie distrito [km2]"],
        "Edificacion vivienda 2025 residencial antiguedad | Mas de 220 anos aprox [%]": [
            "Vivienda - Viviendas super recientes menos de 10 anos [%]",
            "Vivienda - Viviendas recientes menos de 25 anos [%]",
            "Vivienda - Viviendas antiguas mas de 50 anos [%]",
            "Vivienda - Viviendas historicas mas de 100 anos aprox [%]",
        ],
        "Edificacion vivienda 2025 superficie construida | >200m2 [n]": [
            "Vivienda - Superficie construida muy pequena <=60m2 [%]",
            "Vivienda - Superficie construida muy grande >200m2 [%]",
        ],
        "Edificacion vivienda 2025 inmuebles uso | Resto [por_1000_hab]": [
            "Edificacion vivienda 2025 inmuebles uso | Actividad economica no residencial [por_1000_hab]",
        ],
        "Edificacion vivienda 2025 parcelas urbanas | Superficie total [m2]": [
            "Urbanismo - Parcelas urbanas pequenas <=500m2 [por_100_hab]",
            "Urbanismo - Parcelas urbanas medianas 501_10000m2 [por_100_hab]",
            "Urbanismo - Parcelas urbanas grandes >10000m2 [por_100_hab]",
            "Urbanismo - Parcelas urbanas superficie [m2_hab]",
        ],
        "Edificacion vivienda 2025 valor catastral medio | Valor medio m2 [EUR]": [
            "Vivienda - Peso del valor del suelo sobre valor catastral total [%]",
        ],
        "Demografia - Saldo neto [n]": [
            "Demografia - Movilidad residencial total entradas+salidas [por_1000_hab]",
            "Demografia - Balance residencial neto entradas-salidas [por_1000_hab]",
        ],
        "Bienestar social - Recursos mujeres [por_1000_hab]": [
            "Bienestar social - Recursos exclusion social y reinsercion [por_1000_hab]",
        ],
        "Recursos municipales - Otros edificios valor [EUR_por_1000_hab]": [
            "Recursos municipales - Dotacion municipal construida [m2_por_1000_hab]",
            "Recursos municipales - Valor patrimonial municipal [EUR_por_1000_hab]",
        ],
    }

    # Quitar nuevas columnas del orden base si quedaron añadidas al final.
    all_new = [c for v in insertions.values() for c in v]
    preferred_order = [c for c in preferred_order if c not in all_new and c not in cols_drop]
    for anchor, new_cols in insertions.items():
        new_cols_existing = [c for c in new_cols if c in data.columns and c not in cols_drop]
        if not new_cols_existing:
            continue
        if anchor in preferred_order:
            pos = preferred_order.index(anchor) + 1
        else:
            pos = len(preferred_order)
        for offset, col in enumerate(new_cols_existing):
            if col not in preferred_order:
                preferred_order.insert(pos + offset, col)

    # Si queda alguna columna no incluida, añadirla al final.
    for col in data.columns:
        if col not in preferred_order and col not in cols_drop:
            preferred_order.append(col)

    df_final = pd.concat([pd.DataFrame([cat.to_dict()]), data], ignore_index=True)
    df_final = df_final[[c for c in preferred_order if c in df_final.columns]]

    # Reescribir reporte como auditoría global, no como reporte parcial de un parche.
    audit_rows = [
        {"seccion": "reproducibilidad", "medida": "entrada", "valor": "tabla_por_distritos_limpia.csv"},
        {"seccion": "reproducibilidad", "medida": "dependencias_intermedias", "valor": "ninguna"},
        {"seccion": "politica", "medida": "columna_derivable_eliminada", "valor": "Politica - Votos a candidaturas media [% votos validos]"},
        {"seccion": "politica", "medida": "motivo", "valor": "Votos a candidaturas = 100 - votos en blanco"},
        {"seccion": "categorias", "medida": "Padron 2025 | Poblacion", "valor": "Auxiliar"},
        {"seccion": "categorias", "medida": "codigo/nombre", "valor": "__categoria__/CATEGORIA"},
        {"seccion": "salida", "medida": "columnas_finales", "valor": len(df_final.columns)},
        {"seccion": "salida", "medida": "filas_incluyendo_categoria", "valor": len(df_final)},
    ]
    pd.DataFrame(audit_rows).to_csv(audit_csv, index=False, encoding="utf-8")

    return df_final




# =============================================================================
# FUNCIONES DE JERARQUIZACIÓN
# =============================================================================

def norm(s: str) -> str:
    return (s or '').lower()


def infer_role(col: str, block: str) -> str:
    if col in ('codigo', 'nombre'):
        return 'Identificacion'
    if block == 'Auxiliar' or col == 'Padron 2025 | Poblacion':
        return 'Auxiliar'
    if block == 'Politica':
        return 'Suplementaria interpretativa'
    if col == 'Territorio - Superficie distrito [km2]':
        return 'Suplementaria contextual'
    return 'Activa candidata'


def infer_subdimension(col: str, block: str) -> str:
    s = norm(col)
    if col == 'codigo':
        return 'Identificacion territorial'
    if col == 'nombre':
        return 'Identificacion territorial'
    if col == 'Padron 2025 | Poblacion':
        return 'Denominador poblacional'

    if block == 'Urbanismo e infraestructuras':
        if 'superficie distrito' in s:
            return 'Territorio'
        if 'proteccion publica' in s:
            return 'Vivienda protegida'
        if 'valor catastral' in s or 'valor del suelo' in s or 'valor medio' in s:
            return 'Valor catastral y valor del suelo'
        if 'venta trimestral' in s or 'alquiler idealista' in s or 'viviendas alquiladas' in s:
            return 'Mercado residencial'
        if 'antiguedad' in s or 'recientes' in s or 'antiguas' in s or 'historicas' in s:
            return 'Antigüedad residencial'
        if 'superficie construida' in s or 'superficie por ocupante' in s or 'establecimiento colectivo' in s:
            return 'Condiciones residenciales y tamaño de vivienda'
        if 'solares' in s or 'paa' in s or 'parcelas urbanas' in s or 'manzanas catastrales' in s:
            return 'Suelo urbano, parcelas y actuaciones urbanísticas'
        if 'bancos en via publica' in s:
            return 'Espacio público urbano'
        if 'licencias construccion' in s or 'rehabilitacion' in s:
            return 'Licencias, construcción y rehabilitación'
        if 'inmuebles uso' in s or 'aparcamientos' in s:
            return 'Usos del inmueble y aparcamiento edificado'
        if 'recursos municipales' in s:
            return 'Patrimonio y dotación municipal'
        if 'viviendas [por_1000_hab]' in s or 'residencial | viviendas' in s:
            return 'Parque residencial'
        return 'Urbanismo general'

    if block == 'Movilidad y transporte':
        if 'emt' in s:
            return 'Transporte público'
        if 'turismos' in s:
            return 'Parque móvil'
        if 'aparcamiento' in s:
            return 'Aparcamiento'
        if 'ciclistas' in s:
            return 'Infraestructura ciclista'
        if 'trafico' in s or 'velocidad' in s:
            return 'Tráfico y red viaria'
        if 'ocupacion via publica' in s:
            return 'Ocupación de vía pública'
        if 'valenbisi' in s:
            return 'Bicicleta pública'
        return 'Movilidad general'

    if block == 'Economia':
        if 'renta' in s or 'gini' in s:
            return 'Renta y desigualdad'
        if 'fuente ingresos' in s:
            return 'Fuentes de ingresos'
        if 'poblacion ocupada' in s or 'poblacion parada' in s or 'jubilacion' in s or 'ocupados' in s or 'trabaja' in s:
            return 'Mercado laboral'
        if 'actividades economicas' in s or 'empresas' in s or 'industriales' in s or 'terciarizacion' in s:
            return 'Tejido empresarial y actividad económica'
        if 'alojamiento' in s or 'viviendas turisticas' in s or 'terrazas' in s:
            return 'Turismo, hostelería y terciarización urbana'
        if 'oficinas bancarias' in s or 'economia social' in s:
            return 'Servicios económicos y economía social'
        return 'Economía general'

    if block == 'Demografia':
        if 'densidad' in s:
            return 'Densidad poblacional'
        if 'crecimiento vegetativo' in s or 'variacion interanual' in s or 'fecundidad' in s or 'mortalidad' in s or 'movilidad residencial' in s or 'balance residencial' in s or 'inmigracion intraurbana' in s or 'interurbana' in s or 'emigracion' in s:
            return 'Dinámica demográfica y movilidad residencial'
        if 'edad media' in s or 'esperanza de vida' in s or 'poblacion 0-14' in s or 'poblacion 65+' in s or 'envejecimiento' in s or 'estructura poblacion activa' in s or 'progresividad' in s:
            return 'Estructura por edad y envejecimiento'
        if 'hogares' in s or 'personas por hogar' in s:
            return 'Estructura de hogares'
        if 'extranjera' in s or 'nacidos en valencia' in s:
            return 'Origen y población extranjera'
        if 'solteras' in s or 'casadas' in s or 'viudas' in s or 'separadas' in s or 'masculinidad' in s:
            return 'Estado civil y composición por sexo'
        return 'Demografía general'

    if block == 'Sociedad y Bienestar':
        if 'innovacion social' in s:
            return 'Innovación social'
        if 'vulnerabilidad' in s:
            return 'Vulnerabilidad social'
        if 'asociaciones' in s:
            return 'Tejido asociativo'
        if 'recursos' in s and 'sugerencias' not in s:
            return 'Recursos sociales'
        if 'cheques escolares' in s or 'renta familiar media' in s:
            return 'Ayudas educativas y renta familiar'
        if 'pobreza' in s or 'no puede' in s or 'lavadora' in s or 'movil' in s:
            return 'Pobreza y privación material'
        if 'cultura y ocio' in s or 'clubs federados' in s or 'zonas de actividades' in s or 'juegos infantiles' in s:
            return 'Cultura, ocio y dotaciones recreativas'
        if 'wifi' in s:
            return 'Acceso digital'
        if 'sugerencias' in s or 'quejas' in s or 'reclamaciones' in s:
            return 'Relación ciudadanía-administración'
        return 'Sociedad y bienestar general'

    if block == 'Educacion':
        if 'centros publicos' in s or 'centros concertados' in s or 'centros privados' in s:
            return 'Titularidad de centros'
        if 'centros educativos' in s or 'colecaminos' in s:
            return 'Infraestructura y accesibilidad educativa'
        if 'titulacion' in s:
            return 'Nivel educativo de la población adulta'
        if 'infantil' in s:
            return 'Alumnado infantil'
        if 'primaria' in s:
            return 'Alumnado primaria'
        if 'eso' in s:
            return 'Alumnado ESO'
        if 'bachillerato' in s and 'pau' not in s:
            return 'Alumnado bachillerato'
        if 'fp grado medio' in s:
            return 'Alumnado FP grado medio'
        if 'fp grado superior' in s:
            return 'Alumnado FP grado superior'
        if 'pau' in s:
            return 'Resultados PAU'
        return 'Educación general'

    if block == 'Medio Ambiente':
        if 'consumo publico' in s or 'agua' in s or 'alumbrado' in s or 'pasos inferiores' in s or 'monumentos' in s:
            return 'Consumo público y servicios urbanos'
        if 'zonas verdes' in s or 'arbolado' in s:
            return 'Zonas verdes y arbolado'
        if 'ruido' in s or 'no2' in s or 'contaminacion' in s or 'ozono' in s:
            return 'Ruido y contaminación atmosférica'
        if 'fuentes' in s:
            return 'Fuentes y agua urbana'
        if 'acusticamente saturadas' in s:
            return 'Presión acústica urbana'
        if 'escombros' in s:
            return 'Residuos y escombros'
        return 'Medio ambiente general'

    if block == 'Seguridad y convivencia':
        if 'hechos discriminatorios' in s:
            return 'Hechos discriminatorios y convivencia'
        if 'hidrantes' in s:
            return 'Infraestructura de emergencia'
        if 'policia local' in s:
            return 'Policía local'
        if 'bomberos' in s:
            return 'Bomberos y emergencias'
        return 'Seguridad general'

    if block == 'Politica':
        if 'participacion' in s:
            return 'Participación electoral'
        if 'nulos' in s or 'blanco' in s:
            return 'Calidad del voto'
        if 'bloque izquierda' in s or 'bloque derecha' in s:
            return 'Bloques ideológicos'
        return 'Voto por partidos y candidaturas'

    return 'Sin subdimensión asignada'


def explain_role(role: str) -> str:
    if role == 'Activa candidata':
        return 'Variable candidata para PCA/clustering tras estandarización y revisión final de colinealidad.'
    if role == 'Suplementaria interpretativa':
        return 'Variable útil para interpretar perfiles, no recomendada como activa por defecto.'
    if role == 'Suplementaria contextual':
        return 'Variable contextual/estructural; útil para interpretación o análisis auxiliar.'
    if role == 'Auxiliar':
        return 'Variable denominadora o auxiliar; no debe entrar como activa en PCA/clustering.'
    if role == 'Identificacion':
        return 'Identificador territorial; no debe entrar en análisis multivariante.'
    return ''


# =============================================================================
# PARTE 2. JERARQUIZACIÓN DE VARIABLES
# =============================================================================

import csv
from collections import Counter

OUTPUT_HIERARCHIZED_NAME = "tabla_por_distritos_final_jerarquizada.csv"
OUTPUT_DICTIONARY_NAME = "diccionario_jerarquia_variables_final.csv"
OUTPUT_SUMMARY_NAME = "resumen_jerarquia_bloques_final.csv"


def write_hierarchy_files(depurada_csv: Path) -> tuple[Path, Path, Path]:
    """Añade subdimensiones y roles de análisis a la tabla depurada final.

    La tabla depurada conserva la primera fila temática con:
        codigo = "__categoria__"
        nombre = "CATEGORIA"

    A partir de esa fila se generan:
        1. tabla final jerarquizada con filas de metadatos adicionales;
        2. diccionario largo de variables;
        3. resumen por bloque, subdimensión y rol.
    """
    output_table = depurada_csv.with_name(OUTPUT_HIERARCHIZED_NAME)
    output_dict = depurada_csv.with_name(OUTPUT_DICTIONARY_NAME)
    output_summary = depurada_csv.with_name(OUTPUT_SUMMARY_NAME)

    with depurada_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    headers = rows[0]
    categories = rows[1]
    data_rows = rows[2:]

    subdims = []
    roles = []
    dictionary = []

    for i, col in enumerate(headers):
        block = categories[i] if i < len(categories) else ""

        if col == "codigo":
            block = "Identificacion"
        elif col == "nombre":
            block = "Identificacion"

        subdim = infer_subdimension(col, block)
        role = infer_role(col, block)

        subdims.append(subdim)
        roles.append(role)
        dictionary.append({
            "orden": i + 1,
            "variable": col,
            "bloque_tematico": block,
            "subdimension": subdim,
            "rol_analisis": role,
            "nota_uso": explain_role(role),
        })

    metadata_rows = [
        categories,
        ["__subdimension__" if c == "codigo" else "SUBDIMENSION" if c == "nombre" else subdims[i] for i, c in enumerate(headers)],
        ["__rol_analisis__" if c == "codigo" else "ROL_ANALISIS" if c == "nombre" else roles[i] for i, c in enumerate(headers)],
    ]

    with output_table.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(metadata_rows)
        w.writerows(data_rows)

    with output_dict.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["orden", "variable", "bloque_tematico", "subdimension", "rol_analisis", "nota_uso"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(dictionary)

    block_counts = Counter(d["bloque_tematico"] for d in dictionary)
    active_counts = Counter((d["bloque_tematico"], d["rol_analisis"]) for d in dictionary)
    subdim_counts = Counter((d["bloque_tematico"], d["subdimension"]) for d in dictionary)

    with output_summary.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["bloque_tematico", "subdimension", "rol_analisis", "n_variables"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for block in block_counts:
            w.writerow({
                "bloque_tematico": block,
                "subdimension": "TOTAL BLOQUE",
                "rol_analisis": "",
                "n_variables": block_counts[block],
            })

        for (block, subdim), count in subdim_counts.items():
            w.writerow({
                "bloque_tematico": block,
                "subdimension": subdim,
                "rol_analisis": "",
                "n_variables": count,
            })

        for (block, role), count in active_counts.items():
            w.writerow({
                "bloque_tematico": block,
                "subdimension": "",
                "rol_analisis": role,
                "n_variables": count,
            })

    return output_table, output_dict, output_summary


def main() -> None:
    """Ejecuta el flujo completo desde la tabla original hasta la tabla jerarquizada."""
    input_csv = find_input_csv()
    depurada_csv = resolve_output_path(OUTPUT_NAME, input_csv)
    report_csv = resolve_output_path(REPORT_NAME, input_csv)
    audit_csv = resolve_output_path(AUDIT_REPORT_NAME, input_csv)

    print("Entrada original:", input_csv)

    build_tabla_depurada()

    output_table, output_dict, output_summary = write_hierarchy_files(depurada_csv)

    print("Tabla depurada final:", depurada_csv)
    print("Tabla jerarquizada final:", output_table)
    print("Diccionario de jerarquía:", output_dict)
    print("Resumen por bloques:", output_summary)
    print("Reporte de correlaciones y redundancias:", report_csv)
    print("Reporte de auditoría:", audit_csv)


if __name__ == "__main__":
    main()
