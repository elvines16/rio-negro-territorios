# Río Negro: una provincia, territorios distintos

Esqueleto funcional para la exploración interactiva del proyecto "Contar con Datos 2026".

## 1. Correr en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`. Ahora mismo funciona con los datos de ejemplo
de `data/tabla_maestra.csv` y, si no hay GeoJSON, muestra un gráfico de barras
en lugar del mapa (para que puedan probar la interacción ya mismo sin esperar
a tener la capa cartográfica lista).

## 2. Completar la tabla maestra

Editar `data/tabla_maestra.csv`. Cada fila es un departamento. Las celdas vacías
se muestran como "Sin dato aún" en la app — no hace falta completar todo para
probar, pero sí antes de la entrega final.

Si prefieren generarlo desde Colab/pandas en vez de editarlo a mano, el único
requisito es que el CSV final tenga estas columnas (incluida `Departamento`
con el nombre exacto que van a usar también en el GeoJSON):

```
Departamento, Region, Poblacion, Densidad_hab_km2, Educ_secundaria_completa_pct,
Salud_solo_publico_pct, Pob_65mas_pct, Agricultura_superficie_ha,
Mineria_mineral_predominante, Energia_MW_instalada, Fuente_notas
```

Para agregar un indicador nuevo (por ejemplo minería como número, o eólica):
1. Agregar la columna al CSV.
2. Agregar una entrada al diccionario `INDICADORES` en `app.py` (arriba del todo).
Nada más — el selector de dimensión, el mapa, la ficha de perfil y la
comparación lo toman automáticamente.

## 3. Agregar el mapa real (GeoJSON del IGN)

Ya vienen trabajando la capa de departamentos de Río Negro en GeoPandas.
Para exportarla como GeoJSON:

```python
import geopandas as gpd

gdf = gpd.read_file("capa_departamentos_ign.shp")  # su archivo actual
gdf = gdf.to_crs(epsg=4326)  # importante: lat/lon, no la proyección original
gdf.to_file("data/rio_negro_departamentos.geojson", driver="GeoJSON")
```

Después:
- Revisar `gdf.columns` para confirmar cómo se llama la columna con el nombre
  del departamento, y poner ese nombre exacto en `GEOJSON_NAME_FIELD` en `app.py`.
- Los nombres de departamento en esa columna deben coincidir EXACTO con los
  de la columna `Departamento` del CSV (mismo problema de homologación de
  nombres que ya venían enfrentando — conviene resolverlo acá de una vez).

## 4. Desplegar gratis (para tener el link público que piden las bases)

1. Crear un repositorio en GitHub y subir esta carpeta completa (`app.py`,
   `requirements.txt`, `data/`).
2. Ir a [share.streamlit.io](https://share.streamlit.io), loguearse con GitHub.
3. "New app" → elegir el repo → `app.py` como archivo principal → Deploy.
4. Copiar el link público (formato `https://TUAPP.streamlit.app`) — ese es el
   que van a pegar en el campo "Archivo externo" del formulario de inscripción.

Este tipo de link cumple con las bases: no implica descarga, es un portal de
reproducción/uso en línea de la app.

## 5. Para el video de 1 minuto que pide el concurso

Grabar la pantalla navegando: mapa general → seleccionar un departamento con
un perfil (ej. población alta) → cambiar de dimensión (ej. a producción) →
mostrar cómo cambia el patrón → comparar dos departamentos contrastantes
(ej. General Roca vs. 9 de Julio). Eso alcanza para transmitir la idea de
"una provincia, territorios distintos" en 60 segundos.

## Pendientes conocidos (no son bugs, son próximos pasos)

- Completar todos los "PENDIENTE" de `tabla_maestra.csv`.
- Agregar la columna de minería como indicador cuantitativo si logran un
  número comparable por departamento (hoy el CSV solo tiene una celda de
  texto libre para el mineral predominante).
- La columna `Region` que viene en el CSV de ejemplo es un borrador de
  regionalización — está marcada como tal en el documento del proyecto y
  puede necesitar ajustes en zonas de transición (Catriel, Valcheta, etc.).
