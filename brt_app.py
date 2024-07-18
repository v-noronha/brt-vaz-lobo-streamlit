"""Streamlit App for next arrival predictions at BRT Vaz Lobo station"""

from math import floor

import pandas as pd
import requests
from requests import Response

import folium
from folium.map import Icon

import streamlit as st
from streamlit_folium import st_folium


st.title("O BRT tá chegando em Vaz Lobo?")


@st.cache_data(
    ttl=60,
    show_spinner="Consultando os dados da API do BRT...",
)
def get_data() -> list[list[float, float], Response]:
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
        pd.DataFrame(json_results)[
            ["codigo", "dataHora", "trip_short_name", "estimated_time_arrival"]
        ]
        .sort_values("estimated_time_arrival")
        .query("estimated_time_arrival > 0")
        .rename(
            columns={
                "trip_short_name": "linha",
                "estimated_time_arrival": "previsão de chegada (minutos)",
            }
        )
        .reset_index(drop=True)[["codigo", "linha", "previsão de chegada (minutos)"]]
    )

    next_arrival = brt_predictions["previsão de chegada (minutos)"].iloc[0]
    minutes = int(next_arrival)
    seconds = (next_arrival - minutes) * 60

    st.info(
        f"O próximo BRT deve estar chegando em {minutes} minuto(s) e {seconds:.0f} segundo(s)..."
    )

    st.dataframe(brt_predictions)

    vaz_lobo = folium.Map(
        location=loc,
        zoom_start=12,
        scrollWheelZoom=False,
    )

    for result in json_results:
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

    st_data = st_folium(vaz_lobo)
