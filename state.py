import streamlit as st
DEFAULTS={"selected_role":"Gestor Público","nav":"Visão Geral","ana_stage":1,"alpha_analyzed":False,"alpha_validated":False,"alpha_training":False,"audit_decision":None}

def init_state():
    for k,v in DEFAULTS.items():
        if k not in st.session_state: st.session_state[k]=v
def reset():
    for k,v in DEFAULTS.items(): st.session_state[k]=v
def advance(stage:int,page:str|None=None):
    st.session_state.ana_stage=max(st.session_state.ana_stage,stage)
    if page: st.session_state.nav=page
    st.rerun()
