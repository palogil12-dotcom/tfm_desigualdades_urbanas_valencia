from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd


INPUT_NAME = "tabla_por_distritos_limpia.csv"
REPORT_NAME = "reporte_correlaciones.csv"
VERSION_REPORT_GLOB = "reporte_redundancias_correlaciones_v*.csv"


# ---------------------------------------------------------------------------
# Lista editable de comprobaciones
# ---------------------------------------------------------------------------
# Este script está pensado como apoyo manual a la toma de decisiones.
# Para reutilizarlo basta con cambiar los nombres de las columnas en las listas
# PAIR_CHECKS o SHARE_CHECKS y volver a ejecutarlo.

PAIR_CHECKS = [
    {
        "bloque": "Hechos discriminatorios",
        "variable_1": "Hechos discriminatorios - Genero [n]",
        "variable_2": "Hechos discriminatorios - LGTBIFobia [n]",
        "decision_metodologica": "Fusionadas como discriminacion por sexo-genero y diversidad sexual.",
    },
    {
        "bloque": "Medio ambiente",
        "variable_1": "Contaminacion - PM10(µg/m³) [media]",
        "variable_2": "Contaminacion - PM2.5(µg/m³) [media]",
        "decision_metodologica": "PM10 y PM2.5 se integran en un indice estandarizado de particulas.",
    },
    {
        "bloque": "Medio ambiente",
        "variable_1": "Contaminacion - NO(µg/m³) [media]",
        "variable_2": "Contaminacion - NOx(µg/m³) [media]",
        "decision_metodologica": "NO, NO2 y NOx son muy redundantes; se conserva NO2 como indicador mas interpretable de trafico urbano.",
    },
    {
        "bloque": "Medio ambiente",
        "variable_1": "Contaminacion - NO2(µg/m³) [media]",
        "variable_2": "Contaminacion - NOx(µg/m³) [media]",
        "decision_metodologica": "NOx se elimina por redundancia con NO2.",
    },
    {
        "bloque": "Movilidad",
        "variable_1": "Edat mitjana dels turismes particulars [2025]",
        "variable_2": "Percentatge de turismes particulars de 10 i més anys [2025]",
        "decision_metodologica": "Se conserva la edad media de los turismos y se elimina el porcentaje de turismos de 10 o mas anos.",
    },
    {
        "bloque": "Educacion - titulacion",
        "variable_1": "Padron 2025 titulacion 18+ | Bachiller FP2 o superior [%]",
        "variable_2": "Educacion superior [% distrito, mayores 15, censo 2022]",
        "decision_metodologica": "Se conserva Padron 2025 en porcentajes y se eliminan indicadores de censo 2022 por solapamiento temporal y conceptual.",
    },
    {
        "bloque": "Educacion - PAU",
        "variable_1": "Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Alumnado matriculado",
        "variable_2": "Educacion | Resultados de Bachillerato y notas PAU por distrito. Curso 202425 | Alumnado presentado",
        "decision_metodologica": "No se conserva el recuento absoluto de presentados; se transforma en porcentaje sobre alumnado matriculado.",
    },
    {
        "bloque": "Economia",
        "variable_1": "INE - Renta media por persona [EUR distrito]",
        "variable_2": "INE - Renta media por hogar [EUR distrito]",
        "decision_metodologica": "Rentas por persona y por hogar presentan solapamiento; se conserva renta por persona como indicador principal.",
    },
    {
        "bloque": "Economia",
        "variable_1": "INE - Renta media por persona [EUR distrito]",
        "variable_2": "INE - Media renta por unidad de consumo [EUR distrito]",
        "decision_metodologica": "Las distintas medidas medias de renta son muy proximas; se conserva renta por persona y mediana por unidad de consumo.",
    },
    {
        "bloque": "Economia",
        "variable_1": "INE 2023 desigualdad | Índice de Gini [distrito]",
        "variable_2": "INE 2023 desigualdad | Distribución de la renta P80/P20 [distrito]",
        "decision_metodologica": "Gini y P80/P20 miden desigualdad; se conserva Gini como indicador sintetico.",
    },
    {
        "bloque": "Urbanismo e infraestructuras",
        "variable_1": "Edificacion vivienda 2025 parcelas urbanas | Total [n]",
        "variable_2": "Edificacion vivienda 2025 solares | Numero [n]",
        "decision_metodologica": "Parcelas urbanas y solares son casi equivalentes en estos datos; se evita duplicar recuentos.",
    },
]


SHARE_CHECKS = [
    {
        "bloque": "Policia local",
        "componentes": [
            "Recursos municipales 2024 policia local | Servicios trafico [n]",
            "Recursos municipales 2024 policia local | Seguridad ciudadana [n]",
            "Recursos municipales 2024 policia local | Vigilancias [n]",
            "Recursos municipales 2024 policia local | Policia administrativa [n]",
            "Recursos municipales 2024 policia local | Actos via publica [n]",
            "Recursos municipales 2024 policia local | Informacion [n]",
            "Recursos municipales 2024 policia local | Incidencias [n]",
            "Recursos municipales 2024 policia local | Humanitarios y riesgos [n]",
        ],
        "etiquetas": [
            "Servicios trafico",
            "Seguridad ciudadana",
            "Vigilancias",
            "Policia administrativa",
            "Actos via publica",
            "Informacion",
            "Incidencias",
            "Humanitarios y riesgos",
        ],
        "decision_metodologica": "Agrupacion de subtipos en cuatro bloques funcionales por cada 1.000 habitantes.",
    },
    {
        "bloque": "Bomberos",
        "componentes": [
            "Recursos municipales 2024 bomberos | Salvamentos [n]",
            "Recursos municipales 2024 bomberos | Asistencia tecnica [n]",
            "Recursos municipales 2024 bomberos | Incendios [n]",
            "Recursos municipales 2024 bomberos | Falsas alarmas [n]",
            "Recursos municipales 2024 bomberos | Mercancias peligrosas [n]",
        ],
        "etiquetas": [
            "Salvamentos",
            "Asistencia tecnica",
            "Incendios",
            "Falsas alarmas",
            "Mercancias peligrosas",
        ],
        "decision_metodologica": "Agrupacion en rescate/asistencia e incendios/alertas de riesgo.",
    },
]


STANDARD_COLUMNS = [
    "version",
    "archivo_origen",
    "formato_origen",
    "fila_origen",
    "bloque",
    "tipo_medida",
    "variable_1",
    "variable_2",
    "valor",
    "n_observaciones",
    "decision_metodologica",
    "decision",
    "criterio",
    "medida",
]


def find_input_csv() -> Path:
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

    raise FileNotFoundError(f"No se encontro {INPUT_NAME}")


def resolve_output_path(filename: str) -> Path:
    return Path(__file__).resolve().parent / filename


def find_version_reports_dir() -> Path | None:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "Resultados" / "resultados chatgp",
        script_dir.parent / "resultados" / "resultados chatgp",
        script_dir / "Resultados" / "resultados chatgp",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def parse_es_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def resolve_column(columns_by_norm: dict[str, str], column_name: str) -> str:
    normalized = normalize_text(column_name)
    if normalized in columns_by_norm:
        return columns_by_norm[normalized]
    raise KeyError(f"No se encontro la columna: {column_name}")


def format_es(value: float | None) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{float(value):.3f}".replace(".", ",")


def safe_num(value: float | None) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(value)


def build_current_report(df: pd.DataFrame) -> pd.DataFrame:
    non_category_mask = df["codigo"].astype(str) != "__categoria__"
    columns_by_norm = {normalize_text(col): col for col in df.columns}
    rows: list[dict[str, str]] = []

    for check in PAIR_CHECKS:
        col1 = resolve_column(columns_by_norm, check["variable_1"])
        col2 = resolve_column(columns_by_norm, check["variable_2"])
        pair_df = df.loc[non_category_mask, [col1, col2]].copy()
        pair_df[col1] = pair_df[col1].apply(parse_es_number)
        pair_df[col2] = pair_df[col2].apply(parse_es_number)
        pair_df = pair_df.dropna()

        corr = None if len(pair_df) < 2 else float(pair_df[col1].corr(pair_df[col2]))
        rows.append(
            {
                "bloque": check["bloque"],
                "tipo_medida": "correlacion_pearson",
                "variable_1": col1,
                "variable_2": col2,
                "valor": format_es(corr),
                "n_observaciones": str(len(pair_df)),
                "decision_metodologica": check["decision_metodologica"],
                "decision": "",
                "criterio": "",
            }
        )

    for check in SHARE_CHECKS:
        component_cols = [resolve_column(columns_by_norm, col) for col in check["componentes"]]
        labels = check["etiquetas"]
        totals = [safe_num(df.loc[non_category_mask, col].apply(parse_es_number).sum()) for col in component_cols]
        grand_total = sum(totals)

        for label, total_value in zip(labels, totals):
            share = None if grand_total == 0 else (total_value / grand_total) * 100.0
            rows.append(
                {
                    "bloque": check["bloque"],
                    "tipo_medida": "peso_sobre_total_ciudad_%",
                    "variable_1": label,
                    "variable_2": "total del bloque",
                    "valor": format_es(share),
                    "n_observaciones": str(int(non_category_mask.sum())),
                    "decision_metodologica": check["decision_metodologica"],
                    "decision": "",
                    "criterio": "",
                }
            )

    return pd.DataFrame(rows)


def extract_version(path: Path) -> int:
    match = re.search(r"_v(\d+)\.csv$", path.name)
    if not match:
        raise ValueError(f"No se pudo extraer la version de {path.name}")
    return int(match.group(1))


def normalize_version_report(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).fillna("")
    format_type = "detallado" if {"tipo_medida", "variable_1", "variable_2"}.issubset(df.columns) else "resumido"

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["version"] = extract_version(path)
    df["archivo_origen"] = path.name
    df["formato_origen"] = format_type
    df["fila_origen"] = range(1, len(df) + 1)

    return df[STANDARD_COLUMNS]


def build_historical_report() -> pd.DataFrame:
    reports_dir = find_version_reports_dir()
    if reports_dir is None:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    files = sorted(reports_dir.glob(VERSION_REPORT_GLOB), key=extract_version)
    if not files:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    frames = [normalize_version_report(path) for path in files]
    combined = pd.concat(frames, ignore_index=True)
    corr_mask = combined["tipo_medida"].str.contains("correlacion", case=False, na=False)
    return combined[corr_mask].copy()


def standardize_current_report(current_report: pd.DataFrame) -> pd.DataFrame:
    df = current_report.copy()
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["version"] = "manual_actual"
    df["archivo_origen"] = "correlaciones.py"
    df["formato_origen"] = "manual_actual"
    df["fila_origen"] = range(1, len(df) + 1)

    return df[STANDARD_COLUMNS]


def main() -> None:
    input_csv = find_input_csv()
    df = pd.read_csv(input_csv, encoding="utf-8", dtype=str)

    current_report = build_current_report(df)
    historical_report = build_historical_report()
    final_report = pd.concat(
        [historical_report, standardize_current_report(current_report)],
        ignore_index=True,
    )
    report_path = resolve_output_path(REPORT_NAME)
    final_report.to_csv(report_path, index=False, encoding="utf-8")

    print("Entrada original:", input_csv)
    print("Reporte de correlaciones:", report_path)
    print("Filas historicas incorporadas:", len(historical_report))
    print("Filas manuales actuales:", len(current_report))
    print("Filas totales:", len(final_report))
    print("Nota: para reutilizar este script, cambia los nombres en PAIR_CHECKS y SHARE_CHECKS.")


if __name__ == "__main__":
    main()
