import pandas as pd
import streamlit as st
from nexo.data.catalog import SKILL_DEMAND_COUNTS,GAP_COUNTS
from nexo.ui.theme import header

def render(ctx):
    header('VISÃO GERAL','Da demanda ao resultado','Inteligência para formar pessoas para oportunidades reais — e verificar os resultados produzidos.')
    cols=st.columns(5); vals=[('Participantes','200'),('Empresas','18'),('Demandas/Vagas','112'),('Skills','47'),('RET90 validados','26')]
    for c,(a,b) in zip(cols,vals): c.metric(a,b)
    l,r=st.columns(2)
    with l: st.subheader('Skills mais demandadas'); st.bar_chart(pd.DataFrame({'Skill':list(SKILL_DEMAND_COUNTS),'Demanda':list(SKILL_DEMAND_COUNTS.values())}).set_index('Skill'))
    with r: st.subheader('Maiores gaps'); st.bar_chart(pd.DataFrame({'Skill':list(GAP_COUNTS),'Participantes':list(GAP_COUNTS.values())}).set_index('Skill'))
    st.info('**43 participantes** estão a até **2 competências** de uma vaga ativa.')
    st.dataframe(pd.DataFrame({'Etapa':['Cadastrados','Diagnosticados','Trilha recomendada','Iniciaram formação','Concluíram','Encaminhados','Contratados','RET90 validado'],'Pessoas':[200,180,126,98,81,63,38,26]}),use_container_width=True,hide_index=True)
