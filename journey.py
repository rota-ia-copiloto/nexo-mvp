import streamlit as st
from nexo.ui.theme import header
from nexo.ui.state import advance

def render(ctx):
    header('JORNADA','Ana Souza','Cada transição relevante vira um evento verificável.')
    stage=st.session_state.ana_stage
    events=[('10 JAN','Cadastro',1),('12 JAN','Diagnóstico',1),('14 JAN','Trilha recomendada',1),('20 JAN','Formação iniciada',2),('20 FEV','Formação concluída',3),('22 FEV','Match Empresa Alfa',4),('10 MAR','Contratação',5),('08 JUN','90 dias',6),('10 JUN','Outcome validado',7)]
    for date,label,req in events: st.write(('✓' if stage>=req else '○')+f' **{date}** — {label}')
    if stage==5 and st.button('Simular permanência de 90 dias',type='primary'): advance(6,'Outcomes')
