import streamlit as st
from nexo.ui.theme import header

def render(ctx):
    header('QUALIFICAÇÃO','Operações Logísticas + ERP','A formação é justificada por gaps concretos de uma demanda real.')
    cols=st.columns(4)
    for c,(a,b) in zip(cols,[('Carga horária','40h'),('Pessoas aderentes',32),('Vagas associadas',18),('Skills',3)]): c.metric(a,b)
    st.info('18 vagas ativas demandam pelo menos 2 destas competências; 32 participantes apresentam gaps compatíveis.')
