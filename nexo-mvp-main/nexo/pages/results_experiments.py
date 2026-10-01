import pandas as pd
import streamlit as st
from nexo.data.cpsi_demo import FUNNEL, EXPERIMENTS, EXPERIMENT_RESULTS, EQUITY_FUNNEL, BARRIERS, ECONOMICS, EMPLOYER_FEEDBACK
from nexo.ui.theme import header


def _money(v):
    return 'R$ ' + f'{v:,.0f}'.replace(',','.')


def render(ctx):
    header('CICLO EXPERIMENTAL','Resultados & Experimentos','Testar hipóteses, acompanhar a trajetória, medir aprendizagem e inserção, identificar desigualdades, calcular economicidade e registrar decisões baseadas em evidências.')
    st.caption('🧪 **MVP CPSI:** indicadores e resultados demonstrativos. O desenho privilegia rastreabilidade, comparabilidade e portas explícitas de decisão.')

    funnel=pd.DataFrame(FUNNEL)
    econ=ECONOMICS
    cards=st.columns(6)
    cards[0].metric('Participantes do piloto',econ['participants'])
    cards[1].metric('Conclusão',f"{econ['completers']/econ['participants']*100:.1f}%")
    cards[2].metric('Inserção até 90d',f"{econ['inserted']/econ['participants']*100:.1f}%")
    cards[3].metric('Permanência 90d',f"{econ['retained_90']/max(econ['inserted'],1)*100:.1f}%")
    cards[4].metric('Custo / concluinte',_money(econ['pilot_cost']/econ['completers']))
    cards[5].metric('Custo / inserido',_money(econ['pilot_cost']/econ['inserted']))

    tabs=st.tabs(['Visão geral','Experimentos','Equidade & Barreiras','Eficiência & Custo-benefício','Setor Produtivo'])

    with tabs[0]:
        st.subheader('Funil longitudinal do piloto')
        st.bar_chart(funnel.set_index('Etapa'),use_container_width=True)
        st.dataframe(funnel,use_container_width=True,hide_index=True)
        st.info('O NEXO preserva um identificador seguro por participante para permitir leitura longitudinal entre mobilização, inscrição, ingresso, participação, conclusão, encaminhamento, inserção e permanência.')

    with tabs[1]:
        st.subheader('Experiment Designer')
        st.dataframe(pd.DataFrame(EXPERIMENTS),use_container_width=True,hide_index=True)
        with st.expander('➕ Criar novo experimento',expanded=False):
            name=st.text_input('Nome',value='Trilha logística orientada por demanda empresarial')
            problem=st.text_area('Problema',value='Baixa aderência entre formação ofertada e competências efetivamente demandadas.')
            hypothesis=st.text_area('Hipótese',value='Trilha orientada por competências + acompanhamento ativo aumenta a conclusão e a inserção profissional.')
            population=st.text_input('População-alvo',value='Pessoas desempregadas de 18–44 anos interessadas em logística')
            comparator=st.selectbox('Estratégia de comparação',['Linha de base','Coorte anterior','Grupo comparável','Braço A × Braço B','Antes × depois'])
            selected=st.multiselect('Indicadores',['Conclusão','Evasão','Ganho de competências','Inserção 90 dias','Permanência 180 dias','Renda','Satisfação empresarial','Custo por inserido'],default=['Conclusão','Ganho de competências','Inserção 90 dias','Custo por inserido'])
            if st.button('Criar experimento',key='create_experiment'):
                st.session_state['draft_experiment']={"name":name,"problem":problem,"hypothesis":hypothesis,"population":population,"comparator":comparator,"indicators":selected}
                st.success('Experimento criado na sessão demonstrativa. Na versão persistente, ele receberá versão, responsáveis, população, baseline, evidências e trilha de auditoria.')

        st.subheader('Resultado comparativo — experimento selecionado')
        results=pd.DataFrame(EXPERIMENT_RESULTS)
        results['Status']=results.apply(lambda r:'🟢 Meta superada' if r['Resultado']>=r['Meta'] else '🟡 Abaixo da meta',axis=1)
        display=results.copy()
        for col in ['Baseline','Meta','Resultado']:
            display[col]=display.apply(lambda r: f"{r[col]:.0f}{r['Unidade']}",axis=1)
        st.dataframe(display.drop(columns=['Unidade']),use_container_width=True,hide_index=True)

        st.subheader('Porta de decisão')
        decision=st.radio('Decisão baseada nas evidências',['Continuar','Reformular','Novo ciclo experimental','Suspender','Encerrar','Recomendar escala'],horizontal=True)
        rationale=st.text_area('Justificativa da decisão',value='Resultados de conclusão e inserção superaram as metas; permanência em 180 dias ficou abaixo do patamar esperado. Recomenda-se ajustar o acompanhamento pós-inserção antes da escala.')
        if st.button('Registrar decisão',key='record_gate'):
            st.session_state['decision_gate']={"decision":decision,"rationale":rationale}
            st.success('Decisão registrada na sessão demonstrativa com vínculo lógico ao experimento e aos indicadores exibidos.')

    with tabs[2]:
        st.subheader('Funil comparativo por segmento')
        eq=pd.DataFrame(EQUITY_FUNNEL)
        eq['Gap (p.p.)']=eq['Grupo comparador']-eq['Mulheres 35–49']
        st.dataframe(eq,use_container_width=True,hide_index=True)
        st.bar_chart(eq.set_index('Etapa')[['Mulheres 35–49','Grupo comparador']],use_container_width=True)
        max_gap=eq.sort_values('Gap (p.p.)',ascending=False).iloc[0]
        st.warning(f"⚠️ **Gap relevante identificado:** na etapa **{max_gap['Etapa']}**, o segmento Mulheres 35–49 está {int(max_gap['Gap (p.p.)'])} p.p. abaixo do grupo comparador.")
        st.subheader('Barreiras e respostas adotadas')
        st.dataframe(pd.DataFrame(BARRIERS),use_container_width=True,hide_index=True)
        st.markdown('**Ciclo de equidade:** identificar segmento → localizar perda no funil → registrar barreira → testar resposta diferenciada → medir novamente o gap.')

    with tabs[3]:
        cpp=econ['pilot_cost']/econ['participants']; cpc=econ['pilot_cost']/econ['completers']; cpi=econ['pilot_cost']/econ['inserted']; cpr=econ['pilot_cost']/econ['retained_90']
        c1,c2,c3,c4=st.columns(4)
        c1.metric('Custo por participante',_money(cpp))
        c2.metric('Custo por concluinte',_money(cpc))
        c3.metric('Custo por inserido',_money(cpi))
        c4.metric('Custo por retido 90d',_money(cpr))

        current_insertion=econ['inserted']/econ['participants']*100
        comparator_cpi=econ['comparator_cost_per_participant']/(econ['comparator_insertion']/100)
        comparison=pd.DataFrame([
            {"Modelo":"Modelo comparador","Custo/participante":econ['comparator_cost_per_participant'],"Conclusão (%)":econ['comparator_completion'],"Inserção (%)":econ['comparator_insertion'],"Custo/inserido":comparator_cpi},
            {"Modelo":"NEXO — piloto","Custo/participante":cpp,"Conclusão (%)":econ['completers']/econ['participants']*100,"Inserção (%)":current_insertion,"Custo/inserido":cpi},
        ])
        pretty=comparison.copy(); pretty['Custo/participante']=pretty['Custo/participante'].map(_money); pretty['Custo/inserido']=pretty['Custo/inserido'].map(_money)
        st.dataframe(pretty,use_container_width=True,hide_index=True)
        delta=(cpi/comparator_cpi-1)*100
        if delta<0:
            st.success(f'**Leitura econômica:** o custo por inserção do piloto é {abs(delta):.1f}% menor que o modelo comparador demonstrativo, apesar do investimento adicional por participante.')
        else:
            st.warning(f'**Leitura econômica:** o custo por inserção do piloto é {delta:.1f}% maior que o comparador; a proposta deverá justificar o ganho adicional de resultado e/ou reformular o desenho.')

    with tabs[4]:
        st.subheader('Feedback empresarial → reformulação')
        st.dataframe(pd.DataFrame(EMPLOYER_FEEDBACK),use_container_width=True,hide_index=True)
        st.markdown('**Regra de governança:** feedback empresarial só produz mudança quando estiver documentado, vinculado a uma competência/intervenção e posteriormente reavaliado. O NEXO preserva a trilha **evidência → decisão → mudança → novo resultado**.')
