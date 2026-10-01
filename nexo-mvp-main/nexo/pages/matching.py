import pandas as pd
import streamlit as st
from nexo.ui.theme import header
from nexo.ui.state import advance

def render(ctx):
    header('MATCHING','Aderência explicável','Nenhum score sem decomposição de seus componentes.')
    stage=st.session_state.ana_stage; score,parts=ctx.matching.score('P001','J001',course_done=stage>=3)
    st.dataframe(pd.DataFrame([['Carlos Mendes','88%',1],['Júlia Rocha','79%',1],['Ana Souza',f'{score*100:.0f}%',0 if stage>=3 else 2],['Roberto Lima','44%',3]],columns=['Candidato','Match','Gap']),use_container_width=True,hide_index=True)
    cols=st.columns(4)
    for c,(k,v) in zip(cols,[('Skill Fit',parts['skill_fit']),('Experiência',parts['experience_fit']),('Disponibilidade',parts['availability_fit']),('Preferência',parts['preference_fit'])]): c.metric(k,f'{v*100:.0f}%')
    st.code(f'MATCH_V0.9\nScore = SkillFit×0.65 + Experience×0.15 + Availability×0.10 + Preference×0.10\nResultado: {score*100:.0f}%')
    if stage==3 and st.button('Registrar encaminhamento para Empresa Alfa',type='primary'): advance(4,'Matching')
    if stage==4 and st.button('Registrar contratação',type='primary'): advance(5,'Jornada')
