import streamlit as st
from nexo.ui.theme import header
from nexo.ui.state import advance


def render(ctx):
    header('PESSOAS','Ana Souza','Da competência atual até um outcome verificável.')
    stage=st.session_state.ana_stage
    score,parts=ctx.matching.score('P001','J001',course_done=stage>=3)
    l,r=st.columns([1.15,1])
    with l:
        st.subheader('Competências')
        levels={
            'Microsoft Excel':3,
            'Atendimento':3,
            'Rotinas Administrativas':3,
            'Gestão de Estoque':2 if stage>=3 else 1,
            'ERP':2 if stage>=3 else 0,
            'Logística Operacional':2 if stage>=3 else 0,
        }
        for name,lvl in levels.items():
            st.write(f'**{name}** — {lvl}/4')
            st.progress(lvl/4)
    with r:
        st.subheader('Assistente de Logística — Empresa Alfa')
        st.metric('Aderência atual',f'{score*100:.0f}%')
        st.markdown('✓ Excel adequado  \n✓ Experiência relacionada')
        if stage<3:
            st.markdown('◐ Estoque parcial  \n✕ ERP  \n✕ Logística Operacional')
            st.info('Faltam **2 competências críticas**.')
        else:
            st.markdown('✓ Estoque  \n✓ ERP  \n✓ Logística Operacional')
            st.success('Principais gaps reduzidos.')

    st.markdown('### Próxima decisão')
    if stage==1:
        st.write('Trilha recomendada: **Operações Logísticas + ERP — 40h**.')
        if st.button('Iniciar trajetória da Ana',type='primary'):
            advance(2,'Participantes')
    elif stage==2:
        st.write('Formação em andamento.')
        if st.button('Concluir formação',type='primary'):
            advance(3,'Matching')
    elif stage==3:
        st.success('Formação concluída; aderência estimada agora é 83%.')
        if st.button('Avançar para matching',type='primary'):
            advance(4,'Matching')
    elif stage==4:
        st.info('Match elegível para encaminhamento.')
        if st.button('Registrar contratação',type='primary'):
            advance(5,'Jornada')
    elif stage==5:
        st.info('Contratação registrada.')
        if st.button('Avançar 90 dias',type='primary'):
            advance(6,'Outcomes')
    elif stage==6:
        st.warning('RETENTION_90 candidato: aguardando validação independente.')
        if st.button('Abrir Evidence Ledger',type='primary'):
            st.session_state.nav='Evidence Ledger'
            st.rerun()
    else:
        st.success('Outcome RETENTION_90 validado. Trajetória demonstrativa concluída.')
