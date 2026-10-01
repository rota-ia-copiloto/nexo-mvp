from types import SimpleNamespace
import streamlit as st
from nexo.db.factory import get_repository
from nexo.services.matching import MatchingService
from nexo.services.outcomes import OutcomeService
from nexo.services.skills import SkillsService
from nexo.services.validation import validate_demo
from nexo.services.supabase_edge import EdgeFunctionClient
from nexo.ui.theme import apply_theme, footer
from nexo.ui.state import init_state, reset
from nexo.pages import home,territorial,labor_market,investments,vacancy_radar,market,companies,participants,training,matching,journey,outcomes,evidence,graph,cpsi,participant_mode

def run():
    st.set_page_config(page_title='NEXO — MVP CPSI',page_icon='🔗',layout='wide',initial_sidebar_state='expanded')
    apply_theme(); init_state(); repo=get_repository()
    if repo.__class__.__name__=='DemoRepository': validate_demo(repo)
    ctx=SimpleNamespace(repo=repo,matching=MatchingService(repo),outcomes=OutcomeService(repo),skills=SkillsService(repo),edge=EdgeFunctionClient.from_env())
    st.sidebar.markdown('# 🔗 NEXO'); st.sidebar.caption('Inteligência de Competências e Resultados')
    role=st.sidebar.selectbox('Modo de demonstração',['Gestor Público','Empresa','Participante'],key='selected_role')
    st.sidebar.markdown('---'); st.sidebar.caption(f'Backend: {repo.__class__.__name__.replace("Repository","")}')
    if st.sidebar.button('Resetar demonstração'): reset(); st.rerun()
    if role=='Participante': participant_mode.render(ctx)
    elif role=='Empresa': companies.render(ctx)
    else:
        options=['Visão Geral','Visão Territorial','Mercado de Trabalho','Radar de Investimentos','Radar de Vagas','Skills Intelligence','Skills Graph']
        if st.session_state.nav not in options: st.session_state.nav='Visão Geral'
        nav=st.sidebar.radio('Navegação',options,key='nav')
        mapping={'Visão Geral':home,'Visão Territorial':territorial,'Mercado de Trabalho':labor_market,'Radar de Investimentos':investments,'Radar de Vagas':vacancy_radar,'Skills Intelligence':market,'Skills Graph':graph}
        mapping[nav].render(ctx)
    footer()
