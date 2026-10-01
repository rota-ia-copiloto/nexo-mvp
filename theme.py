import streamlit as st

CSS="""<style>
.block-container{padding-top:1.3rem;padding-bottom:3rem;max-width:1400px}.nexo-hero{padding:1.5rem 1.6rem;border-radius:18px;border:1px solid rgba(120,120,120,.2);background:linear-gradient(135deg,rgba(120,120,120,.06),rgba(120,120,120,.01));margin-bottom:1rem}.nexo-kicker{font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.65}.nexo-title{font-size:2rem;font-weight:750;margin:.15rem 0}.nexo-sub{opacity:.72}.audit-box{border:1px solid rgba(120,120,120,.25);border-radius:14px;padding:1rem;margin:.5rem 0}.small-note{font-size:.8rem;opacity:.7}
</style>"""
def apply_theme(): st.markdown(CSS,unsafe_allow_html=True)
def header(kicker,title,subtitle): st.markdown(f'<div class="nexo-hero"><div class="nexo-kicker">{kicker}</div><div class="nexo-title">{title}</div><div class="nexo-sub">{subtitle}</div></div>',unsafe_allow_html=True)
def footer(): st.markdown('---'); st.caption('NEXO — Ambiente demonstrativo. Dados inteiramente sintéticos para prova de conceito do CPSI.')
