import hashlib
import streamlit as st
from nexo.ui.theme import header

def render(ctx):
    header('EVIDENCE LEDGER','OUT001 — Ana Souza','A trilha não prova causalidade; prova que o evento declarado é reproduzível e verificável.')
    ev=ctx.outcomes.evidence_for('OUT001'); st.dataframe(ev[['evidence_id','evidence_type','source','captured_at','strength','status']],use_container_width=True,hide_index=True)
    st.markdown('### Integridade e rastreabilidade'); h=hashlib.sha256(b'EV003-demo').hexdigest(); st.code(f'EV003\nSHA-256: {h}\nRegra vinculada: RET90_V1.0\nAlterações: 0')
    st.markdown('### Checklist para auditor'); st.checkbox('Contratação verificada',value=True,disabled=True); st.checkbox('90 dias transcorridos',value=True,disabled=True); st.checkbox('Evidência mínima atendida',value=True,disabled=True); st.checkbox('Sem alerta crítico de fraude',value=True,disabled=True)
    if st.session_state.ana_stage>=6 and st.button('Enviar para validação independente',type='primary'): st.session_state.selected_role='Auditor'; st.rerun()
