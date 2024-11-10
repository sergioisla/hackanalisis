import pandas as pd
import geopandas as gpd
import numpy as np

from gtfs_merida import GTFSMerida

datos = "../datos"
gtfs_file = f"{datos}/GTFS/gtfs-merida.zip"
zonas_path = f"{datos}/od_celular/zonificacion.gpkg"
od_path = f"{datos}/od_celular/Matriz_OD_Movilidad_Merida.csv"
isocronas_pob_gpkg = f"{datos}/isocronas_mza_pob_merida_2020.gpkg"
manzanas_shp = f"{datos}/31_Manzanas_INV2020_shp/INV2020_IND_PVEU_MZA_31.shp"
bbox_merida = 3764086,1034675,3792830,1069982

t = 5
gtfs_base = GTFSMerida(gtfs_file)

def calcula_correlacion_gtfs(gtfs_obj, zonas_path, od_path):
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
    correlaciones_hora = np.diag(oferta_demanda.corr().filter(like="demanda_").values)
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
    manz["POBTOT"] = manz["POBTOT"].astype(int)

    mzas_ruta_total = []
    for i in rutas.index:
        if (i % 10) == 0:
            print(f"Procesando ruta {i+1} de {len(rutas)}")
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
    iso = gpd.read_file(isocronas_pob_gpkg, encoding='utf-8', layer=f"{t}_minutos_pob", columns=['CVEGEO', 'geometry'])
    manz = gpd.read_file(manzanas_shp, encoding='utf-8', bbox=bbox_merida)\
        .to_crs(epsg=4326)
    manz["POBTOT"] = manz["POBTOT"].astype(int)
    tiempo_promedio_paradas = stop_times.sort_values(["stop_id", "arrival_time"])\
    .groupby(["stop_id"])\
    .apply(lambda x: x["arrival_time"].diff().dt.total_seconds().div(60).mean())\
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


correlacion_od = calcula_correlacion_gtfs(gtfs_base, zonas_path, od_path)
print("Correlación entre oferta y demanda:", correlacion_od)

manz_rutas_atendidas_base = get_poblacion_atendida_from_gtfs(gtfs_base, t=t)
pob_atendida_base = manz_rutas_atendidas_base["POBTOT"].sum()
print(f"Población atendida a {t} minutos: {pob_atendida_base}")

manzanas_tiempo_promedio = get_waiting_times_gtfs(gtfs_base, t)
print(f"Tiempo promedio de espera en paraderos a {t} minutos", manzanas_tiempo_promedio["mean_time"].mean())
