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

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "tabla_maestra.csv")
GEOJSON_PATH = os.path.join(DATA_DIR, "rio_negro_departamentos.geojson")

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
    "Ganaderia_bovinos_pct": "Composición del rodeo: bovinos (%)",
    "Ganaderia_ovinos_pct": "Composición del rodeo: ovinos (%)",
    "Ganaderia_caprinos_pct": "Composición del rodeo: caprinos (%)",
    "Ganaderia_porcinos_pct": "Composición del rodeo: porcinos (%)",
    "Ganaderia_equinos_pct": "Composición del rodeo: equinos (%)",
    "Mineria_minas_formales_totales": "Minas formales registradas",
    "Mineria_minerales_diferentes": "Diversidad de minerales distintos",
    "Mineria_superficie_registrada_ha": "Superficie minera registrada (ha)",
    "Energia_MW_instalada": "Potencia eléctrica instalada (MW)",
    "Hidrocarburos_pozos_totales": "Pozos de petróleo/gas (total)",
    "Hidrocarburos_prod_petroleo_m3_2025": "Producción de petróleo 2025 (m³)",
    "Hidrocarburos_prod_gas_miles_m3_2025": "Producción de gas 2025 (miles de m³)",
    "Turismo_localidades_con_alojamiento": "Localidades con alojamiento turístico registrado",
    "Turismo_parques_nacionales": "Parques nacionales (Administración de Parques Nacionales)",
    "Turismo_areas_naturales_protegidas": "Áreas naturales protegidas (provinciales)",
    "Turismo_plazas_disponibles_oct2025": "Plazas turísticas disponibles (oct. 2025, INDEC)",
    "Turismo_pernoctaciones_oct2025": "Pernoctaciones (oct. 2025, INDEC)",
    "Turismo_tasa_ocupacion_pct": "Tasa de ocupación hotelera (%, oct. 2025, INDEC)",
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


df = cargar_tabla()
geojson = cargar_geojson()

# ---------------------------------------------------------------------------
# Sidebar: navegación
# ---------------------------------------------------------------------------

st.sidebar.title("Río Negro")
st.sidebar.caption("Una provincia, territorios distintos")

regiones = ["Todas"] + sorted(df["Region"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("Región", regiones)

df_filtrado = df if region_sel == "Todas" else df[df["Region"] == region_sel]

indicador_key = st.sidebar.selectbox(
    "Dimensión a explorar",
    options=list(INDICADORES.keys()),
    format_func=lambda k: INDICADORES[k],
)
indicador_label = INDICADORES[indicador_key]

departamento_sel = st.sidebar.selectbox(
    "Ver perfil de un departamento",
    options=["Toda la provincia"] + df_filtrado["Departamento"].tolist(),
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Los valores en blanco están PENDIENTES de carga. "
    "Editá data/tabla_maestra.csv para completarlos."
)

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------

st.title("Río Negro: una provincia, territorios distintos")
st.markdown(
    "Explorá cómo cambian la población, la educación, la salud, la producción, "
    "la minería y la energía según el departamento y la región que selecciones."
)

col_mapa, col_perfil = st.columns([2, 1])

# ---------------------------------------------------------------------------
# Mapa
# ---------------------------------------------------------------------------

with col_mapa:
    st.subheader(f"Mapa: {indicador_label}")

    if indicador_key in INDICADORES_COBERTURA_PARCIAL:
        st.warning(f"⚠️ Cobertura parcial: {INDICADORES_COBERTURA_PARCIAL[indicador_key]}")

    if geojson is not None:
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
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=550)

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
        fig.update_layout(legend={"orientation": "h", "yanchor": "bottom", "y": 1.02})

        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Los puntos azules son las 5 centrales hidroeléctricas del río Limay, compartidas con "
            "Neuquén. No están coloreadas por departamento ni suman al total de MW de Río Negro."
        )
    else:
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
        fig_bar.update_layout(height=550)
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
                     "Ganaderia_bovinos_pct", "Ganaderia_ovinos_pct", "Ganaderia_caprinos_pct",
                     "Ganaderia_porcinos_pct", "Ganaderia_equinos_pct"],
        "Minería": ["Mineria_minas_formales_totales", "Mineria_mineral_predominante",
                   "Mineria_minerales_diferentes", "Mineria_superficie_registrada_ha"],
        "Energía": ["Energia_MW_instalada", "Energia_MW_hidraulica", "Energia_MW_eolica",
                   "Energia_MW_termica", "Energia_proyectos_en_desarrollo"],
        "Hidrocarburos": ["Hidrocarburos_pozos_totales", "Hidrocarburos_pozos_extraccion_efectiva",
                          "Hidrocarburos_prod_petroleo_m3_2025", "Hidrocarburos_prod_gas_miles_m3_2025"],
        "Turismo": ["Turismo_localidades_con_alojamiento", "Turismo_parques_nacionales",
                   "Turismo_areas_naturales_protegidas",
                   "Turismo_plazas_disponibles_oct2025", "Turismo_pernoctaciones_oct2025",
                   "Turismo_tasa_ocupacion_pct", "Turismo_destino_relevado_indec"],
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
    fig_comp.update_layout(height=400)
    st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.caption("Elegí al menos dos departamentos para ver la comparación.")

# ---------------------------------------------------------------------------
# Tabla completa (transparencia de datos)
# ---------------------------------------------------------------------------

with st.expander("Ver tabla completa de datos"):
    st.dataframe(df, use_container_width=True)
