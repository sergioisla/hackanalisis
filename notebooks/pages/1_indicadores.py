import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Indicadore GTFS Merida",
    page_icon="🚍",
    #layout="wide",
)

t=5
datos = "../datos"
input_folder = f"{datos}/calculos_gtfs"
imgs_folder = "images"

@st.cache_data
def get_correlation():
    correlacion_od_base = pd.read_csv(f"{input_folder}/correlacion_oferta_demanda_base.csv")
    correlacion_od_treatment = pd.read_csv(f"{input_folder}/correlacion_oferta_demanda_treatment.csv")
    return correlacion_od_base, correlacion_od_treatment

@st.cache_data
def get_poblacion_atendida():
    manzanas_poblacion_atendidas_base = gpd.read_file(f"{input_folder}/manzanas_rutas_atendidas_base.gpkg")
    manzanas_poblacion_atendidas_treatment = gpd.read_file(f"{input_folder}/manzanas_rutas_atendidas_treatment.gpkg")
    return manzanas_poblacion_atendidas_base, manzanas_poblacion_atendidas_treatment


@st.cache_data
def get_tiempo_promedio():
    manzanas_tiempo_promedio_base = gpd.read_file(f"{input_folder}/manzanas_tiempo_promedio_base.gpkg")
    manzanas_tiempo_promedio_treatment = gpd.read_file(f"{input_folder}/manzanas_tiempo_promedio_treatment.gpkg")
    return manzanas_tiempo_promedio_base, manzanas_tiempo_promedio_treatment

correlacion_od_base, correlacion_od_treatment = get_correlation()
manzanas_poblacion_atendidas_base, manzanas_poblacion_atendidas_treatment = get_poblacion_atendida()
manzanas_tiempo_promedio_base, manzanas_tiempo_promedio_treatment = get_tiempo_promedio()

variables_poblacion = ["POBTOT", "POBFEM", "POB0_14", "P_60YMAS", "P_CD_T"]

pob_atendida_base = manzanas_poblacion_atendidas_base["POBTOT"].sum()
pob_atendida_treatment = manzanas_poblacion_atendidas_treatment["POBTOT"].sum()

pob_atendida_base_mujeres = manzanas_poblacion_atendidas_base["POBFEM"].sum()
pob_atendida_treatment_mujeres = manzanas_poblacion_atendidas_treatment["POBFEM"].sum()

pob_atendida_base_ninios = manzanas_poblacion_atendidas_base["POB0_14"].sum()
pob_atendida_treatment_ninios = manzanas_poblacion_atendidas_treatment["POB0_14"].sum()

pob_atendida_base_60ymas = manzanas_poblacion_atendidas_base["P_60YMAS"].sum()
pob_atendida_treatment_60ymas = manzanas_poblacion_atendidas_treatment["P_60YMAS"].sum()

pob_atendida_base_discapacitados = manzanas_poblacion_atendidas_base["P_CD_T"].sum()
pob_atendida_treatment_discapacitados = manzanas_poblacion_atendidas_treatment["P_CD_T"].sum()


tiempo_promedio_base = manzanas_tiempo_promedio_base["mean_time"].mean()
tiempo_promedio_treatment = manzanas_tiempo_promedio_treatment["mean_time"].mean()

plt.style.use('seaborn-v0_8-whitegrid')

def color_markdown(v):
    if v < 0:
        return f':red[{v:,}]'
    elif v > 0:
        return f':green[{v:,}]'
    else:
        return f':blue[{v:,}]'

st.markdown(
    f"""
    # Indicadores de Impacto

    *Simulemos ¿Qué pasaría si introducimos una nueva ruta de transporte público en Mérida?*

    ### Población atendida a {t} minutos:

    | Tipo de Población | Sin intervención | Con intervención | Impacto |
    |-------------------|------------------|------------------|---------|
    | Población total | {pob_atendida_base:,} | {pob_atendida_treatment:,} | {color_markdown(pob_atendida_treatment - pob_atendida_base)} |
    | Población mujeres | {pob_atendida_base_mujeres} | {pob_atendida_treatment_mujeres} | {color_markdown(pob_atendida_treatment_mujeres - pob_atendida_base_mujeres)} |
    | Población 0-14 años | {pob_atendida_base_ninios} | {pob_atendida_treatment_ninios} | {color_markdown(pob_atendida_treatment_ninios - pob_atendida_base_ninios)} |
    | Población 60+ años | {pob_atendida_base_60ymas} | {pob_atendida_treatment_60ymas} | {color_markdown(pob_atendida_treatment_60ymas - pob_atendida_base_60ymas)} |
    | Población con discapacidad | {pob_atendida_base_discapacitados} | {pob_atendida_treatment_discapacitados} | {color_markdown(pob_atendida_treatment_discapacitados - pob_atendida_base_discapacitados)} |
    """
)
# mapa de población atendida
st.image(f"{imgs_folder}/mapa_poblacion_atendida.png")

# Población atendida
fig, ax = plt.subplots()
ax.bar(['Base', 'Tratamiento'], [pob_atendida_base, pob_atendida_treatment], color=['blue', 'orange'])
ax.set_ylabel('Población atendida')
ax.set_title('Comparación de población con acceso a transporte público a 5 minutos caminando')
_ = [sp.set_visible(False) for sp in ax.spines.values()]
st.pyplot(fig)

st.markdown(
    f"""
    ### Tiempo promedio de espera en paraderos cercanos:

    | Indicador | Sin intervención | Con intervención | Impacto |
    |-----------|------------------|------------------|---------|
    | Tiempo de espera | {tiempo_promedio_base:.2f} minutos | {tiempo_promedio_treatment:.2f} minutos | {color_markdown(tiempo_promedio_treatment - tiempo_promedio_base)} |
    """
)

# Mapa de tiempo promedio de espera
st.image(f"{imgs_folder}/mapa_tiempo_promedio_espera.png")

# Tiempo promedio de espera
st.markdown("## Comparación de Tiempo Promedio de Espera")
fig, ax = plt.subplots()
ax.bar(['Base', 'Tratamiento'], [tiempo_promedio_base, tiempo_promedio_treatment], color=['blue', 'orange'])
ax.set_ylabel('Tiempo Promedio de Espera (minutos)')
ax.set_title('Comparación de Tiempo Promedio de Espera')
_ = [sp.set_visible(False) for sp in ax.spines.values()]

st.pyplot(fig)

# Correlación entre oferta y demanda
st.markdown(
    f"""
    ### Correlación entre oferta y demanda:

    | Indicador | Sin intervención | Con intervención | Impacto |
    |-----------|------------------|------------------|---------|
    | Correlación oferta-demanda | {correlacion_od_base["correlacion"].mean():.3f} | {correlacion_od_treatment["correlacion"].mean():.3f} | {color_markdown(correlacion_od_treatment["correlacion"].mean() - correlacion_od_base["correlacion"].mean())} |
    """
)

fig, ax = plt.subplots()
correlacion_od_base.set_index('hora')["correlacion"].plot(ax=ax, label='Base', color='blue')
correlacion_od_treatment.set_index('hora')["correlacion"].plot(ax=ax, label='Tratamiento', color='orange')
ax.set_ylabel('Correlación')
ax.set_title('Comparación de Correlación entre Oferta y Demanda')
ax.legend()
_ = [sp.set_visible(False) for sp in ax.spines.values()]
st.pyplot(fig)
