import streamlit as st
from nexo.ui.theme import header

def render(ctx):
    header('LABORATÓRIO CPSI','Hipóteses e experimentos','O software existe para testar hipóteses de inovação pública.')
    st.warning('Resultados sintéticos — não representam resultados reais do CPSI.')
    for r in ctx.repo.table('experiments').itertuples():
        st.subheader(r.name); a,b,c=st.columns(3); a.metric('Amostra',r.sample); b.metric('Meta',f'{r.target*100:.0f}%'); c.metric('Resultado sintético',f'{r.result*100:.1f}%'); st.progress(min(float(r.result),1.0))
