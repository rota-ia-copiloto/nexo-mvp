import pandas as pd
import streamlit as st
from nexo.data.cpsi_demo import QUALIFICATION_DEMAND, COMPETENCY_MATRIX, LEARNING_PATHS
from nexo.ui.theme import header


def render(ctx):
    header('ENGENHARIA EDUCACIONAL','Qualificação & Competências','Da demanda do setor produtivo ao objetivo de aprendizagem: competências, gaps, desenho formativo e avaliação em uma única cadeia de evidências.')
    st.caption('🧪 **MVP:** dados demonstrativos. A lógica foi desenhada para receber sinais do Radar de Vagas, empresas, investimentos e bases municipais, preservando fonte e período de referência.')

    demand = pd.DataFrame(QUALIFICATION_DEMAND)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric('Ocupações priorizadas',len(demand))
    c2.metric('Vagas sinalizadas',int(demand['Vagas'].sum()))
    c3.metric('Empresas demandantes',int(demand['Empresas demandantes'].sum()))
    c4.metric('Gaps críticos',int((demand['Prioridade']=='Crítica').sum()))
    c5.metric('Trilhas em desenho',len(LEARNING_PATHS))

    st.subheader('1 · Demanda de competências')
    st.dataframe(demand,use_container_width=True,hide_index=True)

    occupation = st.selectbox('Explorar matriz de competências', list(COMPETENCY_MATRIX.keys()))
    matrix = pd.DataFrame(COMPETENCY_MATRIX[occupation])
    left,right = st.columns([1.45,1])
    with left:
        st.subheader(f'2 · Matriz de competências — {occupation}')
        st.dataframe(matrix,use_container_width=True,hide_index=True)
    with right:
        st.subheader('Gap médio por competência')
        st.bar_chart(matrix.set_index('Competência')[['Gap']],use_container_width=True)
        biggest=matrix.sort_values('Gap',ascending=False).iloc[0]
        st.info(f"**Maior distância observada:** {biggest['Competência']} · gap de {int(biggest['Gap'])} nível(is).")

    st.subheader('3 · Engenharia educacional')
    st.markdown('**Gap de competência → objetivo de aprendizagem → experiência formativa → instrumento de avaliação → resultado esperado → validação no trabalho**')
    paths=pd.DataFrame(LEARNING_PATHS)
    st.dataframe(paths,use_container_width=True,hide_index=True)

    with st.expander('➕ Prototipar uma intervenção formativa'):
        gap=st.text_input('Gap / competência-alvo',value='WMS / sistemas de armazém')
        obj=st.text_area('Objetivo de aprendizagem',value='Executar corretamente rotinas essenciais de WMS em um fluxo simulado de armazém.')
        method=st.text_input('Experiência / intervenção',value='Laboratório prático + simulação')
        assess=st.text_input('Instrumento de avaliação',value='Pré/pós-teste + tarefa prática')
        target=st.text_input('Meta de aprendizagem',value='+25% no domínio da competência')
        if st.button('Registrar protótipo',key='save_learning_proto'):
            st.session_state['learning_prototype']={"gap":gap,"objective":obj,"method":method,"assessment":assess,"target":target}
            st.success('Protótipo registrado na sessão demonstrativa. Em produção, este registro será versionado e ligado ao experimento correspondente.')

    st.success('**Leitura CPSI:** esta página transforma demanda produtiva em arquitetura de aprendizagem mensurável — sem exigir que o NEXO seja um LMS. O foco é provar a cadeia lógica e a capacidade de testar se a formação fecha o gap identificado.')
