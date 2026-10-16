"""Página standalone para apresentar o protótipo do Radar de Vagas."""
import streamlit as st
from nexo_radar_vagas import render_radar_vagas

st.set_page_config(page_title="NEXO | Radar de Vagas (Demo)", page_icon="🧭", layout="wide")
render_radar_vagas()
