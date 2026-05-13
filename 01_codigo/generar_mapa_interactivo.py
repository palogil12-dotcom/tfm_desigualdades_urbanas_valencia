from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SOURCE_DIR = PROJECT_ROOT / "Resultados" / "resultados chatgp"
INPUT_CSV = SOURCE_DIR / "tabla_por_distritos_limpia_derivada_integrada_v31.csv"
HIERARCHY_CSV = SOURCE_DIR / "diccionario_jerarquia_variables_v32.csv"
KMZ_PATH = PROJECT_ROOT / "Urbanismo" / "distritos.geojson"
HTML_OUTPUT = SCRIPT_DIR / "mapa_interactivo_distritos_v31_jerarquizado.html"


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    text = text.replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", text):
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def load_table() -> tuple[dict[str, str], list[dict[str, str]]]:
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    category_row = next((row for row in rows if row.get("codigo") == "__categoria__"), {})
    district_rows = [row for row in rows if row.get("codigo") and row["codigo"] != "__categoria__"]
    return category_row, district_rows


def load_hierarchy() -> dict[str, dict[str, str]]:
    with HIERARCHY_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return {row["variable"]: row for row in reader}


def infer_numeric_variables(rows: list[dict[str, str]], ordered_columns: list[str]) -> list[str]:
    numeric: list[str] = []
    for column in ordered_columns:
        if column in {"codigo", "nombre"}:
            continue
        if any(parse_number(row.get(column)) is not None for row in rows):
            numeric.append(column)
    return numeric


def load_kml_from_kmz(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as archive:
        for member in archive.namelist():
            if member.lower().endswith("doc.kml"):
                return archive.read(member).decode("utf-8")
    raise FileNotFoundError("No se encontró doc.kml dentro del fichero territorial de distritos.")


def strip_html(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text or "").split())


def extract_district_code(description: str) -> str | None:
    clean = strip_html(description)
    patterns = [
        r"C(?:Ã³|o|ÃƒÂ³)digo distrito\s+(\d+)",
        r"C\S*digo distrito\s+(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, re.IGNORECASE)
        if match:
            return str(int(match.group(1)))
    return None


def parse_coordinates(text: str) -> list[list[float]]:
    points: list[list[float]] = []
    for chunk in text.strip().split():
        parts = chunk.split(",")
        if len(parts) < 2:
            continue
        try:
            lon = float(parts[0])
            lat = float(parts[1])
        except ValueError:
            continue
        points.append([lon, lat])

    if points and points[0] != points[-1]:
        points.append(points[0])
    return points


def build_geojson_from_kmz(path: Path) -> dict:
    kml_text = load_kml_from_kmz(path)
    root = ET.fromstring(kml_text)
    placemarks = root.findall(".//{*}Placemark")

    grouped: OrderedDict[str, dict[str, object]] = OrderedDict()

    for placemark in placemarks:
        name = (placemark.findtext("{*}name") or "").strip()
        description = placemark.findtext("{*}description") or ""
        code = extract_district_code(description)
        if not code:
            continue

        polygons: list[list[list[float]]] = []
        for polygon in placemark.findall(".//{*}Polygon"):
            coord_text = polygon.findtext(".//{*}outerBoundaryIs/{*}LinearRing/{*}coordinates")
            if not coord_text:
                continue
            ring = parse_coordinates(coord_text)
            if ring:
                polygons.append(ring)

        if not polygons:
            continue

        if code not in grouped:
            grouped[code] = {"code": code, "name": name, "polygons": []}

        grouped[code]["polygons"].extend(polygons)

    features = []
    for code, item in grouped.items():
        polygons = item["polygons"]
        if len(polygons) == 1:
            geometry = {"type": "Polygon", "coordinates": [polygons[0]]}
        else:
            geometry = {
                "type": "MultiPolygon",
                "coordinates": [[[point for point in ring]] for ring in polygons],
            }

        features.append(
            {
                "type": "Feature",
                "properties": {"codigo": code, "nombre": item["name"]},
                "geometry": geometry,
            }
        )

    return {"type": "FeatureCollection", "features": features}


def compute_bounds(geojson: dict) -> list[list[float]]:
    min_lon = float("inf")
    min_lat = float("inf")
    max_lon = float("-inf")
    max_lat = float("-inf")

    def walk(node):
        if isinstance(node[0], (float, int)):
            yield node
        else:
            for child in node:
                yield from walk(child)

    for feature in geojson["features"]:
        for point in walk(feature["geometry"]["coordinates"]):
            lon, lat = point[0], point[1]
            min_lon = min(min_lon, lon)
            min_lat = min(min_lat, lat)
            max_lon = max(max_lon, lon)
            max_lat = max(max_lat, lat)

    return [[min_lat, min_lon], [max_lat, max_lon]]


def build_variable_metadata(
    columns: list[str],
    numeric_variables: list[str],
    category_row: dict[str, str],
    hierarchy: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    numeric_set = set(numeric_variables)
    metadata: list[dict[str, str]] = []

    for column in columns:
        if column not in numeric_set:
            continue
        row = hierarchy.get(column, {})
        metadata.append(
            {
                "variable": column,
                "categoria_original": category_row.get(column, "Sin categoria"),
                "bloque_tematico": row.get("bloque_tematico", category_row.get(column, "Sin bloque")),
                "subdimension": row.get("subdimension", "Sin subdimension"),
                "rol_analisis": row.get("rol_analisis", "Sin jerarquia"),
                "nota_uso": row.get("nota_uso", ""),
            }
        )

    return metadata


def build_html(
    rows: list[dict[str, str]],
    variable_metadata: list[dict[str, str]],
    district_geojson: dict,
    initial_bounds: list[list[float]],
) -> str:
    data_json = json.dumps(rows, ensure_ascii=False)
    variables_json = json.dumps(variable_metadata, ensure_ascii=False)
    geojson_json = json.dumps(district_geojson, ensure_ascii=False)
    bounds_json = json.dumps(initial_bounds, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Valencia por distritos</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    :root {{
      --bg: #f7f6f2;
      --panel: rgba(255, 255, 255, 0.96);
      --ink: #24313a;
      --muted: #69757e;
      --line: #d7ddd7;
      --shadow: 0 18px 40px rgba(40, 56, 64, 0.14);
      --teal: #1a6d67;
      --teal-soft: #dfeeea;
    }}

    * {{
      box-sizing: border-box;
    }}

    html, body {{
      height: 100%;
    }}

    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background: var(--bg);
    }}

    .page {{
      position: relative;
      min-height: 100vh;
      isolation: isolate;
      background:
        radial-gradient(circle at top left, rgba(230, 239, 236, 0.82), transparent 30%),
        linear-gradient(180deg, #edf1ee 0%, #f4f1ea 100%);
    }}

    .sidebar {{
      position: absolute;
      top: 14px;
      left: 14px;
      z-index: 900;
      width: min(344px, calc(100vw - 28px));
      pointer-events: none;
    }}

    .panel {{
      max-height: calc(100vh - 28px);
      overflow-y: auto;
      overflow-x: hidden;
      padding: 22px 22px 20px;
      background: rgba(255, 252, 247, 0.91);
      border-radius: 24px;
      border: 1px solid rgba(219, 225, 219, 0.92);
      box-shadow: 0 24px 46px rgba(36, 54, 57, 0.17);
      backdrop-filter: blur(10px);
      pointer-events: auto;
      scrollbar-width: thin;
      scrollbar-color: rgba(118, 130, 132, 0.72) transparent;
    }}

    .panel::-webkit-scrollbar {{
      width: 10px;
    }}

    .panel::-webkit-scrollbar-track {{
      background: transparent;
    }}

    .panel::-webkit-scrollbar-thumb {{
      background: rgba(118, 130, 132, 0.68);
      border-radius: 999px;
      border: 2px solid transparent;
      background-clip: padding-box;
    }}

    h1 {{
      margin: 0 0 12px 0;
      font-size: clamp(2rem, 4vw, 2.7rem);
      line-height: 0.96;
      letter-spacing: 0.01em;
    }}

    p {{
      margin: 0 0 14px 0;
      color: var(--muted);
      line-height: 1.45;
      font-size: 0.97rem;
    }}

    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 18px 0 18px;
    }}

    .chip {{
      border: 1px solid #bfd5ce;
      background: #f8fcfb;
      color: #135f58;
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 0.9rem;
    }}

    .controls {{
      display: grid;
      gap: 14px;
    }}

    label {{
      display: block;
      margin-bottom: 6px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #54626c;
    }}

    select, input {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid #d7dcd6;
      background: #fffdfa;
      color: var(--ink);
      font: inherit;
    }}

    input::placeholder {{
      color: #7b858c;
    }}

    .meta {{
      margin-top: 18px;
      display: grid;
      gap: 10px;
    }}

    .meta-card {{
      padding: 14px 15px;
      border-radius: 16px;
      background: #f6f7f3;
      border: 1px solid #e1e4dd;
    }}

    .meta-k {{
      display: block;
      margin-bottom: 4px;
      font-size: 0.73rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #5f6d77;
    }}

    .meta-v {{
      font-size: 0.97rem;
      line-height: 1.35;
    }}

    .stats {{
      margin-top: 16px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}

    .stat {{
      padding: 14px;
      border-radius: 16px;
      background: rgba(243, 240, 233, 0.95);
      border: 1px solid #ece5d8;
    }}

    .stat .k {{
      display: block;
      margin-bottom: 6px;
      font-size: 0.73rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #606b73;
    }}

    .stat .v {{
      font-size: 1.08rem;
      font-weight: 700;
    }}

    .map-wrap {{
      position: relative;
      width: 100%;
      min-height: 100vh;
      background: #e8edeb;
    }}

    #map {{
      width: 100%;
      height: 100vh;
    }}

    .legend {{
      position: absolute;
      right: 16px;
      bottom: 16px;
      z-index: 700;
      background: rgba(255, 255, 255, 0.94);
      border-radius: 18px;
      padding: 14px 16px;
      border: 1px solid rgba(214, 220, 215, 0.96);
      box-shadow: 0 18px 40px rgba(38, 53, 59, 0.16);
      min-width: 210px;
      max-width: min(280px, calc(100vw - 32px));
    }}

    .legend-title {{
      margin-bottom: 10px;
      font-size: 0.9rem;
      font-weight: 700;
      line-height: 1.3;
    }}

    .legend-bar {{
      height: 14px;
      border-radius: 999px;
      background: linear-gradient(90deg, rgb(224,241,234) 0%, rgb(101,187,169) 50%, rgb(18,101,98) 100%);
      border: 1px solid rgba(0,0,0,0.08);
    }}

    .legend-range {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      margin-top: 8px;
      font-size: 0.82rem;
      color: #57636c;
    }}

    .leaflet-popup-content-wrapper {{
      border-radius: 16px;
      font-family: Georgia, "Times New Roman", serif;
    }}

    .popup-title {{
      margin-bottom: 4px;
      font-weight: 700;
      font-size: 1rem;
    }}

    .popup-value {{
      color: #41515b;
      line-height: 1.35;
    }}

    @media (max-width: 520px) {{
      .sidebar {{
        position: static;
        width: auto;
        padding: 12px 12px 0;
      }}

      .panel {{
        max-height: none;
      }}

      #map {{
        height: 72vh;
      }}

      .legend {{
        right: 12px;
        left: 12px;
        min-width: 0;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <main class="map-wrap">
      <div id="map"></div>
      <div class="legend">
        <div class="legend-title" id="legendTitle">Variable</div>
        <div class="legend-bar"></div>
        <div class="legend-range">
          <span id="legendMin">-</span>
          <span id="legendMax">-</span>
        </div>
      </div>
    </main>

    <aside class="sidebar">
      <div class="panel">
        <h1>Valencia por distritos</h1>
        <p>
          Explorador interactivo construido sobre
          <strong>tabla_por_distritos_limpia_derivada_integrada_v31.csv</strong>,
          enlazada con la jerarquización de variables de la
          <strong>v32</strong>.
        </p>
        <p>
          Filtra por categoría original, rol analítico o busca una variable concreta
          para ver cómo se distribuye espacialmente.
        </p>

        <div class="chips">
          <div class="chip">19 distritos</div>
          <div class="chip">{len(variable_metadata)} variables numéricas</div>
        </div>

        <div class="controls">
          <div>
            <label for="categorySelect">Categoría</label>
            <select id="categorySelect"></select>
          </div>
          <div>
            <label for="roleSelect">Jerarquía</label>
            <select id="roleSelect"></select>
          </div>
          <div>
            <label for="searchBox">Buscar variable</label>
            <input id="searchBox" type="text" placeholder="Ej. renta, vivienda, pobreza, turismo" />
          </div>
          <div>
            <label for="variableSelect">Variable</label>
            <select id="variableSelect"></select>
          </div>
        </div>

        <div class="meta">
          <div class="meta-card">
            <span class="meta-k">Variable seleccionada</span>
            <div class="meta-v" id="metaTitle">-</div>
          </div>
          <div class="meta-card">
            <span class="meta-k">Categoría original</span>
            <div class="meta-v" id="metaCategory">-</div>
          </div>
          <div class="meta-card">
            <span class="meta-k">Bloque temático</span>
            <div class="meta-v" id="metaBlock">-</div>
          </div>
          <div class="meta-card">
            <span class="meta-k">Subdimensión</span>
            <div class="meta-v" id="metaSubdimension">-</div>
          </div>
          <div class="meta-card">
            <span class="meta-k">Jerarquía</span>
            <div class="meta-v" id="metaRole">-</div>
          </div>
          <div class="meta-card">
            <span class="meta-k">Nota de uso</span>
            <div class="meta-v" id="metaNote">-</div>
          </div>
        </div>

        <div class="stats">
          <div class="stat"><span class="k">Mínimo</span><span class="v" id="statMin">-</span></div>
          <div class="stat"><span class="k">Máximo</span><span class="v" id="statMax">-</span></div>
          <div class="stat"><span class="k">Media</span><span class="v" id="statMean">-</span></div>
          <div class="stat"><span class="k">Distritos con dato</span><span class="v" id="statCount">-</span></div>
        </div>
      </div>
    </aside>
  </div>

  <script id="district-data" type="application/json">{data_json}</script>
  <script id="variable-metadata" type="application/json">{variables_json}</script>
  <script id="district-geojson" type="application/json">{geojson_json}</script>
  <script id="initial-bounds" type="application/json">{bounds_json}</script>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const rows = JSON.parse(document.getElementById("district-data").textContent);
    const variables = JSON.parse(document.getElementById("variable-metadata").textContent);
    const geojson = JSON.parse(document.getElementById("district-geojson").textContent);
    const initialBounds = JSON.parse(document.getElementById("initial-bounds").textContent);

    const rowByCode = new Map(rows.map((row) => [String(row.codigo).trim(), row]));
    const variableByName = new Map(variables.map((row) => [row.variable, row]));

    const categorySelect = document.getElementById("categorySelect");
    const roleSelect = document.getElementById("roleSelect");
    const searchBox = document.getElementById("searchBox");
    const variableSelect = document.getElementById("variableSelect");
    const metaTitle = document.getElementById("metaTitle");
    const metaCategory = document.getElementById("metaCategory");
    const metaBlock = document.getElementById("metaBlock");
    const metaSubdimension = document.getElementById("metaSubdimension");
    const metaRole = document.getElementById("metaRole");
    const metaNote = document.getElementById("metaNote");
    const statMin = document.getElementById("statMin");
    const statMax = document.getElementById("statMax");
    const statMean = document.getElementById("statMean");
    const statCount = document.getElementById("statCount");
    const legendTitle = document.getElementById("legendTitle");
    const legendMin = document.getElementById("legendMin");
    const legendMax = document.getElementById("legendMax");

    function parseNumber(value) {{
      if (value === null || value === undefined) return null;
      let text = String(value).trim();
      if (!text) return null;
      text = text.replace(/\\s+/g, "");

      if (text.includes(",") && text.includes(".")) {{
        text = text.replace(/\\./g, "").replace(",", ".");
      }} else if (text.includes(",")) {{
        text = text.replace(",", ".");
      }} else if (/^-?\\d{{1,3}}(?:\\.\\d{{3}})+$/.test(text)) {{
        text = text.replace(/\\./g, "");
      }}

      const numeric = Number(text);
      return Number.isFinite(numeric) ? numeric : null;
    }}

    function formatNumber(value) {{
      if (!Number.isFinite(value)) return "-";
      return value.toLocaleString("es-ES", {{
        maximumFractionDigits: 2,
        minimumFractionDigits: value % 1 === 0 ? 0 : 2
      }});
    }}

    function getExtent(values) {{
      const finite = values.filter(Number.isFinite);
      if (!finite.length) return [null, null];
      return [Math.min(...finite), Math.max(...finite)];
    }}

    function interpolateColor(t) {{
      const clamp = Math.max(0, Math.min(1, t));
      const stops = [
        [224, 241, 234],
        [101, 187, 169],
        [18, 101, 98]
      ];

      const scaled = clamp * (stops.length - 1);
      const i = Math.floor(scaled);
      const frac = scaled - i;
      const a = stops[i];
      const b = stops[Math.min(i + 1, stops.length - 1)];
      const rgb = a.map((value, index) => Math.round(value + (b[index] - value) * frac));
      return `rgb(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}})`;
    }}

    function populateSelect(select, values, labelAll) {{
      const current = select.value;
      select.innerHTML = "";

      const allOption = document.createElement("option");
      allOption.value = "Todas";
      allOption.textContent = `${{labelAll}} (${{values.length}})`;
      select.appendChild(allOption);

      values.forEach((value) => {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
      }});

      if ([...select.options].some((opt) => opt.value === current)) {{
        select.value = current;
      }} else {{
        select.value = "Todas";
      }}
    }}

    function populateCategorySelect() {{
      const categories = [...new Set(variables.map((item) => item.categoria_original || "Sin categoria"))]
        .sort((a, b) => a.localeCompare(b, "es"));
      populateSelect(categorySelect, categories, "Todas");
    }}

    function populateRoleSelect() {{
      const roles = [...new Set(variables.map((item) => item.rol_analisis || "Sin jerarquia"))]
        .sort((a, b) => a.localeCompare(b, "es"));
      populateSelect(roleSelect, roles, "Todas");
    }}

    function getFilteredVariables() {{
      const selectedCategory = categorySelect.value;
      const selectedRole = roleSelect.value;
      const search = searchBox.value.trim().toLowerCase();

      return variables.filter((item) => {{
        const categoryOk = selectedCategory === "Todas" || item.categoria_original === selectedCategory;
        const roleOk = selectedRole === "Todas" || item.rol_analisis === selectedRole;
        const searchOk = !search || item.variable.toLowerCase().includes(search);
        return categoryOk && roleOk && searchOk;
      }});
    }}

    function populateVariableSelect() {{
      const previous = variableSelect.value;
      const filtered = getFilteredVariables();

      if (!filtered.length) {{
        variableSelect.innerHTML = '<option value="">No hay variables con ese filtro</option>';
        updateMetadata("");
        updateLayer("");
        return;
      }}

      variableSelect.innerHTML = filtered
        .map((item) => `<option value="${{item.variable}}">${{item.variable}}</option>`)
        .join("");

      const keepPrevious = filtered.some((item) => item.variable === previous);
      variableSelect.value = keepPrevious ? previous : filtered[0].variable;
      updateMetadata(variableSelect.value);
      updateLayer(variableSelect.value);
    }}

    function updateMetadata(variableName) {{
      if (!variableName) {{
        metaTitle.textContent = "No hay variables con ese filtro";
        metaCategory.textContent = "-";
        metaBlock.textContent = "-";
        metaSubdimension.textContent = "-";
        metaRole.textContent = "-";
        metaNote.textContent = "-";
        legendTitle.textContent = "Variable";
        return;
      }}

      const meta = variableByName.get(variableName);
      metaTitle.textContent = variableName;
      metaCategory.textContent = meta?.categoria_original || "-";
      metaBlock.textContent = meta?.bloque_tematico || "-";
      metaSubdimension.textContent = meta?.subdimension || "-";
      metaRole.textContent = meta?.rol_analisis || "-";
      metaNote.textContent = meta?.nota_uso || "-";
      legendTitle.textContent = variableName;
    }}

    const map = L.map("map", {{
      zoomControl: false,
      attributionControl: false,
      preferCanvas: true
    }});

    L.tileLayer("https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png", {{
      subdomains: "abcd",
      maxZoom: 20
    }}).addTo(map);

    L.control.zoom({{ position: "topright" }}).addTo(map);

    map.fitBounds(initialBounds, {{ padding: [24, 24] }});
    map.createPane("districts");
    map.getPane("districts").style.zIndex = 450;

    let geoLayer = null;

    function updateLayer(variableName) {{
      if (geoLayer) {{
        map.removeLayer(geoLayer);
        geoLayer = null;
      }}

      if (!variableName) {{
        statMin.textContent = "-";
        statMax.textContent = "-";
        statMean.textContent = "-";
        statCount.textContent = "-";
        legendMin.textContent = "-";
        legendMax.textContent = "-";
        return;
      }}

      const values = geojson.features.map((feature) => {{
        const row = rowByCode.get(String(feature.properties.codigo));
        return parseNumber(row ? row[variableName] : null);
      }});

      const [min, max] = getExtent(values);
      const finite = values.filter(Number.isFinite);
      const mean = finite.length ? finite.reduce((a, b) => a + b, 0) / finite.length : null;

      statMin.textContent = formatNumber(min);
      statMax.textContent = formatNumber(max);
      statMean.textContent = formatNumber(mean);
      statCount.textContent = String(finite.length);
      legendMin.textContent = formatNumber(min);
      legendMax.textContent = formatNumber(max);

      geoLayer = L.geoJSON(geojson, {{
        pane: "districts",
        style: (feature) => {{
          const row = rowByCode.get(String(feature.properties.codigo));
          const value = parseNumber(row ? row[variableName] : null);
          const ratio = min === null || max === null || max === min || value === null
            ? 0.5
            : (value - min) / (max - min);

          return {{
            color: "#ffffff",
            weight: 2.8,
            fillColor: value === null ? "#dce4de" : interpolateColor(ratio),
            fillOpacity: value === null ? 0.52 : 0.88
          }};
        }},
        onEachFeature: (feature, layer) => {{
          const row = rowByCode.get(String(feature.properties.codigo));
          const value = parseNumber(row ? row[variableName] : null);
          const districtName = row && row.nombre ? row.nombre : feature.properties.nombre;

          layer.bindPopup(`
            <div class="popup-title">${{districtName}}</div>
            <div class="popup-value">${{variableName}}: <strong>${{formatNumber(value)}}</strong></div>
          `);

          layer.on({{
            mouseover: () => layer.setStyle({{ weight: 4.0, fillOpacity: 0.96 }}),
            mouseout: () => geoLayer.resetStyle(layer)
          }});
        }}
      }}).addTo(map);
    }}

    categorySelect.addEventListener("change", populateVariableSelect);
    roleSelect.addEventListener("change", populateVariableSelect);
    searchBox.addEventListener("input", populateVariableSelect);
    variableSelect.addEventListener("change", () => {{
      updateMetadata(variableSelect.value);
      updateLayer(variableSelect.value);
    }});

    populateCategorySelect();
    populateRoleSelect();
    populateVariableSelect();
  </script>
</body>
</html>
"""


def main() -> None:
    category_row, rows = load_table()
    hierarchy = load_hierarchy()
    ordered_columns = list(category_row.keys()) if category_row else list(rows[0].keys())
    numeric_variables = infer_numeric_variables(rows, ordered_columns)
    variable_metadata = build_variable_metadata(ordered_columns, numeric_variables, category_row, hierarchy)
    district_geojson = build_geojson_from_kmz(KMZ_PATH)
    initial_bounds = compute_bounds(district_geojson)

    HTML_OUTPUT.write_text(
        build_html(rows, variable_metadata, district_geojson, initial_bounds),
        encoding="utf-8",
    )

    print(f"Filas de distritos: {len(rows)}")
    print(f"Variables numericas: {len(variable_metadata)}")
    print(f"Geometrias de distrito: {len(district_geojson['features'])}")
    print(f"Mapa interactivo: {HTML_OUTPUT}")


if __name__ == "__main__":
    main()
