import pandas as pd
import streamlit as st
from nexo.data.territorial_demo import MUNICIPALITY, TERRITORIAL_KPIS, AGE_GENDER, EDUCATION, SOURCE_CATALOG
from nexo.ui.theme import header


def _fmt_int(v):
    return f"{int(v):,}".replace(",", ".")


def render(ctx):
    header('TERRITÓRIO','Visão Territorial','Quem compõe a força de trabalho do município — antes de decidir o que ofertar em qualificação.')
    st.caption('🧪 **MVP:** valores demonstrativos. As etiquetas de fonte indicam os conectores previstos; não representam carga oficial em tempo real.')

    a,b,c = st.columns([1.2,1,1])
    with a:
        st.selectbox('Município', [f"{MUNICIPALITY['name']}/{MUNICIPALITY['state']}"], disabled=True)
    with b:
        st.text_input('Código IBGE', MUNICIPALITY['ibge_code'], disabled=True)
    with c:
        st.selectbox('Ano de referência', ['2026 — visão integrada','2025','2024'], disabled=True)

    cols=st.columns(4)
    cards=[
        ('População',_fmt_int(TERRITORIAL_KPIS['population']),'Fonte prevista: IBGE'),
        ('18–64 anos',_fmt_int(TERRITORIAL_KPIS['working_age']),'base potencial de trabalho'),
        ('Economicamente ativos',_fmt_int(TERRITORIAL_KPIS['economically_active']),'estimativa demonstrativa'),
        ('Empregos formais',_fmt_int(TERRITORIAL_KPIS['formal_jobs']),'Fonte prevista: RAIS'),
    ]
    for col,(label,value,help_text) in zip(cols,cards): col.metric(label,value,help=help_text)

    left,right=st.columns([1.25,1])
    with left:
        st.subheader('População em idade ativa por faixa etária e sexo')
        df=pd.DataFrame(AGE_GENDER).set_index('Faixa etária')
        st.bar_chart(df,use_container_width=True)
        st.caption('Recorte demonstrativo. No conector oficial, os grupos serão derivados dos dados IBGE disponíveis para o município.')
    with right:
        st.subheader('Escolaridade da força de trabalho')
        edu=pd.DataFrame(EDUCATION).set_index('Escolaridade')
        st.bar_chart(edu,use_container_width=True)
        st.metric('Remuneração formal média',f"R$ {TERRITORIAL_KPIS['avg_formal_wage']:,.0f}".replace(',','.'))
        st.metric('Índice demonstrativo de formalização',f"{TERRITORIAL_KPIS['formalization_rate']:.1f}%".replace('.',','))

    st.subheader('Fontes que compõem a leitura territorial')
    st.dataframe(pd.DataFrame(SOURCE_CATALOG),use_container_width=True,hide_index=True)
    st.info('**Princípio do NEXO:** nenhum indicador deve aparecer sem período de referência, fonte e data de atualização. Quando houver divergência entre bases, o sistema preservará a proveniência em vez de substituir silenciosamente uma fonte por outra.')
