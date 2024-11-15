import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from gtfs_merida import GTFSMerida

datos = "../datos"
gtfs_file_base = f"{datos}/GTFS/gtfs-merida.zip"
gtfs_file_treatment = f"{datos}/GTFS/gtfs-merida.zip"
zonas_path = f"{datos}/od_celular/zonificacion.gpkg"
path_rutas_base = f"{datos}/rutas_merida_geo/rutas_merida.geojson"
path_rutas_treatment = f"{datos}/rutas_merida_geo/rutas_merida.geojson"
path_paradas_base = f"{datos}/rutas_merida_geo/paradas_merida.geojson"
path_paradas_treatment = f"{datos}/rutas_merida_geo/paradas_merida.geojson"
od_path = f"{datos}/od_celular/Matriz_OD_Movilidad_Merida.csv"
isocronas_pob_gpkg = f"{datos}/isocronas_mza_pob_merida_2020.gpkg"
manzanas_shp = f"{datos}/31_Manzanas_INV2020_shp/INV2020_IND_PVEU_MZA_31.shp"
bbox_merida = 3764086,1034675,3792830,1069982
imgs_folder = "images"
t = 5

FIG_SIZE = (14, 14)

def get_correlacion_gtfs(gtfs_obj, zonas_path, od_path):
    """
    Calcula la correlación entre la oferta de transporte público y la demanda de viajes
    en función de la hora del día.
    :param gtfs_obj: objeto GTFSMerida
    :param zonas_path: ruta al archivo de zonas de celular
    :param od_path: ruta al archivo de matriz origen destino
    :return: numpy array con la correlación entre oferta y demanda por hora
    """
    stoptimes = gtfs_obj.get_stop_times()
    paradas = gtfs_obj.get_stops()
    print("Número de paradas", paradas.shape[0])
    print("Número de viajes", stoptimes.shape[0])
    zonas_celular = gpd.read_file(zonas_path)\
            .to_crs(epsg=4326)\
            .set_index("ID")\
            .rename(int)
    od = pd.read_csv(od_path)
    od["hora"] = od.origin_period.str[1:].astype(int)
    matrix_od = pd.crosstab([od["origin_zone"], od["hora"]], od["destination_zone"], values=od["trips"], aggfunc="sum").fillna(0)
    viajes_origen_hora = matrix_od.sum(axis=1).unstack("hora").fillna(0)
    paradas_zona = gpd.sjoin(paradas, zonas_celular, predicate="intersects")\
            .rename(columns={"ID": "zona_id"})
    stoptimes_zona = pd.merge(stoptimes, paradas_zona[["stop_id", "zona_id"]], on="stop_id")
    oferta_zona_hora = stoptimes_zona.groupby(["zona_id", "hora"])["trip_id"].nunique().unstack("hora").fillna(0)
    oferta_demanda = oferta_zona_hora.add_prefix("oferta_")\
        .join(viajes_origen_hora.add_prefix("demanda_"))
    corr = np.diag(oferta_demanda.corr().filter(like="demanda_").values)
    correlaciones_hora = pd.DataFrame(data={"correlacion": corr, "hora": range(len(corr))})
    return correlaciones_hora

def get_poblacion_atendida_from_gtfs(gtfs_obj, t=5):
    """
    Calcula la población atendida por las rutas de transporte público a t minutos de viaje en transporte público en Merida Yucatán.
    :param gtfs_obj: objeto GTFSMerida
    :param t: tiempo de viaje en minutos
    :return: GeoDataFrame con las manzanas atendidas por las rutas de transporte público.
    """
    rutas = gtfs_obj.get_rutas()
    iso = gpd.read_file(isocronas_pob_gpkg, encoding='utf-8', layer=f"{t}_minutos_pob", columns=['CVEGEO', 'geometry'])
    manz = gpd.read_file(manzanas_shp, encoding='utf-8', bbox=bbox_merida)\
        .to_crs(epsg=4326)
    variables_poblacion = ["POBTOT", "POBFEM", "POB0_14", "P_60YMAS", "P_CD_T"]
    for v in variables_poblacion:
        manz[v] = manz[v].str.replace("\D", "0", regex=True).astype(int)


    mzas_ruta_total = []
    for i in rutas.index:
        ruta_i = rutas.loc[i, "geometry"]
        mzas_ruta_iso = iso.loc[iso.intersects(ruta_i), "CVEGEO"].unique().tolist()
        mzas_ruta_total += mzas_ruta_iso

    mzas_ruta_unq = list(set(mzas_ruta_total))
    manz_rutas = manz.loc[manz["CVEGEO"].isin(mzas_ruta_unq)]
    return manz_rutas

def get_waiting_times_gtfs(gtfs_obj, t):
    stop_times = gtfs_obj.get_stop_times().query("hora<24").copy()
    stop_times["arrival_time"] = pd.to_datetime(stop_times["arrival_time"], format="%H:%M:%S")#.groupby(["stop_id"])#["trip_id"]
    paradas = gtfs_obj.get_stops()
    print("Número de paradas", paradas.shape[0])
    iso = gpd.read_file(isocronas_pob_gpkg, encoding='utf-8', layer=f"{t}_minutos_pob", columns=['CVEGEO', 'geometry'])
    manz = gpd.read_file(manzanas_shp, encoding='utf-8', bbox=bbox_merida)\
        .to_crs(epsg=4326)
    manz["POBTOT"] = manz["POBTOT"].astype(int)
    tiempo_promedio_paradas = stop_times.sort_values(["stop_id", "arrival_time"])\
    .groupby(["stop_id"])\
    .apply(lambda x: x["arrival_time"].diff().dt.total_seconds().div(60).mean(), include_groups=False)\
    .reset_index(name="mean_time")\
    .merge(paradas, on="stop_id")\
    .filter(["stop_id", "mean_time", "geometry"])\
    .pipe(gpd.GeoDataFrame, crs="EPSG:4326", geometry="geometry")

    tiempo_promedio_mza = gpd.sjoin(iso, tiempo_promedio_paradas, predicate="contains")\
    .groupby("CVEGEO")\
    .agg({"mean_time": "mean"})\
    .reset_index()

    manzanas_tiempo_promedio = manz[["CVEGEO", "geometry"]].merge(tiempo_promedio_mza, on="CVEGEO")
    return manzanas_tiempo_promedio

# if __name__ == "__main__":
#     gtfs_base = GTFSMerida(gtfs_file_base)
#     gtfs_treatment = GTFSMerida(gtfs_file_treatment)
#     rutas_base = gtfs_base.get_rutas()
#     rutas_treatment = gtfs_treatment.get_rutas()
#     paradas_base = gtfs_base.get_stops()
#     paradas_treatment = gtfs_treatment.get_stops()
#     ouput_folder = f"{datos}/calculos_gtfs"

#     # Correlación oferta-demanda
#     correlacion_od_base = get_correlacion_gtfs(gtfs_base, zonas_path, od_path)
#     correlacion_od_base.to_csv(f"{ouput_folder}/correlacion_oferta_demanda_base.csv")
#     print(f"archivo guardado en {ouput_folder}/correlacion_oferta_demanda_base.csv")
#     correlacion_od_treatment = get_correlacion_gtfs(gtfs_treatment, zonas_path, od_path)
#     correlacion_od_treatment.to_csv(f"{ouput_folder}/correlacion_oferta_demanda_treatment.csv")
#     print(f"archivo guardado en {ouput_folder}/correlacion_oferta_demanda_treatment.csv")

#     # Población atendida por manzanas
#     manz_rutas_atendidas_base = get_poblacion_atendida_from_gtfs(gtfs_base, t=t)
#     manz_rutas_atendidas_base.to_file(f"{ouput_folder}/manzanas_rutas_atendidas_base.gpkg", driver="GPKG")
#     print(f"archivo guardado en {ouput_folder}/manzanas_rutas_atendidas_base.gpkg")
#     manz_rutas_atendidas_treatment = get_poblacion_atendida_from_gtfs(gtfs_treatment, t=t)
#     manz_rutas_atendidas_treatment.to_file(f"{ouput_folder}/manzanas_rutas_atendidas_treatment.gpkg", driver="GPKG")
#     print(f"archivo guardado en {ouput_folder}/manzanas_rutas_atendidas_treatment.gpkg")

#     # mapa de población atendida
#     fig, (ax1, ax2) = plt.subplots(2, 1)
#     manz_rutas_atendidas_base.plot(column='POBTOT', ax=ax1, legend=True, cmap="viridis")
#     rutas_base.plot(ax=ax1, color="red", linewidth=0.5)
#     ax1.set_title('Población con acceso a transporte público a 5 minutos caminando (base)')
#     ax1.set_axis_off()

#     manz_rutas_atendidas_treatment.plot(column='POBTOT', ax=ax2, legend=True, cmap="viridis")
#     ax2.set_title('Población con acceso a transporte público a 5 minutos caminando (tratamiento)')
#     ax2.set_axis_off()
#     rutas_treatment.plot(ax=ax2, color="red", linewidth=0.5)
#     fig.set_size_inches(FIG_SIZE)
#     fig.savefig(f"{imgs_folder}/mapa_poblacion_atendida.png", bbox_inches="tight", dpi=600)

#     pob_atendida_base = manz_rutas_atendidas_base["POBTOT"].sum()
#     print(f"Población atendida a {t} minutos (base): {pob_atendida_base}")
#     pob_atendida_treatment = manz_rutas_atendidas_treatment["POBTOT"].sum()
#     print(f"Población atendida a {t} minutos (treatment): {pob_atendida_treatment}")

#     # Tiempo promedio de espera en paraderos
#     manzanas_tiempo_promedio_base = get_waiting_times_gtfs(gtfs_base, t)
#     manzanas_tiempo_promedio_base.to_file(f"{ouput_folder}/manzanas_tiempo_promedio_base.gpkg", driver="GPKG")
#     print(f"archivo guardado en {ouput_folder}/manzanas_tiempo_promedio_base.gpkg")

#     manzanas_tiempo_promedio_treatment = get_waiting_times_gtfs(gtfs_treatment, t)
#     manzanas_tiempo_promedio_treatment.to_file(f"{ouput_folder}/manzanas_tiempo_promedio_treatment.gpkg", driver="GPKG")
#     print(f"archivo guardado en {ouput_folder}/manzanas_tiempo_promedio_treatment.gpkg")

#     print(f"Tiempo promedio de espera en paraderos a {t} minutos (base)", manzanas_tiempo_promedio_base["mean_time"].mean())
#     print(f"Tiempo promedio de espera en paraderos a {t} minutos (treatment)", manzanas_tiempo_promedio_treatment["mean_time"].mean())

#     # mapas de tiempo promedio de espera
#     MARKER_SIZE = 0.05
#     fig, (ax1, ax2) = plt.subplots(2, 1)
#     manzanas_tiempo_promedio_base.plot(column='mean_time', ax=ax1, legend=True, cmap="viridis")
#     paradas_base.plot(ax=ax1, color="red", markersize=MARKER_SIZE)
#     ax1.set_title('Tiempo promedio de espera (base)')
#     ax1.set_axis_off()

#     manzanas_tiempo_promedio_treatment.plot(column='mean_time', ax=ax2, legend=True, cmap="viridis")
#     paradas_treatment.plot(ax=ax2, color="red", markersize=MARKER_SIZE)
#     ax2.set_title('Tiempo promedio de espera (tratamiento)')
#     ax2.set_axis_off()
#     fig.set_size_inches(FIG_SIZE)
#     fig.savefig(f"{imgs_folder}/mapa_tiempo_promedio_espera.png", bbox_inches="tight", dpi=600)

#     # feed time series
#     fts_base = gtfs_base.get_feed_ts()
#     fts_base.to_csv(f"{ouput_folder}/feed_time_series_base.csv")
#     print(f"archivo guardado en {ouput_folder}/feed_time_series_base.csv")
#     fts_treatment = gtfs_treatment.get_feed_ts()
#     fts_treatment.to_csv(f"{ouput_folder}/feed_time_series_treatment.csv")
#     print(f"archivo guardado en {ouput_folder}/feed_time_series_treatment.csv")
