import streamlit as st
from nexo.ui.theme import header

def render(ctx):
    header('MINHA JORNADA','Olá, Ana','Uma linguagem simples para quem precisa decidir o próximo passo.')
    stage=st.session_state.ana_stage
    if stage<3: st.info('Você já possui competências relevantes. Recomendamos desenvolver **ERP** e **Logística Operacional**.'); st.write('**Próximo passo:** Operações Logísticas + ERP — 40 horas')
    else: st.success('Formação concluída. Seu perfil foi atualizado.'); st.metric('Aderência estimada','83%')
    if stage>=5: st.success('Contratação registrada na Empresa Alfa.')
    if stage>=7: st.success('Permanência de 90 dias validada.')
