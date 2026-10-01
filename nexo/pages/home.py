import pandas as pd
import streamlit as st
from nexo.data.catalog import SKILL_DEMAND_COUNTS,GAP_COUNTS
from nexo.data.territorial_demo import TERRITORIAL_KPIS, VACANCY_KPIS, INVESTMENTS
from nexo.ui.theme import header


def render(ctx):
    header('GESTOR PÚBLICO','Inteligência territorial de capital humano','Quem é a força de trabalho, o que a economia demanda agora, o que demandará amanhã e onde estão os gaps que a política pública pode reduzir.')
    st.caption('🧪 Novos painéis territoriais e radares usam dados demonstrativos nesta versão do MVP. O motor de demanda empresarial, skills e revisão humana permanece conectado ao backend real.')

    cols=st.columns(4)
    cols[0].metric('Força de trabalho estimada',f"{TERRITORIAL_KPIS['economically_active']:,}".replace(',','.'))
    cols[1].metric('Vagas detectadas — 30d',f"{VACANCY_KPIS['active_30d']:,}".replace(',','.'))
    cols[2].metric('Investimentos monitorados',len(INVESTMENTS))
    cols[3].metric('Participantes NEXO','200')

    st.subheader('As quatro perguntas do planejamento')
    a,b,c,d=st.columns(4)
    with a:
        st.markdown('### 1 · Território')
        st.write('Quem pode trabalhar? Qual o perfil etário, de sexo/gênero e escolaridade?')
        st.caption('IBGE / SIDRA + RAIS')
    with b:
        st.markdown('### 2 · Demanda atual')
        st.write('Quem está contratando agora e quais competências aparecem nas vagas?')
        st.caption('Novo CAGED + Radar de Vagas + Empresas')
    with c:
        st.markdown('### 3 · Demanda futura')
        st.write('Quais investimentos podem alterar a estrutura ocupacional nos próximos meses?')
        st.caption('Radar de Investimentos')
    with d:
        st.markdown('### 4 · Gap')
        st.write('A população local possui as competências requeridas? Qual formação fecha a menor distância?')
        st.caption('Skills Intelligence + Matching')

    st.markdown('---')
    left,right=st.columns(2)
    with left:
        st.subheader('Skills mais demandadas no universo NEXO')
        st.bar_chart(pd.DataFrame({'Skill':list(SKILL_DEMAND_COUNTS),'Demanda':list(SKILL_DEMAND_COUNTS.values())}).set_index('Skill'))
    with right:
        st.subheader('Maiores gaps na base de participantes')
        st.bar_chart(pd.DataFrame({'Skill':list(GAP_COUNTS),'Participantes':list(GAP_COUNTS.values())}).set_index('Skill'))

    st.success('**43 participantes** estão a até **2 competências** de uma oportunidade ativa no universo demonstrativo. O objetivo da nova arquitetura é contextualizar esse número com a realidade territorial, vagas externas e investimentos futuros.')
    st.markdown('**Fluxo analítico:** Território + Mercado de Trabalho + Radar de Vagas + Radar de Investimentos → Skills Intelligence → Gap → Formação → Matching → Contratação → Permanência → Evidência.')
