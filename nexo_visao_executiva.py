"""NEXO Qualifica+ | Visão Geral Executiva v2.0.

Painel de entrada que apresenta as cinco páginas e suas relações com o
objetivo de aferir aderência e investigar efetividade da qualificação.

- NÃO realiza requisições web, nem consultas ao CAGED oficial.
- Quando os módulos existentes estiverem disponíveis, reutiliza as bases
  sintéticas e/ou informações editadas NA SESSÃO pelo operador.
- A comparação de competências é exploratória, por nome normalizado;
  não representa validação de equivalência, impacto ou causalidade.
- Não altera outras páginas, não grava no banco e não recebe dados pessoais.
"""
from __future__ import annotations

from collections import Counter
from html import escape
import re
import unicodedata
from typing import Iterable

import pandas as pd
import streamlit as st


MODULES = [
    {
        "n": "01", "name": "Radar de Vagas", "nav": ["Radar de Vagas (demo)", "Radar de Vagas"],
        "tag": "Sinais de mercado", "subtitle": "Quais ocupações e competências o mercado procura?",
        "features": ["Histórico de anúncios e postos por setor", "Ocupações, competências e requisitos recorrentes"],
        "output": "Demanda produtiva observada", "icon": "▤",
    },
    {
        "n": "02", "name": "Perfil Empresa", "nav": ["Perfil Empresa", "Demanda & Competências"],
        "tag": "Validação da demanda", "subtitle": "O que as empresas confirmam como necessário?",
        "features": ["Registro das necessidades empresariais", "Classificação CBO/QBQ e validação de competências"],
        "output": "Competências estruturadas e revisáveis", "icon": "◇",
    },
    {
        "n": "03", "name": "Perfil Cidadão", "nav": ["Perfil Cidadão", "Diagnóstico & Trajetória"],
        "tag": "Capacidades das pessoas", "subtitle": "Quais competências e barreiras encontramos?",
        "features": ["Diagnóstico de experiência, skills e barreiras", "Lacunas e trajetórias de desenvolvimento"],
        "output": "Necessidades formativas dos participantes", "icon": "◎",
    },
    {
        "n": "04", "name": "Gestão das Ofertas de Qualificação", "nav": ["Gestão das Ofertas de Qualificação", "Planejamento & Engenharia"],
        "tag": "Oferta e execução", "subtitle": "O que foi contratado, executado e ainda está disponível?",
        "features": ["Contratos, cursos e saldo de vagas formativas", "Comparação entre currículos e demanda de mercado"],
        "output": "Capacidade de resposta da política", "icon": "▥",
    },
    {
        "n": "05", "name": "Empregabilidade e Renda", "nav": ["Empregabilidade e Renda", "Resultados & Impactos"],
        "tag": "Evidência de resultados", "subtitle": "Como evoluem empregos e rendimentos relacionados?",
        "features": ["Saldo ocupacional e remuneração média de admissão", "Registros complementares da rede e limitações"],
        "output": "Sinais de resultado e lacunas de evidência", "icon": "↗",
    },
]


def _esc(x: object) -> str:
    return escape(str(x), quote=True)


def _num(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def _norm(x: object) -> str:
    txt = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", txt)).strip()


def _css() -> None:
    st.markdown("""
    <style>
    .nxe-hero {background: radial-gradient(circle at 86% 8%,rgba(93,169,235,.26),transparent 36%),linear-gradient(110deg,#081A3D,#21496E);border-radius:20px;padding:28px 32px 25px;color:#fff;margin-bottom:12px;}
    .nxe-hero .eyebrow {text-transform:uppercase;letter-spacing:.14em;color:#BBDCF3;font-size:10px;font-weight:800;}
    .nxe-hero h1 {color:#fff!important;font-size:29px!important;font-weight:780!important;letter-spacing:-.03em;margin:11px 0 10px!important;line-height:1.19!important;}
    .nxe-hero p {color:#DFE9F8!important;font-size:14px!important;line-height:1.55!important;margin:0!important;max-width:850px}
    .nxe-note{display:flex;flex-wrap:wrap;align-items:center;gap:8px;color:#64748B;font-size:11px;margin:3px 0 18px}
    .nxe-demo{display:inline-block;background:#FFF1D3;color:#835619;font-weight:760;border-radius:100px;padding:5px 10px;font-size:10px}
    .nxe-kpi{border:1px solid #E1E8F2;background:#fff;border-radius:16px;padding:17px 17px 14px;min-height:117px;box-shadow:0 4px 14px rgba(8,25,60,.035)}
    .nxe-kpi label{font-weight:710;color:#63758D;font-size:12px;display:block;line-height:1.3}
    .nxe-kpi strong{display:block;margin:6px 0 3px;color:#102448;font-size:29px;font-weight:800;letter-spacing:-.04em;line-height:1.15}
    .nxe-kpi small{color:#7890A5;display:block;font-size:11px;line-height:1.45}
    .nxe-heading{margin:26px 0 10px}.nxe-heading .eyebrow{text-transform:uppercase;font-weight:800;font-size:10px;letter-spacing:.14em;color:#397DB2}
    .nxe-heading h3{font-size:21px!important;margin:6px 0 3px!important;color:#102448!important}
    .nxe-heading p{font-size:12px;color:#73849A;margin:0}
    .nxe-rail{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin:12px 0}
    .nxe-step{border:1px solid #E0E9F2;border-radius:13px;padding:14px 12px;background:#F7FAFE;min-height:144px;position:relative}
    .nxe-step .number{display:block;font-size:10px;letter-spacing:.13em;color:#6088B7;font-weight:830}
    .nxe-step b{display:block;color:#17365D;font-size:12px;line-height:1.45;margin:9px 0 6px}
    .nxe-step small{display:block;color:#6A7B90;font-size:11px;line-height:1.45}
    .nxe-strap{padding:15px 18px;background:#EDF4FB;border:1px solid #D7E7F6;border-radius:13px;font-size:12px;line-height:1.55;color:#244868;margin-top:12px}
    .nxe-panel{background:#fff;border:1px solid #E0E9F2;border-radius:15px;padding:17px 19px;min-height:247px}
    .nxe-panel h4{font-size:14px;color:#172F50;margin:0 0 6px}
    .nxe-panel p{font-size:11px;color:#78899A;margin:0 0 16px}
    .nxe-bar{margin:0 0 13px}
    .nxe-bar-head{display:flex;justify-content:space-between;gap:12px;font-size:11px;color:#334A65;margin-bottom:5px}
    .nxe-bar-head span:first-child{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:82%}
    .nxe-bar-track{background:#EDF2F9;height:7px;border-radius:99px;overflow:hidden}
    .nxe-bar-fill{height:7px;background:linear-gradient(90deg,#3476BB,#75ACE4);border-radius:99px}
    .nxe-mcard{border:1px solid #DFE8F1;border-radius:14px;padding:16px 18px;background:#fff;min-height:200px;}
    .nxe-mcard .tag{color:#2D6D9F;text-transform:uppercase;letter-spacing:.10em;font-weight:800;font-size:10px}
    .nxe-mcard h4{color:#112F54;font-size:16px;margin:7px 0 5px}
    .nxe-mcard .desc{font-size:12px;color:#506B84;min-height:34px}
    .nxe-mcard ul{padding-left:17px;margin:8px 0 0;font-size:12px;line-height:1.7;color:#3D5570}
    .nxe-output{display:block;font-size:11px;color:#337DB9;font-weight:670;border-top:1px solid #EAF0F6;padding-top:9px;margin-top:13px}
    .nxe-pill{display:inline-block;border:1px solid #DCE8F4;background:#F3F8FD;color:#275B8E;border-radius:50px;padding:5px 10px;font-size:11px;margin:3px 4px 2px 0;line-height:1.3}
    .nxe-pill.miss{background:#FFF6E8;border-color:#F7E3C0;color:#80531A}
    .nxe-signal{border-left:3px solid #4B8EBB;background:#F5F9FD;border-radius:6px;padding:11px 14px;margin:9px 0;font-size:12px;line-height:1.55;color:#3D5770}
    .nxe-strong{color:#1A4775;font-weight:800}
    .nxe-foot{color:#8593A7;font-size:11px;line-height:1.6;margin:17px 0}
    @media(max-width:1100px){.nxe-rail{grid-template-columns:repeat(3,minmax(0,1fr))}}
    @media(max-width:650px){.nxe-rail{grid-template-columns:1fr 1fr}.nxe-hero{padding:21px}.nxe-hero h1{font-size:22px!important}.nxe-kpi strong{font-size:22px}}
    </style>
    """, unsafe_allow_html=True)


def _heading(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="nxe-heading"><div class="eyebrow">{_esc(eyebrow)}</div><h3>{_esc(title)}</h3><p>{_esc(subtitle)}</p></div>', unsafe_allow_html=True)


def _kpi(title: str, val: str, detail: str) -> None:
    st.markdown(f'<div class="nxe-kpi"><label>{_esc(title)}</label><strong>{_esc(val)}</strong><small>{_esc(detail)}</small></div>', unsafe_allow_html=True)


def _bars(items: Iterable[tuple[object, float]], max_items: int = 5, empty: str = "Dados indisponíveis") -> None:
    vals = [(str(name), int(val)) for name, val in list(items)[:max_items]]
    if not vals:
        st.caption(empty)
        return
    peak = max(1, max(v for _, v in vals))
    parts = []
    for name, n in vals:
        pct = max(2, int(n * 100 / peak)) if n else 0
        parts.append(f'<div class="nxe-bar"><div class="nxe-bar-head"><span title="{_esc(name)}">{_esc(name)}</span><b>{_num(n)}</b></div><div class="nxe-bar-track"><div class="nxe-bar-fill" style="width:{pct}%"></div></div></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def _ofertas():
    """Acesso não destrutivo ao cadastro em sessão ou à fixture do módulo existente."""
    atual = st.session_state.get("nexo_plan_courses")
    if atual is not None:
        return list(atual), "cadastro desta sessão (origem dos registros não validada)"
    try:
        from nexo_planejamento_contratos import CURSOS_DEMO
        return [dict(id=i, contrato_id=c, curso=t, setor=s, contratadas=q, ocupadas=o, concluidas=f, competencias=list(k), origem="Demonstração") for i,c,t,s,q,o,f,k in CURSOS_DEMO], "base sintética demonstrativa"
    except (ImportError, AttributeError):
        return [], "módulo de ofertas indisponível"


def _radar():
    try:
        from nexo_radar_vagas import _historico_sintetico, _periodo
        df = _periodo(_historico_sintetico(), 365)
        return df, "série sintética do Radar de Vagas"
    except (ImportError, AttributeError):
        return pd.DataFrame(), "módulo do Radar indisponível"


def _ocupacoes(cursos: list[dict]):
    try:
        from nexo_resultados_empregabilidade import MAPEAMENTO_DEMO, demonstracao_caged
    except (ImportError, AttributeError):
        return None, "módulo de Empregabilidade e Renda indisponível"
    mapping = st.session_state.get("nexo_er_mapeamento", MAPEAMENTO_DEMO)
    cbos = {str(cbo) for c in cursos for cbo in mapping.get(c.get("id"), [])}
    df = st.session_state.get("nexo_er_base_caged")
    origem = "CSV inserido nesta sessão (procedência não validada)" if isinstance(df, pd.DataFrame) else "série sintética ilustrativa do CAGED"
    if not isinstance(df, pd.DataFrame):
        df = demonstracao_caged()
    if df.empty or not cbos:
        return None, origem
    cur = df[df["cbo"].astype(str).isin(cbos)].copy()
    if cur.empty:
        return None, origem
    end = cur["mes"].max()
    cur = cur[(cur["mes"] >= end - pd.DateOffset(months=5)) & (cur["mes"] <= end)]
    sum_by_occ = cur.groupby("cbo")["admissoes"].sum() - cur.groupby("cbo")["desligamentos"].sum()
    return {"saldo": int((cur["admissoes"] - cur["desligamentos"]).sum()),
            "cbos": int(cur["cbo"].nunique()),
            "positivas": int((sum_by_occ > 0).sum()),
            "periodo": str(end.strftime("%m/%Y"))}, origem


def _skill_map(df: pd.DataFrame, cursos: list[dict]) -> tuple[list[tuple[str, int]], list[str], list[str]]:
    if df.empty or "Competências sugeridas" not in df.columns:
        return [], [], []
    freq = Counter()
    for vals in df["Competências sugeridas"].tolist():
        if isinstance(vals, list):
            freq.update(set(str(v) for v in vals))
    principais = freq.most_common(8)
    em_oferta = {_norm(x) for o in cursos for x in o.get("competencias", [])}
    presentes = [s for s, _ in principais if _norm(s) in em_oferta]
    ausentes = [s for s, _ in principais if _norm(s) not in em_oferta]
    return principais, presentes, ausentes


def _nav_target(options: list[str], paginas: list[str]) -> str | None:
    return next((x for x in options if x in paginas), None)


def _go_to(label: str) -> None:
    # Executado em callback antes de Streamlit recriar o st.sidebar.radio.
    st.session_state["nexo_nav"] = label


def _module_card(module: dict, paginas: list[str]) -> None:
    lines = "".join("<li>" + _esc(x) + "</li>" for x in module["features"])
    st.markdown(f'''<div class="nxe-mcard">
        <div class="tag">{module["n"]} · {_esc(module["tag"])}</div>
        <h4>{_esc(module["name"])}</h4>
        <div class="desc">{_esc(module["subtitle"])}</div>
        <ul>{lines}</ul>
        <span class="nxe-output">Entrega → {_esc(module["output"])}</span>
    </div>''', unsafe_allow_html=True)
    target = _nav_target(module["nav"], paginas)
    if target is not None:
        st.button("Abrir módulo →", key="nxe_open_" + module["n"], use_container_width=True,
                  on_click=_go_to, args=(target,))
    else:
        st.caption("Disponível na navegação lateral quando configurado")


def render_visao_executiva(paginas: list[str] | None = None) -> None:
    """Painel público. Para botões ativos, use sidebar radio(key='nexo_nav')."""
    _css()
    paginas = list(paginas or [])
    cursos, origem_ofertas = _ofertas()
    radar, origem_radar = _radar()
    caged, origem_caged = _ocupacoes(cursos)

    n_cursos = len(cursos)
    contratadas = sum(int(x.get("contratadas", 0) or 0) for x in cursos)
    ocupadas = sum(int(x.get("ocupadas", 0) or 0) for x in cursos)
    saldo_formacao = sum(max(0, int(x.get("contratadas", 0) or 0) - int(x.get("ocupadas", 0) or 0)) for x in cursos)
    postos = int(radar["Postos"].sum()) if not radar.empty and "Postos" in radar else None
    principal, presentes, ausentes = _skill_map(radar, cursos)

    st.markdown('''<div class="nxe-hero">
       <div class="eyebrow">NEXO QUALIFICA+ &nbsp; / &nbsp; PAINEL EXECUTIVO</div>
       <h1>Da demanda do mercado à efetividade da qualificação.</h1>
       <p>Uma visão integrada do que as empresas procuram, do que o poder público oferece, do que as pessoas precisam desenvolver e dos resultados observáveis no mercado de trabalho.</p>
    </div>''', unsafe_allow_html=True)
    st.markdown('<div class="nxe-note"><span class="nxe-demo">AMBIENTE DEMONSTRATIVO</span><span>Dados sintéticos ou lançamentos temporários de sessão · sem coleta oficial automatizada · recomendações exigem validação humana</span></div>', unsafe_allow_html=True)

    _heading("01 / Em um olhar", "Panorama da qualificação e do mercado", "Indicadores de dimensões distintas — não são uma medida causal de impacto.")
    a, b, c, d = st.columns(4, gap="small")
    with a: _kpi("Postos anunciados", _num(postos) if postos is not None else "—", "Radar · janela demonstrativa de 12 meses")
    with b: _kpi("Vagas de qualificação", _num(contratadas) if cursos else "—", f"Em {n_cursos} cursos monitorados")
    with c: _kpi("Saldo de formação", _num(saldo_formacao) if cursos else "—", f"{_num(ocupadas)} matrículas confirmadas / vagas ocupadas")
    with d: _kpi("Saldo formal relacionado", f"{caged['saldo']:+,}".replace(",", ".") if caged else "—", "Ocupações CBO vinculadas · últimos 6 meses")

    st.markdown('''<div class="nxe-strap"><strong>As duas perguntas do NEXO:</strong> <b>Aderência</b> — os cursos e competências ofertados correspondem ao que o mercado demanda? &nbsp;·&nbsp; <b>Efetividade</b> — a qualificação desenvolve capacidades e se associa a melhores trajetórias de trabalho e renda, considerando evidências confiáveis? <span style="color:#68829B">O saldo CAGED sozinho não responde à segunda pergunta.</span></div>''', unsafe_allow_html=True)

    _heading("02 / Como o NEXO funciona", "Um único circuito de inteligência pública", "Cada módulo gera informações que alimentam os seguintes; a decisão final permanece sob responsabilidade do gestor.")
    steps = [
        ("01", "Demanda produtiva", "Radar + empresas identificam vagas, ocupações e competências."),
        ("02", "Diagnóstico", "Perfis dos cidadãos mostram competências e barreiras."),
        ("03", "Oferta e execução", "Contratos revelam cursos, capacidade e saldo de formação."),
        ("04", "Emprego e renda", "CAGED e rede registram sinais e evidências disponíveis."),
        ("05", "Decisão pública", "Manter, ajustar, ampliar ou testar novas ofertas."),
    ]
    st.markdown('<div class="nxe-rail">' + "".join(f'<div class="nxe-step"><span class="number">{_esc(n)} / ETAPA</span><b>{_esc(name)}</b><small>{_esc(desc)}</small></div>' for n, name, desc in steps) + '</div>', unsafe_allow_html=True)

    _heading("03 / Correspondência entre mercado e oferta", "Quais sinais já podem ser explorados?", "Um exemplo de como a Visão Geral conecta demanda e capacidade contratada sem equiparar anúncios a matrículas.")
    left, right = st.columns(2, gap="medium")
    with left:
        with st.container(border=True):
            st.markdown('**Setores com mais postos anunciados**')
            st.caption('Participação relativa no Radar · últimos 12 meses simulados')
            if not radar.empty:
                _bars(radar.groupby("Setor")["Postos"].sum().sort_values(ascending=False).items(), max_items=5)
            else:
                st.caption("Radar indisponível")
    with right:
        with st.container(border=True):
            st.markdown('**Vagas formativas contratadas por setor**')
            st.caption('Capacidade dos cursos na Gestão das Ofertas · sem correspondência 1:1 com postos')
            if cursos:
                setor_counter = Counter()
                for c in cursos:
                    setor_counter[str(c.get("setor", "Não classificado"))] += int(c.get("contratadas", 0) or 0)
                _bars(setor_counter.most_common(5))
            else:
                st.caption("Cursos indisponíveis")

    st.markdown('''<div class="nxe-signal"><span class="nxe-strong">Como usar essa comparação:</span> a concentração de anúncios orienta onde investigar oportunidades; a capacidade contratada mostra a resposta atual da política. Para afirmar aderência curricular, é preciso validar ocupações, competências e conteúdo dos cursos — não apenas comparar volumes.</div>''', unsafe_allow_html=True)

    if principal:
        left, right = st.columns([1.25, 1])
        with left:
            st.markdown('**Competências mais recorrentes nos anúncios**')
            _bars(principal, 6)
            st.caption("Frequência em anúncios, não em pessoas. Extração lexical demonstrativa.")
        with right:
            st.markdown('**Correspondências textuais com cursos**')
            st.markdown("".join(f'<span class="nxe-pill">✓ {_esc(x)}</span>' for x in presentes[:6]) or '<span class="nxe-pill">Nenhuma correspondência exata</span>', unsafe_allow_html=True)
            st.markdown('**Competências a conferir na matriz curricular**')
            st.markdown("".join(f'<span class="nxe-pill miss">· {_esc(x)}</span>' for x in ausentes[:5]) or '<span class="nxe-pill">Sem itens adicionais na amostra</span>', unsafe_allow_html=True)
            st.caption("Comparação por nome normalizado. Não equivale a matching semântico ou validação técnico-pedagógica.")

    _heading("04 / Funcionalidades", "Explore as cinco páginas do NEXO", "Cada página tem uma finalidade, um conjunto de informações e uma contribuição específica para avaliar as ofertas.")
    for i in (0, 2, 4):
        pair = MODULES[i:i+2]
        cols = st.columns(2, gap="medium")
        for col, module in zip(cols, pair):
            with col:
                _module_card(module, paginas)

    _heading("05 / O que a gestão consegue decidir", "Da informação à ação", "O sistema apoia hipóteses de decisão; resultados e custos precisam de evidências antes de autorizar mudanças relevantes.")
    st.markdown('''<div class="nxe-strap"><b>Alinhamento ao mercado:</b> cruzar competências e requisitos do Radar/Perfil Empresa com currículos e cursos contratados. &nbsp; <b>Capacidade de atendimento:</b> conferir vagas formativas disponíveis e ocupadas. &nbsp; <b>Efetividade:</b> observar conclusão e competências adquiridas, somadas a registros de encaminhamento/contratação e tendências ocupacionais de emprego e remuneração. &nbsp; <b>Recalibração:</b> fundamentar decisões de manutenção, ampliação, revisão curricular e novos testes.</div>''', unsafe_allow_html=True)

    with st.expander("Fontes, qualidade e limites de interpretação"):
        st.markdown(f"**Radar:** {origem_radar}. **Ofertas:** {origem_ofertas}. **Emprego formal:** {origem_caged}.")
        st.markdown("**Não inferir causalidade:** a variação do saldo de emprego municipal por CBO não comprova contratação de egressos ou ganho individual decorrente de um curso. Requer fontes complementares e método de avaliação.")
        st.markdown("**Unidades distintas:** anúncios, postos anunciados, vagas de curso, matrículas, admissões e saldos de empregos não são intercambiáveis.")
        st.markdown("**Indicadores integrados:** os valores dependem da disponibilidade dos módulos existentes e podem variar com os lançamentos realizados nesta sessão. O painel não salva alterações e não utiliza dados oficiais automaticamente.")

    st.markdown('<div class="nxe-foot">NEXO Qualifica+ · MVP demonstrativo · leituras de aderência são exploratórias; decisões automatizadas de elegibilidade ou exclusão não são realizadas.</div>', unsafe_allow_html=True)
