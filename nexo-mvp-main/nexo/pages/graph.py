import graphviz
import streamlit as st
from nexo.ui.theme import header

def render(ctx):
    header('SKILLS GRAPH','Mapa de relações','Pessoa ↔ skill ↔ curso ↔ ocupação ↔ vaga.')
    dot=graphviz.Digraph(); dot.attr(rankdir='LR');
    for n,l in [('ANA','Ana'),('EXCEL','Excel'),('ERP','ERP'),('LOG','Logística'),('EST','Estoque'),('JOB','Assistente de Logística'),('COURSE','Curso Logística + ERP')]: dot.node(n,l)
    for a,b,l in [('ANA','EXCEL','possui'),('ANA','JOB','alvo'),('JOB','ERP','requer'),('JOB','LOG','requer'),('JOB','EST','requer'),('ANA','ERP','gap'),('ANA','LOG','gap'),('ANA','COURSE','recomendação'),('COURSE','ERP','desenvolve'),('COURSE','LOG','desenvolve')]: dot.edge(a,b,l)
    st.graphviz_chart(dot,use_container_width=True)
