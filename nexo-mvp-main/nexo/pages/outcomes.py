import pandas as pd
import streamlit as st
from nexo.ui.theme import header

def render(ctx):
    header('OUTCOMES','Do evento ao resultado','Outcome é regra versionada + evidência suficiente, não inferência generativa.')
    cols=st.columns(4)
    for c,(a,b) in zip(cols,[('Contratações',38),('Aderentes',31),('RET90',26),('RET180',11)]): c.metric(a,b)
    stage=st.session_state.ana_stage
    status='VALIDADO' if stage>=7 else ('AGUARDANDO AUDITOR' if stage>=6 else 'AINDA NÃO ELEGÍVEL')
    st.subheader('OUT001 — RETENTION_90'); st.metric('Status',status); result=ctx.outcomes.evaluate_retention90('OUT001'); st.code(f"RET90_V1.0\nDias observados: 92\nEvidência suficiente: {result['evidence_ok']}\nResultado técnico da regra: {result['result']}")
    if stage>=6 and st.button('Abrir Evidence Ledger'): st.session_state.nav='Evidence Ledger'; st.rerun()
