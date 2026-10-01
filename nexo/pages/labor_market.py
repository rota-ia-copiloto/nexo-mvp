import pandas as pd
import streamlit as st
from nexo.data.territorial_demo import CAGED_MONTHLY, FORMAL_SECTORS, OCCUPATION_MOVEMENT
from nexo.ui.theme import header


def render(ctx):
    header('MERCADO DE TRABALHO','Mercado de Trabalho','O que está acontecendo agora no emprego formal — e onde surgem sinais para a política de qualificação.')
    st.caption('🧪 **MVP:** série demonstrativa inspirada na estrutura de RAIS/Novo CAGED. Conectores oficiais serão adicionados na fase de integração de dados.')

    caged=pd.DataFrame(CAGED_MONTHLY)
    caged['Saldo']=caged['Admissões']-caged['Desligamentos']
    adm=int(caged['Admissões'].sum()); des=int(caged['Desligamentos'].sum()); saldo=int(caged['Saldo'].sum())
    cols=st.columns(4)
    cols[0].metric('Admissões — janela exibida',f'{adm:,}'.replace(',','.'))
    cols[1].metric('Desligamentos — janela exibida',f'{des:,}'.replace(',','.'))
    cols[2].metric('Saldo',f'{saldo:+,}'.replace(',','.'))
    cols[3].metric('Meses com saldo positivo',f"{int((caged['Saldo']>0).sum())}/{len(caged)}")

    left,right=st.columns([1.35,1])
    with left:
        st.subheader('Fluxo mensal de emprego formal')
        st.line_chart(caged.set_index('Mês')[['Admissões','Desligamentos']],use_container_width=True)
    with right:
        st.subheader('Saldo mensal')
        st.bar_chart(caged.set_index('Mês')[['Saldo']],use_container_width=True)
        st.caption('Fonte prevista: Novo CAGED · periodicidade mensal.')

    st.subheader('Estrutura setorial do emprego')
    sectors=pd.DataFrame(FORMAL_SECTORS)
    a,b=st.columns([1.2,1])
    with a: st.bar_chart(sectors.set_index('Setor')[['Vínculos']],use_container_width=True)
    with b:
        st.dataframe(sectors,use_container_width=True,hide_index=True)
        st.caption('Fonte prevista: RAIS para estoque anual; Novo CAGED para movimentos recentes.')

    st.subheader('Ocupações com maior sinal de contratação')
    occ=pd.DataFrame(OCCUPATION_MOVEMENT)
    st.dataframe(occ,use_container_width=True,hide_index=True)
    st.info('O próximo passo analítico do NEXO é cruzar **movimento ocupacional + vagas abertas + investimentos anunciados + skills empresariais validadas** antes de recomendar expansão ou contratação de uma trilha formativa.')
