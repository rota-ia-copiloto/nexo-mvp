import pandas as pd
import streamlit as st
from nexo.data.territorial_demo import VACANCY_KPIS, VACANCY_BY_OCCUPATION, VACANCY_SKILLS, VACANCY_SOURCES
from nexo.ui.theme import header


def render(ctx):
    header('DEMANDA ATUAL','Radar de Vagas','Sinais distribuídos na internet convertidos em inteligência municipal de demanda por ocupações e competências.')
    st.caption('🧪 **MVP:** números demonstrativos. A coleta futura deve respeitar termos de uso, robots.txt, autenticação e demais restrições de cada fonte. O produto não pressupõe raspagem irrestrita da internet.')

    cols=st.columns(4)
    cols[0].metric('Vagas detectadas — 30d',f"{VACANCY_KPIS['active_30d']:,}".replace(',','.'))
    cols[1].metric('Novas — 7d',f"{VACANCY_KPIS['new_7d']:,}".replace(',','.'))
    cols[2].metric('Empresas identificadas',VACANCY_KPIS['companies'])
    cols[3].metric('Duplicidades removidas',VACANCY_KPIS['deduplicated'])

    left,right=st.columns([1.2,1])
    with left:
        st.subheader('Vagas por família ocupacional')
        occ=pd.DataFrame(VACANCY_BY_OCCUPATION)
        st.bar_chart(occ.set_index('Ocupação'),use_container_width=True)
    with right:
        st.subheader('Pipeline de ingestão')
        st.code('fontes permitidas\n  ↓\ncoleta\n  ↓\nnormalização + localização\n  ↓\ndeduplicação\n  ↓\nLLM extrai skills\n  ↓\npgvector normaliza\n  ↓\nRadar municipal',language=None)
        st.caption('O mesmo motor de taxonomia que já funciona na demanda empresarial pode estruturar descrições de vagas externas.')

    st.subheader('Competências mais citadas nas vagas')
    skills=pd.DataFrame(VACANCY_SKILLS)
    st.dataframe(skills,use_container_width=True,hide_index=True)

    st.subheader('Fontes de coleta e governança')
    sources=pd.DataFrame(VACANCY_SOURCES)
    st.dataframe(sources,use_container_width=True,hide_index=True)
    st.info('Cada vaga deverá preservar **URL/fonte, data de publicação, data de coleta e identificador de deduplicação**. Vagas expiradas permanecem no histórico para análise temporal, mas deixam de alimentar o estoque de oportunidades ativas.')
