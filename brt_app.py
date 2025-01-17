"""Streamlit App for next arrival predictions at BRT Vaz Lobo station"""

from math import floor

import pandas as pd
import requests
from requests import Response

import folium
from folium.map import Icon
from folium.plugins import MiniMap

import streamlit as st
from streamlit_folium import st_folium
from streamlit_extras.let_it_rain import rain


st.title("O BRT tá chegando em Vaz Lobo?")


@st.cache_data(
    ttl=60,
    show_spinner="Consultando os dados da API do BRT...",
)
def get_data() -> list[tuple[float, float], Response]:
    """Get predictions of next arrivals at Vaz Lobo station from the BRT API

    Returns:
       location (list[float, float]): The location of Vaz Lobo station
       response (Response): The predictions for next BRT arrivals
    """

    vaz_lobo_station_location = [-22.85647, -43.32815]

    response = requests.get(
        "https://api.mobilidade.rio/predictor/?stop_id=3084BC0001U2", timeout=30
    )

    return vaz_lobo_station_location, response


loc, results = get_data()

if results.status_code != 200:
    st.error("Não foi possível recuperar os dados da API... Tente novamente mais tarde")

    json_results = results.json()

    st.json(
        {
            "status_code": results.status_code,
            "code": json_results["code"],
            "message": json_results["message"],
        }
    )

else:
    json_results = results.json()["results"]

    brt_predictions = (
        pd.DataFrame(json_results)
        .query("estimated_time_arrival > 0 & estimated_time_arrival < 16")
        .sort_values("estimated_time_arrival")
        .reset_index(drop=True)
    )

    if brt_predictions.shape[0] < 1:
        st.error("Sem previsões no momento... Tente mais tarde")
        rain(
            emoji="😭",
            font_size=54,
            falling_speed=5,
            animation_length=10,
        )

    else:
        next_arrival = brt_predictions["estimated_time_arrival"].iloc[0]
        minutes = int(next_arrival)
        seconds = (next_arrival - minutes) * 60

        st.info(
            f"O próximo BRT deve estar chegando em {minutes} minuto(s) e {seconds:.0f} segundo(s)..."
        )

        vaz_lobo = folium.Map(
            location=loc,
            zoom_start=11,
            scrollWheelZoom=False,
        )

        for result in brt_predictions.to_dict(orient="records"):
            if result["estimated_time_arrival"] <= 0:
                continue

            arrival_time = floor(result["estimated_time_arrival"])

            folium.Marker(
                location=[result["latitude"], result["longitude"]],
                icon=Icon(color="orange", prefix="fa", icon="bus"),
                tooltip=f"Tempo de chegada desse BRT: {arrival_time:.0f} min",
            ).add_to(vaz_lobo)

        folium.Marker(
            location=loc,
            tooltip="Estação BRT Vaz Lobo",
            icon=Icon(color="blue", prefix="fa", icon="signs-post"),
        ).add_to(vaz_lobo)

        MiniMap().add_to(vaz_lobo)

        st_data = st_folium(vaz_lobo)
