import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

datos = "../datos"
input_folder = f"{datos}/calculos_gtfs"
imgs_folder = "images"


# Estadísticas generales del feed
st.markdown("## Estadísticas generales del feed")

oferta = pd.read_pickle(f"{datos}/od_celular/oferta_zona_hora.pkl")\
        .rename(lambda x: f"Zona {x}").round(0)
demanda = pd.read_pickle(f"{datos}/od_celular/viajes_origen_hora_zona.pkl")\
        .rename(lambda x: f"Zona {x}").round(0)

st.markdown("### Oferta de viajes (basado en GTFS)")
st.write(oferta)

fig, ax = plt.subplots()
oferta.sum().plot(ax=ax)
ax.set_title("Oferta de viajes por hora")
st.pyplot(fig)

fig, ax = plt.subplots(figsize=(6, 9))
oferta.sum(axis=1).sort_values(ascending=True).plot.barh(ax=ax)
ax.set_title("Oferta de viajes por zona")
st.pyplot(fig)

st.markdown("### Demanda de viajes (basado en datos celular)")
st.write(demanda)

fig, ax = plt.subplots()
demanda.sum().plot(ax=ax)
ax.set_title("Demanda de viajes por hora")
st.pyplot(fig)


st.markdown("### Estadísticas generales por hora")

fts_base = pd.read_csv(f"{input_folder}/feed_time_series_base.csv")
st.write(fts_base)





# st.markdown("### Tratamiento")
# fts_treatment = pd.read_csv(f"{input_folder}/feed_time_series_treatment.csv")
# st.write(fts_treatment)

# fts_impacto = fts_treatment.set_index("datetime") - fts_base.set_index("datetime")

# def style_negative(v):
#     if v < 0:
#         return 'color:red;'
#     elif v > 0:
#         return 'color:green;'
#     else:
#         return ''

# fts_impacto = fts_impacto.style.map(style_negative)

# st.markdown("### Impacto")
# st.write(fts_impacto)
