import pandas as pd
import streamlit as st
from nexo.data.territorial_demo import INVESTMENTS, INVESTMENT_SKILL_DEMAND
from nexo.ui.theme import header


def render(ctx):
    header('DEMANDA FUTURA','Radar de Investimentos','Antecipar a demanda de competências antes que os postos de trabalho virem vagas abertas.')
    st.caption('🧪 **MVP:** carteira demonstrativa. Na implantação, cada registro terá fonte, evidência, responsável, estágio e data de última verificação.')

    inv=pd.DataFrame(INVESTMENTS)
    cols=st.columns(4)
    cols[0].metric('Projetos monitorados',len(inv))
    cols[1].metric('CAPEX sinalizado',f"R$ {inv['Investimento (R$ mi)'].sum():,.0f} mi".replace(',','.'))
    cols[2].metric('Empregos potenciais',f"{int(inv['Empregos estimados'].sum()):,}".replace(',','.'))
    cols[3].metric('Alta prioridade',int((inv['Prioridade']=='Alta').sum()))

    st.subheader('Carteira de investimentos com impacto em capital humano')
    fase=st.multiselect('Filtrar fase',sorted(inv['Fase'].unique()),default=list(sorted(inv['Fase'].unique())))
    filtered=inv[inv['Fase'].isin(fase)] if fase else inv.iloc[0:0]
    st.dataframe(filtered,use_container_width=True,hide_index=True)

    left,right=st.columns([1.25,1])
    with left:
        st.subheader('Empregos projetados por iniciativa')
        st.bar_chart(filtered.set_index('Projeto')[['Empregos estimados']],use_container_width=True)
    with right:
        st.subheader('Skills que o território precisará antecipar')
        skills=pd.DataFrame(INVESTMENT_SKILL_DEMAND)
        st.bar_chart(skills.set_index('Skill')[['Demanda projetada']],use_container_width=True)

    st.subheader('Como o NEXO transforma investimento em planejamento')
    st.markdown('**Investimento identificado** → setor e horizonte → ocupações prováveis → competências → comparação com a base local → gap → recomendação de trilhas e mobilização de parceiros.')
    st.warning('A projeção de empregos e skills não deve ser tratada como promessa de contratação. O NEXO mantém **demanda projetada**, **vaga efetivamente publicada** e **contratação verificada** como objetos distintos.')
