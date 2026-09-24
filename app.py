"""
Río Negro: una provincia, territorios distintos
Exploración interactiva de datos abiertos — Concurso "Contar con Datos 2026"

Cómo correr localmente:
    pip install -r requirements.txt
    streamlit run app.py

Estructura esperada de datos (carpeta data/):
    - tabla_maestra.csv         -> una fila por departamento, ya viene con datos de ejemplo
    - rio_negro_departamentos.geojson -> capa de departamentos del IGN (agregarla vos, ver README.md)
"""

import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Río Negro: una provincia, territorios distintos",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Estilo visual (tipografía, paleta, componentes)
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #FBF9F5 !important;
}
[data-testid="stHeader"] {
    background-color: transparent !important;
}

h1, h2, h3 {
    font-family: 'Fraunces', serif !important;
    letter-spacing: -0.01em;
}

.hero-title {
    font-family: 'Fraunces', serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #2B2B26;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}
.hero-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 1.05rem;
    color: #6B6558;
    margin-bottom: 1.4rem;
}
.region-chip {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 6px;
    color: white;
}
.chip-andina { background-color: #2F5D45; }
.chip-linea-sur { background-color: #B5793A; }
.chip-valle { background-color: #4C8C5B; }
.chip-costa { background-color: #2A5C7A; }

[data-testid="stMetric"] {
    background-color: #F0EBE1;
    border-radius: 10px;
    padding: 10px 14px;
    border-left: 4px solid #C77B3F;
}
[data-testid="stMetricLabel"] {
    font-size: 0.8rem;
    color: #6B6558;
}

[data-testid="stExpander"] {
    background-color: #FBF9F5;
    border: 1px solid #E3DBCB;
    border-radius: 10px;
}
[data-testid="stExpander"] summary {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    color: #2B2B26;
}

div[data-testid="stButton"] > button {
    border-radius: 999px;
    border: none;
    background-color: #F0EBE1;
    color: #2B2B26;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 6px 4px;
}
div[data-testid="stButton"] > button:hover {
    background-color: #C77B3F;
    color: white;
}
div[data-testid="stButton"] > button:focus:not(:active) {
    border-color: #C77B3F;
    color: #2B2B26;
}

section[data-testid="stSidebar"] {
    background-color: #F0EBE1;
    border-right: 3px solid #C77B3F;
}
section[data-testid="stSidebar"] .hero-title,
section[data-testid="stSidebar"] h1 {
    color: #2B2B26 !important;
}
</style>
""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "tabla_maestra.csv")
GEOJSON_PATH = os.path.join(DATA_DIR, "rio_negro_departamentos.geojson")

# Capas geográficas opcionales (IGN), recortadas al área de Río Negro. Si el archivo no está,
# la app simplemente no ofrece esa capa como opción (no rompe nada).
CAPAS_GEOGRAFICAS = {
    "rios": {"label": "Ríos principales", "file": "rios_principales_rn.geojson", "color": "#2A6F97", "tipo": "linea"},
    "canales": {"label": "Canales de riego", "file": "canales_rn.geojson", "color": "#4FA3C7", "tipo": "linea"},
    "embalses": {"label": "Embalses", "file": "embalses_rn.geojson", "color": "#1B4965", "tipo": "linea"},
    "ferrocarril": {"label": "Tren Patagónico (vías)", "file": "ferrocarril_rn.geojson", "color": "#6B6558", "tipo": "linea"},
    "estaciones_tren": {"label": "Estaciones de tren", "file": "estaciones_tren_rn.geojson", "color": "#6B6558", "tipo": "punto"},
    "vial_nacional": {"label": "Rutas nacionales", "file": "vial_nacional_rn.geojson", "color": "#C77B3F", "tipo": "linea"},
    "vial_provincial": {"label": "Rutas provinciales", "file": "vial_provincial_rn.geojson", "color": "#D9A05B", "tipo": "linea"},
    "mineria_puntos": {"label": "Registros mineros", "file": "mineria_puntos.geojson", "color": "#8B5E3C", "tipo": "punto"},
    "pozos_hidrocarburos": {"label": "Pozos de petróleo/gas activos", "file": "hidrocarburos_pozos_activos.geojson", "color": "#3B3B3B", "tipo": "punto"},
}

# Columna del GeoJSON que contiene el nombre del departamento.
# En la capa del IGN usada acá, la columna se llama "nam".
GEOJSON_NAME_FIELD = "nam"

# Indicadores disponibles para explorar en el mapa y la comparación (deben ser numéricos).
INDICADORES = {
    "Poblacion": "Población (habitantes)",
    "Densidad_hab_km2": "Densidad poblacional (hab/km²)",
    "Educ_secundaria_completa_pct": "Secundaria completa o más (%)",
    "Salud_solo_publico_pct": "Usa solo salud pública (%)",
    "Pob_65mas_pct": "Población de 65 años o más (%)",
    "Agricultura_superficie_implantada_ha": "Superficie agrícola implantada (ha)",
    "Agricultura_frutales_pct": "Superficie con frutales (%)",
    "Agricultura_forrajeras_pct": "Superficie con forrajeras (%)",
    "Agricultura_cereales_pct": "Superficie con cereales (%)",
    "Agricultura_bosques_pct": "Superficie con bosques/montes (%)",
    "Riego_superficie_regada_ha": "Superficie bajo riego (ha)",
    "Riego_pct_superficie_regada": "Superficie bajo riego (%)",
    "Riego_pct_eap_con_riego": "Productores (EAP) con riego (%)",
    "Ganaderia_cabezas_totales": "Cabezas de ganado (total)",
    "Ganaderia_bovinos": "Cabezas de bovinos",
    "Ganaderia_ovinos": "Cabezas de ovinos",
    "Ganaderia_caprinos": "Cabezas de caprinos",
    "Ganaderia_bovinos_pct": "Composición del rodeo: bovinos (%)",
    "Ganaderia_ovinos_pct": "Composición del rodeo: ovinos (%)",
    "Ganaderia_caprinos_pct": "Composición del rodeo: caprinos (%)",
    "Ganaderia_porcinos_pct": "Composición del rodeo: porcinos (%)",
    "Ganaderia_equinos_pct": "Composición del rodeo: equinos (%)",
    "Mineria_minas_formales_totales": "Minas formales registradas",
    "Mineria_minerales_diferentes": "Diversidad de minerales distintos",
    "Mineria_superficie_registrada_ha": "Superficie minera registrada (ha)",
    "Energia_MW_instalada": "Potencia eléctrica instalada (MW)",
    "Energia_MW_hidraulica": "Potencia hidráulica instalada (MW)",
    "Energia_MW_eolica": "Potencia eólica instalada (MW)",
    "Energia_MW_termica": "Potencia térmica instalada (MW)",
    "Hidrocarburos_pozos_totales": "Pozos de petróleo/gas (total)",
    "Hidrocarburos_pozos_extraccion_efectiva": "Pozos de petróleo/gas en extracción efectiva",
    "Hidrocarburos_prod_petroleo_m3_2025": "Producción de petróleo 2025 (m³)",
    "Hidrocarburos_prod_gas_miles_m3_2025": "Producción de gas 2025 (miles de m³)",
    "Turismo_localidades_con_alojamiento": "Localidades con alojamiento turístico registrado",
    "Turismo_destinos_destacados": "Destinos turísticos destacados (oficiales)",
    "Turismo_parques_nacionales": "Parques nacionales (Administración de Parques Nacionales)",
    "Turismo_areas_naturales_protegidas": "Áreas naturales protegidas (provinciales)",
    "Turismo_plazas_disponibles_oct2025": "Plazas turísticas disponibles (oct. 2025, INDEC)",
    "Turismo_pernoctaciones_oct2025": "Pernoctaciones (oct. 2025, INDEC)",
    "Turismo_tasa_ocupacion_pct": "Tasa de ocupación hotelera (%, oct. 2025, INDEC)",
    "Conectividad_aeropuertos": "Aeropuertos con código IATA",
    "Conectividad_estaciones_tren": "Estaciones del Tren Patagónico",
    "Industria_parques_industriales": "Parques industriales y tecnológicos",
    "Pesca_desembarque_toneladas_2025": "Desembarque pesquero 2025 (toneladas)",
}

# Campos que son porcentajes/tasas: para el resumen provincial se promedian (no se suman).
# Todo lo que no esté acá se trata como cantidad total y se suma.
CAMPOS_TASA = {
    "Educ_secundaria_completa_pct", "Salud_solo_publico_pct", "Pob_65mas_pct",
    "Agricultura_frutales_pct", "Agricultura_forrajeras_pct", "Agricultura_cereales_pct",
    "Agricultura_bosques_pct", "Riego_pct_superficie_regada", "Riego_pct_eap_con_riego",
    "Ganaderia_bovinos_pct", "Ganaderia_ovinos_pct", "Ganaderia_caprinos_pct",
    "Ganaderia_porcinos_pct", "Ganaderia_equinos_pct", "Turismo_tasa_ocupacion_pct",
}
SUPERFICIE_TOTAL_RN_KM2 = 203013  # fuente: Gobierno de Río Negro, rionegro.gov.ar/geografia

# Indicadores que NO cubren los 13 departamentos (solo destinos relevados por una fuente puntual).
# Se muestran igual, pero con una advertencia explícita para no sugerir comparabilidad provincial.
INDICADORES_COBERTURA_PARCIAL = {
    "Turismo_plazas_disponibles_oct2025": "Solo releva 3 de los 13 departamentos: Bariloche, "
        "San Antonio (destino Las Grutas) y Adolfo Alsina (destino Viedma), según la muestra de "
        "51 destinos turísticos de la Encuesta de Ocupación Hotelera del INDEC. El resto de los "
        "departamentos no forma parte de esa muestra: la ausencia de color no significa \"cero\".",
    "Turismo_pernoctaciones_oct2025": "Solo releva 3 de los 13 departamentos (ver Plazas "
        "disponibles). No es comparable como indicador de toda la provincia.",
    "Turismo_tasa_ocupacion_pct": "Solo releva 3 de los 13 departamentos (ver Plazas "
        "disponibles). No es comparable como indicador de toda la provincia.",
}


def construir_resumen_provincial(df_base):
    """Arma una fila sintética con el resumen de toda la provincia (o de la región filtrada)."""
    resumen = {"Departamento": "Toda la provincia", "Region": "Río Negro (13 departamentos)"}
    for key in INDICADORES:
        if key not in df_base.columns:
            continue
        serie = df_base[key].dropna()
        if key == "Densidad_hab_km2":
            resumen[key] = df_base["Poblacion"].sum() / SUPERFICIE_TOTAL_RN_KM2
        elif key in CAMPOS_TASA:
            resumen[key] = serie.mean() if len(serie) else None
        else:
            resumen[key] = serie.sum() if len(serie) else None
    for key in CAMPOS_TEXTO:
        resumen[key] = None  # los campos de texto no se resumen a nivel provincial
    return pd.Series(resumen)


# Campos categóricos/de texto que se muestran en la ficha de perfil pero no en el selector de mapa
CAMPOS_TEXTO = {
    "Ganaderia_especie_predominante": "Especie ganadera predominante",
    "Mineria_mineral_predominante": "Mineral predominante",
    "Energia_proyectos_en_desarrollo": "Proyectos de energía en desarrollo (no instalados aún)",
    "Turismo_destino_relevado_indec": "Destino relevado por INDEC (EOH)",
    "Conectividad_rutas_nacionales": "Rutas nacionales",
    "Conectividad_puerto": "Puerto",
    "Ambiente_ecorregion": "Ecorregión",
    "Ambiente_rio_principal": "Río / cuerpo de agua principal",
    "Ambiente_clima": "Caracterización climática",
}

# Centrales hidroeléctricas del río Limay: generación compartida con Neuquén.
# Se muestran como referencia en el mapa pero NO se suman al total de MW de Río Negro.
CENTRALES_LIMAY = [
    {"nombre": "Alicurá", "lat": -40.586, "lon": -70.753, "potencia_mw": 1050},
    {"nombre": "Piedra del Águila", "lat": -40.011, "lon": -69.990, "potencia_mw": 1400},
    {"nombre": "Pichi Picún Leufú", "lat": -40.05, "lon": -69.85, "potencia_mw": 261},
    {"nombre": "El Chocón", "lat": -39.259, "lon": -68.779, "potencia_mw": 1200},
    {"nombre": "Arroyito", "lat": -39.10, "lon": -68.65, "potencia_mw": 120},
]


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

@st.cache_data
def cargar_tabla():
    df = pd.read_csv(CSV_PATH)
    return df


@st.cache_data
def cargar_geojson():
    if not os.path.exists(GEOJSON_PATH):
        return None
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def cargar_capa_geografica(nombre_archivo):
    path = os.path.join(DATA_DIR, nombre_archivo)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def hex_a_rgba(hex_color, alpha=0.35):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def lineas_a_lat_lon(geojson_data):
    """Convierte features LineString/MultiLineString/Polygon/MultiPolygon en listas
    planas lat/lon con None como separador, listas para un único trace de Scattermap.
    Para polígonos, se dibuja solo el anillo exterior (sin agujeros)."""
    lats, lons = [], []
    for feat in geojson_data["features"]:
        geom = feat["geometry"]
        tipo = geom["type"]
        if tipo == "LineString":
            partes = [geom["coordinates"]]
        elif tipo == "MultiLineString":
            partes = geom["coordinates"]
        elif tipo == "Polygon":
            partes = [geom["coordinates"][0]]  # solo anillo exterior
        elif tipo == "MultiPolygon":
            partes = [poly[0] for poly in geom["coordinates"]]  # anillo exterior de cada parte
        else:
            continue
        for parte in partes:
            for lon, lat in parte:
                lats.append(lat)
                lons.append(lon)
            lats.append(None)
            lons.append(None)
    return lats, lons


def puntos_a_lat_lon(geojson_data):
    lats, lons, nombres = [], [], []
    for feat in geojson_data["features"]:
        geom = feat["geometry"]
        if geom["type"] != "Point":
            continue
        lon, lat = geom["coordinates"][:2]
        lats.append(lat)
        lons.append(lon)
        nombres.append(feat["properties"].get("nam") or feat["properties"].get("fna") or "")
    return lats, lons, nombres


df = cargar_tabla()
geojson = cargar_geojson()

# ---------------------------------------------------------------------------
# Sidebar: navegación
# ---------------------------------------------------------------------------

st.sidebar.title("Río Negro")
st.sidebar.caption("Una provincia, territorios distintos")

# Estado inicial (permite que el mapa y los chips de región actualicen estos valores
# desde afuera de los propios widgets, con key= para que se sincronicen entre sí)
if "region_sel" not in st.session_state:
    st.session_state["region_sel"] = "Todas"
if "departamento_sel" not in st.session_state:
    st.session_state["departamento_sel"] = "Toda la provincia"

regiones = ["Todas"] + sorted(df["Region"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("Región", regiones, key="region_sel")

df_filtrado = df if region_sel == "Todas" else df[df["Region"] == region_sel]

indicador_key = st.sidebar.selectbox(
    "Dimensión a explorar",
    options=list(INDICADORES.keys()),
    format_func=lambda k: INDICADORES[k],
)
indicador_label = INDICADORES[indicador_key]

opciones_depto = ["Toda la provincia"] + df_filtrado["Departamento"].tolist()
if st.session_state["departamento_sel"] not in opciones_depto:
    st.session_state["departamento_sel"] = "Toda la provincia"
departamento_sel = st.sidebar.selectbox(
    "Ver perfil de un departamento",
    options=opciones_depto,
    key="departamento_sel",
)

st.sidebar.markdown("---")
st.sidebar.caption("Capas de referencia sobre el mapa")
capas_activas = {}
for clave, info in CAPAS_GEOGRAFICAS.items():
    datos_capa = cargar_capa_geografica(info["file"])
    if datos_capa is None:
        continue  # el archivo no está disponible todavía: no se ofrece la opción
    activo_por_defecto = clave in ("rios",)
    capas_activas[clave] = st.sidebar.checkbox(info["label"], value=activo_por_defecto)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Los valores en blanco están PENDIENTES de carga. "
    "Editá data/tabla_maestra.csv para completarlos."
)

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero-title">Río Negro: una provincia, territorios distintos</div>
    <div class="hero-subtitle">
        Explorá cómo cambian la población, la educación, la salud, la producción,
        la minería, la energía y el ambiente según el departamento y la región que selecciones.
        Tocá una región abajo, o cualquier departamento del mapa, para filtrar.
    </div>
    """,
    unsafe_allow_html=True,
)

REGIONES_CHIPS = [
    ("Alto Valle", "🍎", "chip-valle"),
    ("Valle Medio", "🌾", "chip-valle"),
    ("Rio Colorado", "🌱", "chip-valle"),
    ("Linea Sur", "🐑", "chip-linea-sur"),
    ("Region Andina", "🏔️", "chip-andina"),
    ("Costa Atlantica", "🌊", "chip-costa"),
]
cols_chips = st.columns(len(REGIONES_CHIPS) + 1)
with cols_chips[0]:
    if st.button("Todas", key="chip_todas", use_container_width=True):
        st.session_state["region_sel"] = "Todas"
        st.rerun()
for col, (nombre, emoji, clase) in zip(cols_chips[1:], REGIONES_CHIPS):
    with col:
        etiqueta = nombre.replace("Rio", "Río").replace("Region", "Región")
        if st.button(f"{emoji} {etiqueta}", key=f"chip_{nombre}", use_container_width=True):
            st.session_state["region_sel"] = nombre
            st.rerun()
st.markdown("<br>", unsafe_allow_html=True)

col_mapa, col_perfil = st.columns([2, 1])

# ---------------------------------------------------------------------------
# Mapa
# ---------------------------------------------------------------------------

with col_mapa:
    st.subheader(f"Mapa: {indicador_label}")

    if indicador_key in INDICADORES_COBERTURA_PARCIAL:
        st.warning(f"⚠️ Cobertura parcial: {INDICADORES_COBERTURA_PARCIAL[indicador_key]}")

    mapa_ok = False
    if geojson is not None:
        try:
            fig = px.choropleth_map(
                df_filtrado,
                geojson=geojson,
                locations="Departamento",
                featureidkey=f"properties.{GEOJSON_NAME_FIELD}",
                color=indicador_key,
                color_continuous_scale="YlOrRd",
                map_style="carto-positron",
                zoom=4.6,
                center={"lat": -40.8, "lon": -67.5},
                opacity=0.75,
                hover_name="Departamento",
                hover_data={indicador_key: True, "Region": True},
            )
            fig.update_layout(
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                height=550,
                paper_bgcolor="#FBF9F5",
                font={"family": "Inter, sans-serif", "color": "#2B2B26"},
            )

            # Capas geográficas de referencia (ríos, canales, rutas, ferrocarril) según lo tildado
            for clave, activo in capas_activas.items():
                if not activo:
                    continue
                info = CAPAS_GEOGRAFICAS[clave]
                datos_capa = cargar_capa_geografica(info["file"])
                if info["tipo"] == "linea":
                    lats, lons = lineas_a_lat_lon(datos_capa)
                    relleno = clave == "embalses"
                    fig.add_scattermap(
                        lat=lats, lon=lons,
                        mode="lines",
                        line={"width": 1.6, "color": info["color"]},
                        fill="toself" if relleno else "none",
                        fillcolor=hex_a_rgba(info["color"]) if relleno else None,
                        name=info["label"],
                        hoverinfo="name",
                        showlegend=True,
                    )
                else:  # punto
                    lats, lons, nombres = puntos_a_lat_lon(datos_capa)
                    fig.add_scattermap(
                        lat=lats, lon=lons,
                        mode="markers",
                        marker={"size": 7, "color": info["color"]},
                        text=nombres,
                        hoverinfo="text",
                        name=info["label"],
                        showlegend=True,
                    )

            # Centrales del Limay: solo como referencia visual, no coloreadas ni sumadas al total de RN
            fig.add_scattermap(
                lat=[c["lat"] for c in CENTRALES_LIMAY],
                lon=[c["lon"] for c in CENTRALES_LIMAY],
                mode="markers+text",
                marker={"size": 12, "color": "#1f77b4", "symbol": "circle"},
                text=[c["nombre"] for c in CENTRALES_LIMAY],
                textposition="top center",
                hovertext=[f"{c['nombre']} — {c['potencia_mw']} MW (compartida con Neuquén, no incluida en el total de RN)"
                           for c in CENTRALES_LIMAY],
                hoverinfo="text",
                name="Centrales del río Limay (compartidas con Neuquén)",
                showlegend=True,
            )
            fig.update_layout(legend={
                "orientation": "h", "yanchor": "bottom", "y": 1.02,
                "bgcolor": "rgba(251,249,245,0.9)",
                "font": {"family": "Inter, sans-serif", "color": "#2B2B26"},
            })

            evento_mapa = st.plotly_chart(
                fig, use_container_width=True,
                on_select="rerun", selection_mode="points", key="mapa_click",
            )
            st.caption(
                "💡 Tocá cualquier departamento del mapa para ver su ficha. "
                "Los puntos azules son las 5 centrales hidroeléctricas del río Limay, compartidas con "
                "Neuquén: no están coloreadas por departamento ni suman al total de MW de Río Negro."
            )
            mapa_ok = True

            # Si el usuario clickeó un departamento en el mapa, sincronizamos el selector de perfil
            try:
                puntos = evento_mapa.selection.points if evento_mapa else []
            except AttributeError:
                puntos = (evento_mapa or {}).get("selection", {}).get("points", [])
            if puntos:
                depto_click = puntos[0].get("location")
                if depto_click and depto_click in df["Departamento"].values \
                        and depto_click != st.session_state.get("departamento_sel"):
                    st.session_state["departamento_sel"] = depto_click
                    st.rerun()
        except Exception as e:
            st.error(
                "No se pudo dibujar el mapa geográfico (error técnico, no es un problema con los "
                "datos). Se muestra el gráfico de barras como alternativa."
            )
            with st.expander("Detalle técnico del error"):
                st.code(str(e))

    if not mapa_ok:
        if geojson is None:
            st.info(
                "Todavía no se encontró data/rio_negro_departamentos.geojson. "
                "Mientras tanto se muestra un gráfico de barras con el mismo indicador. "
                "Ver README.md para exportar el GeoJSON desde tu capa del IGN en GeoPandas."
            )
        fig_bar = px.bar(
            df_filtrado.sort_values(indicador_key, ascending=False),
            x="Departamento",
            y=indicador_key,
            color="Region",
            labels={indicador_key: indicador_label},
        )
        fig_bar.update_layout(
            height=550,
            paper_bgcolor="#FBF9F5",
            plot_bgcolor="#FBF9F5",
            font={"family": "Inter, sans-serif", "color": "#2B2B26"},
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Perfil de departamento
# ---------------------------------------------------------------------------

with col_perfil:
    st.subheader("Perfil territorial")

    if departamento_sel == "Toda la provincia":
        fila = construir_resumen_provincial(df_filtrado)
        st.markdown(f"### {fila['Departamento']}")
        st.caption(
            f"Región: {fila['Region']}" if region_sel == "Todas"
            else f"Resumen de la región: {region_sel}"
        )
        st.caption(
            "Los valores son la suma de los 13 departamentos (o el promedio, cuando el "
            "indicador ya es un porcentaje/tasa)."
        )
    else:
        fila = df[df["Departamento"] == departamento_sel].iloc[0]
        st.markdown(f"### {fila['Departamento']}")
        st.caption(f"Región: {fila['Region']}")

    grupos = {
        "Población": ["Poblacion", "Densidad_hab_km2", "Educ_secundaria_completa_pct",
                      "Salud_solo_publico_pct", "Pob_65mas_pct"],
        "Producción agropecuaria": ["Agricultura_superficie_implantada_ha", "Agricultura_frutales_pct",
                                    "Agricultura_forrajeras_pct", "Agricultura_cereales_pct",
                                    "Agricultura_bosques_pct", "Riego_superficie_regada_ha",
                                    "Riego_pct_superficie_regada", "Riego_pct_eap_con_riego"],
        "Ganadería": ["Ganaderia_cabezas_totales", "Ganaderia_especie_predominante",
                     "Ganaderia_bovinos", "Ganaderia_ovinos", "Ganaderia_caprinos",
                     "Ganaderia_bovinos_pct", "Ganaderia_ovinos_pct", "Ganaderia_caprinos_pct",
                     "Ganaderia_porcinos_pct", "Ganaderia_equinos_pct"],
        "Minería": ["Mineria_minas_formales_totales", "Mineria_mineral_predominante",
                   "Mineria_minerales_diferentes", "Mineria_superficie_registrada_ha"],
        "Energía": ["Energia_MW_instalada", "Energia_MW_hidraulica", "Energia_MW_eolica",
                   "Energia_MW_termica", "Energia_proyectos_en_desarrollo"],
        "Hidrocarburos": ["Hidrocarburos_pozos_totales", "Hidrocarburos_pozos_extraccion_efectiva",
                          "Hidrocarburos_prod_petroleo_m3_2025", "Hidrocarburos_prod_gas_miles_m3_2025"],
        "Turismo": ["Turismo_localidades_con_alojamiento", "Turismo_destinos_destacados",
                   "Turismo_parques_nacionales",
                   "Turismo_areas_naturales_protegidas",
                   "Turismo_plazas_disponibles_oct2025", "Turismo_pernoctaciones_oct2025",
                   "Turismo_tasa_ocupacion_pct", "Turismo_destino_relevado_indec"],
        "Conectividad": ["Conectividad_aeropuertos", "Conectividad_estaciones_tren",
                         "Conectividad_rutas_nacionales", "Conectividad_puerto"],
        "Ambiente": ["Ambiente_ecorregion", "Ambiente_rio_principal", "Ambiente_clima",
                    "Turismo_parques_nacionales", "Turismo_areas_naturales_protegidas"],
        "Pesca e industria": ["Pesca_desembarque_toneladas_2025", "Industria_parques_industriales"],
    }

    for titulo, campos in grupos.items():
        with st.expander(titulo, expanded=(titulo == "Población")):
            for key in campos:
                if key not in fila or pd.isna(fila[key]):
                    continue
                label = INDICADORES.get(key) or CAMPOS_TEXTO.get(key, key)
                valor = fila[key]
                if isinstance(valor, str):
                    st.metric(label, valor)
                else:
                    st.metric(label, f"{valor:,.2f}".rstrip("0").rstrip("."))

    if isinstance(fila.get("Fuente_notas"), str):
        with st.expander("Fuentes y notas metodológicas"):
            st.write(fila["Fuente_notas"])

# ---------------------------------------------------------------------------
# Comparación entre departamentos
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Comparar departamentos")

comparar = st.multiselect(
    "Elegí dos o más departamentos para comparar en la dimensión seleccionada",
    options=df["Departamento"].tolist(),
    default=df_filtrado["Departamento"].tolist()[:3],
)

if len(comparar) >= 2:
    df_comp = df[df["Departamento"].isin(comparar)]
    fig_comp = px.bar(
        df_comp.sort_values(indicador_key, ascending=False),
        x="Departamento",
        y=indicador_key,
        color="Region",
        text=indicador_key,
        labels={indicador_key: indicador_label},
    )
    fig_comp.update_layout(
        height=400,
        paper_bgcolor="#FBF9F5",
        plot_bgcolor="#FBF9F5",
        font={"family": "Inter, sans-serif", "color": "#2B2B26"},
    )
    st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.caption("Elegí al menos dos departamentos para ver la comparación.")

# ---------------------------------------------------------------------------
# Relación entre dos variables (gráfico de dispersión)
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("¿Se relacionan dos variables entre sí?")
st.caption(
    "Elegí dos dimensiones y mirá si los departamentos siguen un patrón: por ejemplo, "
    "¿los más poblados son también los que más energía generan?"
)

col_x, col_y = st.columns(2)
with col_x:
    var_x = st.selectbox(
        "Eje horizontal", options=list(INDICADORES.keys()),
        format_func=lambda k: INDICADORES[k], key="scatter_x",
        index=list(INDICADORES.keys()).index("Poblacion"),
    )
with col_y:
    opciones_y = [k for k in INDICADORES if k != var_x]
    default_y = "Energia_MW_instalada" if "Energia_MW_instalada" in opciones_y else opciones_y[0]
    var_y = st.selectbox(
        "Eje vertical", options=opciones_y,
        format_func=lambda k: INDICADORES[k], key="scatter_y",
        index=opciones_y.index(default_y),
    )

df_scatter = df.dropna(subset=[var_x, var_y])
if len(df_scatter) >= 2:
    fig_scatter = px.scatter(
        df_scatter,
        x=var_x, y=var_y,
        color="Region",
        text="Departamento",
        labels={var_x: INDICADORES[var_x], var_y: INDICADORES[var_y]},
    )
    fig_scatter.update_traces(textposition="top center", marker={"size": 12})
    fig_scatter.update_layout(
        height=450,
        paper_bgcolor="#FBF9F5",
        plot_bgcolor="#FBF9F5",
        font={"family": "Inter, sans-serif", "color": "#2B2B26"},
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption(
        f"{len(df_scatter)} de 13 departamentos tienen dato en ambas variables. "
        "Cada punto es un departamento; si se agrupan formando una diagonal, hay relación "
        "entre las dos variables. Si aparecen dispersos sin patrón, no la hay."
    )
else:
    st.caption("No hay suficientes departamentos con datos en ambas variables para graficar.")

# ---------------------------------------------------------------------------
# Tabla completa (transparencia de datos)
# ---------------------------------------------------------------------------

with st.expander("Ver tabla completa de datos"):
    st.dataframe(df, use_container_width=True)
