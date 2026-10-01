import pandas as pd
import streamlit as st
from nexo.ui.theme import header
from nexo.ui.state import advance

def render(ctx):
    header('VALIDAÇÃO INDEPENDENTE','Fila de auditoria','Regra, evidência, risco e decisão são visualmente separados.')
    st.dataframe(pd.DataFrame([['OUT001','RET90','3/2','Sem flags','Pronto para decisão'],['OUT021','RET90','1/2','Evidência faltante','Pendente'],['OUT029','HIRE','2/2','Duplicidade','Atenção']],columns=['Outcome','Regra','Evidências','Risco','Status']),use_container_width=True,hide_index=True)
    st.markdown('### OUT001 — Ana Souza')
    c1,c2,c3,c4=st.columns(4)
    c1.info('**REGRA**\n\nRET90 v1.0\n\n≥ 90 dias')
    c2.info('**DADOS**\n\n92 dias\n\nVínculo ativo')
    c3.info('**EVIDÊNCIA**\n\n2 fontes A\n\n1 fonte B')
    c4.success('**RISCO**\n\nSem flag crítico')
    st.caption('O auditor decide; o sistema apenas organiza regra, dados e evidências.')
    if st.session_state.ana_stage>=6:
        a,b,c=st.columns(3)
        if a.button('Validar OUT001',type='primary'): st.session_state.audit_decision='VALIDATED'; advance(7,'Jornada')
        if b.button('Solicitar evidência'): st.session_state.audit_decision='MORE_EVIDENCE'; st.warning('Solicitação registrada na sessão da demo.')
        if c.button('Rejeitar'): st.session_state.audit_decision='REJECTED'; st.error('Rejeição registrada na sessão da demo.')
