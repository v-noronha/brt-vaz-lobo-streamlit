import streamlit as st

import requests

import folium
from folium.map import Icon
from streamlit_folium import st_folium

import pandas as pd

st.title("O BRT tá chegando em Vaz Lobo?")


@st.cache_data(
    ttl=60,
    show_spinner="Puxando os dados da API do BRT...",
)
def get_data():
    # tcvlo = requests.get("https://api.mobilidade.rio/gtfs/stops/?stop_code=TCVLO")
    # response_json = tcvlo.json()
    # loc = [
    #     response_json["results"][0]["stop_lat"],
    #     response_json["results"][0]["stop_lon"],
    # ]

    loc = [-22.85647, -43.32815]

    results = requests.get("https://api.mobilidade.rio/predictor/?stop_id=3084BC0001U2")

    return loc, results


loc, results = get_data()

next_brts = (
    pd.DataFrame(results.json()["results"])
    .sort_values("estimated_time_arrival")
    .query("estimated_time_arrival > 0")
)

next_arrival = next_brts.head(1)["estimated_time_arrival"].item()
minutes = int(next_arrival)
seconds = (next_arrival - minutes) * 60

st.info(
    f"O próximo BRT deve estar chegando em {minutes} minuto(s) e {seconds:.0f} segundo(s)..."
)

st.dataframe(next_brts)

vaz_lobo = folium.Map(
    location=loc,
    zoom_start=12,
    scrollWheelZoom=False,
)

for result in results.json()["results"]:
    if result["estimated_time_arrival"] <= 0:
        continue

    folium.Marker(
        location=[result["latitude"], result["longitude"]],
        icon=Icon(color="orange", prefix="fa", icon="bus"),
        tooltip=f"ETA: {result['estimated_time_arrival']:.2f} min",
    ).add_to(vaz_lobo)

folium.Marker(
    location=loc,
    tooltip="Estação BRT Vaz Lobo",
    icon=Icon(color="blue", prefix="fa", icon="signs-post"),
).add_to(vaz_lobo)

st_data = st_folium(vaz_lobo)