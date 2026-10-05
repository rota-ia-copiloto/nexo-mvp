import hashlib
import json
import random
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

# ============================================================
# NEXO QUALIFICA+ — CPSI MVP v1
# Hipótese central: fechar o loop
# demanda -> competências -> trajetória -> intervenção -> outcome -> decisão
# ============================================================

st.set_page_config(
    page_title="NEXO Qualifica+ — CPSI MVP",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# -----------------------------
# STYLE
# -----------------------------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.2rem; padding-bottom: 3rem;}
      [data-testid="stSidebar"] {background: #071B3A;}
      [data-testid="stSidebar"] * {color: white !important;}
      .nexo-kicker {font-size:.75rem; letter-spacing:.14em; text-transform:uppercase; color:#6B7280; font-weight:700;}
      .nexo-title {font-size:2rem; line-height:1.05; font-weight:800; color:#071B3A; margin:.2rem 0 .35rem 0;}
      .nexo-sub {font-size:1rem; color:#5F6B7A; margin-bottom:1rem;}
      .card {background:white; border:1px solid #E5EAF0; border-radius:16px; padding:18px; box-shadow:0 2px 12px rgba(7,27,58,.04); height:100%;}
      .card h4 {color:#071B3A; margin-top:0;}
      .chip {display:inline-block; border-radius:999px; padding:4px 9px; margin:2px; background:#EDF4FF; color:#0B4F9C; font-size:.78rem; font-weight:700;}
      .chip-warn {background:#FFF4D8; color:#7A5200;}
      .chip-good {background:#EAF8EF; color:#176A37;}
      .flow {background:#F7FAFE; border:1px solid #DDE7F2; border-radius:14px; padding:14px; text-align:center; min-height:106px;}
      .flow b {color:#071B3A;}
      .decision {background:#071B3A; color:white; border-radius:16px; padding:18px 20px;}
      .decision b {color:#FFC400;}
      .small-muted {font-size:.82rem; color:#6B7280;}
      .evidence {border-left:4px solid #FFC400; background:#FAFBFC; border-radius:8px; padding:10px 12px; margin:7px 0;}
      .explain {background:#F7FAFE; border-radius:12px; padding:12px 14px; border:1px solid #DDE7F2;}
      .hero {background:linear-gradient(100deg,#071B3A,#123E72); color:white; padding:20px; border-radius:18px; margin-bottom:14px;}
      .hero h2,.hero h3 {color:white; margin:0;}
      .hero p {color:#D9E6F5; margin:.35rem 0 0 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# DOMAIN DATA
# -----------------------------
SKILLS = {
    "SK001": {"name": "Controle de estoque", "type": "Técnica"},
    "SK002": {"name": "Leitura de documentos operacionais", "type": "Técnica"},
    "SK003": {"name": "Sistemas de gestão / ERP", "type": "Digital"},
    "SK004": {"name": "Logística operacional", "type": "Técnica"},
    "SK005": {"name": "Organização operacional", "type": "Transversal"},
    "SK006": {"name": "Trabalho em equipe", "type": "Transversal"},
    "SK007": {"name": "Segurança operacional", "type": "Técnica"},
    "SK008": {"name": "Monitoramento de processos", "type": "Técnica"},
    "SK009": {"name": "Comunicação", "type": "Transversal"},
    "SK010": {"name": "Resolução de problemas", "type": "Transversal"},
    "SK011": {"name": "Excel básico", "type": "Digital"},
    "SK012": {"name": "Atendimento", "type": "Transversal"},
}

KEYWORD_TO_SKILL = {
    "estoque": "SK001",
    "inventário": "SK001",
    "documento": "SK002",
    "nota fiscal": "SK002",
    "erp": "SK003",
    "sistema": "SK003",
    "logística": "SK004",
    "separação": "SK004",
    "expedição": "SK004",
    "organização": "SK005",
    "equipe": "SK006",
    "segurança": "SK007",
    "processo": "SK008",
    "monitoramento": "SK008",
    "comunicação": "SK009",
    "problema": "SK010",
    "excel": "SK011",
    "atendimento": "SK012",
}

DEFAULT_DEMAND_TEXT = (
    "Precisamos contratar 20 auxiliares de operações logísticas. "
    "A função exige controle de estoque, leitura de documentos operacionais, "
    "uso básico de sistema ERP, organização e trabalho em equipe."
)

PARTICIPANTS = pd.DataFrame([
    {
        "participant_id": "P001", "name": "Ana Souza", "age": 24,
        "education": "Ensino Médio", "employment_status": "Desempregada",
        "digital_access": "Médio", "availability": "Integral",
        "barriers": ["Baixa familiaridade com sistemas digitais"],
        "skills": {"SK002": 2, "SK005": 3, "SK006": 3, "SK009": 2, "SK011": 2},
    },
    {
        "participant_id": "P002", "name": "Carlos Mendes", "age": 29,
        "education": "Ensino Médio", "employment_status": "Informal",
        "digital_access": "Alto", "availability": "Noturno",
        "barriers": [],
        "skills": {"SK001": 2, "SK002": 2, "SK003": 2, "SK004": 2, "SK005": 2, "SK006": 2},
    },
    {
        "participant_id": "P003", "name": "Juliana Rocha", "age": 31,
        "education": "Ensino Médio", "employment_status": "Desempregada",
        "digital_access": "Baixo", "availability": "Diurno",
        "barriers": ["Acesso digital instável", "Responsabilidade de cuidado"],
        "skills": {"SK002": 1, "SK005": 2, "SK006": 2, "SK012": 3},
    },
])

LEARNING_BLUEPRINTS = {
    "SK001": {
        "objective": "Executar operações básicas de entrada, armazenamento, conferência e saída de materiais.",
        "strategy": "20% conceito • 50% prática simulada • 30% situações-problema",
        "assessment": "Simulação operacional + checklist de desempenho",
        "hours": 12,
    },
    "SK003": {
        "objective": "Registrar e consultar movimentações básicas em um sistema de gestão de estoque.",
        "strategy": "15% demonstração • 60% prática guiada • 25% exercício autônomo",
        "assessment": "Tarefa prática em ambiente simulado",
        "hours": 10,
    },
    "SK004": {
        "objective": "Aplicar princípios básicos de fluxo logístico em recebimento, armazenagem e expedição.",
        "strategy": "25% conceito • 50% oficina prática • 25% estudo de caso",
        "assessment": "Resolução de caso + execução de fluxo simplificado",
        "hours": 16,
    },
    "SK007": {
        "objective": "Reconhecer riscos básicos e aplicar procedimentos de segurança em ambiente operacional.",
        "strategy": "30% conceito • 40% demonstração • 30% simulação",
        "assessment": "Checklist situacional",
        "hours": 8,
    },
}

EXPERIMENT_DATA = pd.DataFrame([
    ["Coorte A", "Formação padrão", 50, 42, 34, 29, 23, 14, 11],
    ["Coorte B", "Formação + acompanhamento adaptativo", 50, 47, 43, 38, 31, 21, 18],
], columns=["cohort", "intervention", "ingress", "participation", "completion", "skill_demo", "referral", "hiring", "retention"])

# -----------------------------
# STATE / PERSISTENCE (MVP)
# -----------------------------
def init_state():
    defaults = {
        "validated_skills": {},
        "recommendations": {},
        "trajectory_events": [],
        "evidence_log": [],
        "selected_participant": "P001",
        "selected_demand_text": DEFAULT_DEMAND_TEXT,
        "demo_stage": 0,
        "manager_decision": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def event_hash(payload: Dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def add_evidence(event_type: str, actor: str, description: str, source: str = "NEXO MVP"):
    payload = {
        "timestamp": now_iso(),
        "event_type": event_type,
        "actor": actor,
        "description": description,
        "source": source,
    }
    payload["hash"] = event_hash(payload)
    st.session_state.evidence_log.append(payload)


def add_trajectory_event(participant_id: str, event_type: str, label: str, actor: str):
    row = {
        "participant_id": participant_id,
        "timestamp": now_iso(),
        "event_type": event_type,
        "label": label,
        "actor": actor,
    }
    st.session_state.trajectory_events.append(row)
    add_evidence(event_type, actor, f"{participant_id}: {label}")

# -----------------------------
# ENGINES
# -----------------------------
def extract_skills(text: str) -> pd.DataFrame:
    """Deterministic semantic proxy for the MVP; replaceable by embeddings/LLM later."""
    text_l = text.lower()
    rows = []
    seen = set()
    for keyword, skill_id in KEYWORD_TO_SKILL.items():
        if keyword in text_l and skill_id not in seen:
            seen.add(skill_id)
            confidence = 0.94 if keyword == SKILLS[skill_id]["name"].lower() else 0.82
            rows.append({
                "skill_id": skill_id,
                "competência_sugerida": SKILLS[skill_id]["name"],
                "tipo": SKILLS[skill_id]["type"],
                "confiança": confidence,
                "gatilho": keyword,
                "status": st.session_state.validated_skills.get(skill_id, "Pendente"),
            })
    if not rows:
        rows.append({
            "skill_id": "SK004",
            "competência_sugerida": "Logística operacional",
            "tipo": "Técnica",
            "confiança": 0.58,
            "gatilho": "inferência genérica",
            "status": st.session_state.validated_skills.get("SK004", "Pendente"),
        })
    return pd.DataFrame(rows)


def required_skills_from_demand(df: pd.DataFrame) -> List[str]:
    accepted = []
    for r in df.to_dict("records"):
        status = st.session_state.validated_skills.get(r["skill_id"], r["status"])
        if status in ["Validada", "Remapeada"]:
            accepted.append(r["skill_id"])
    return accepted if accepted else df["skill_id"].tolist()


def participant_record(pid: str) -> Dict:
    return PARTICIPANTS[PARTICIPANTS.participant_id == pid].iloc[0].to_dict()


def gap_analysis(pid: str, demand_skill_ids: List[str]) -> Tuple[pd.DataFrame, float]:
    p = participant_record(pid)
    rows = []
    readiness_points = []
    for sid in demand_skill_ids:
        current = int(p["skills"].get(sid, 0))
        required = 2
        gap = max(required - current, 0)
        readiness_points.append(min(current / required, 1.0))
        rows.append({
            "skill_id": sid,
            "competência": SKILLS[sid]["name"],
            "nível_atual": current,
            "nível_requerido": required,
            "gap": gap,
            "situação": "Atendida" if gap == 0 else "Gap",
        })
    base_readiness = sum(readiness_points) / max(len(readiness_points), 1)
    barrier_penalty = min(len(p["barriers"]) * 0.08, 0.24)
    readiness = max(0.0, base_readiness - barrier_penalty)
    return pd.DataFrame(rows), readiness


def recommend_path(pid: str, demand_skill_ids: List[str]) -> Dict:
    p = participant_record(pid)
    gaps, readiness = gap_analysis(pid, demand_skill_ids)
    missing = gaps[gaps["gap"] > 0]["skill_id"].tolist()
    barriers = p["barriers"]

    if readiness >= 0.78 and not barriers:
        pathway = "Trilha técnica rápida + encaminhamento produtivo"
        intensity = "Baixa"
        rationale = "Alta prontidão e gaps predominantemente técnicos, sem barreiras críticas registradas."
    elif readiness >= 0.48:
        pathway = "Preparação funcional + módulo técnico focalizado + acompanhamento"
        intensity = "Média"
        rationale = "Prontidão intermediária: há competências de base, mas gaps e/ou barreiras recomendam preparação complementar."
    else:
        pathway = "Percurso protegido: preparação de base + inclusão digital + técnica progressiva"
        intensity = "Alta"
        rationale = "Baixa prontidão relativa ao perfil da demanda e presença de barreiras que podem comprometer ingresso ou permanência."

    recommended_modules = []
    for sid in missing:
        if sid in LEARNING_BLUEPRINTS:
            recommended_modules.append(sid)
    if not recommended_modules and missing:
        recommended_modules = missing[:2]

    return {
        "participant_id": pid,
        "pathway": pathway,
        "intensity": intensity,
        "readiness": readiness,
        "missing_skills": missing,
        "recommended_modules": recommended_modules,
        "barriers": barriers,
        "rationale": rationale,
        "human_review_required": True,
    }


def experiment_summary() -> Dict:
    a = EXPERIMENT_DATA.iloc[0]
    b = EXPERIMENT_DATA.iloc[1]
    def rate(row, col):
        return row[col] / row["ingress"] if row["ingress"] else 0
    metrics = {
        "completion_A": rate(a, "completion"),
        "completion_B": rate(b, "completion"),
        "hiring_A": rate(a, "hiring"),
        "hiring_B": rate(b, "hiring"),
        "retention_A": rate(a, "retention"),
        "retention_B": rate(b, "retention"),
    }
    improvement = metrics["completion_B"] - metrics["completion_A"]
    recommendation = (
        "Continuar o teste com nova coorte antes de escala. A intervenção B apresenta sinal preliminar favorável, "
        "mas o MVP não trata esse resultado sintético como evidência causal conclusiva."
    )
    return {"metrics": metrics, "completion_gain": improvement, "recommendation": recommendation}

# -----------------------------
# UI HELPERS
# -----------------------------
def page_header(kicker: str, title: str, subtitle: str):
    st.markdown(f'<div class="nexo-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="nexo-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="nexo-sub">{subtitle}</div>', unsafe_allow_html=True)


def skill_chips(skill_ids: List[str], css="chip"):
    if not skill_ids:
        st.caption("Nenhuma competência registrada.")
        return
    html = " ".join([f'<span class="{css}">{SKILLS[s]["name"]}</span>' for s in skill_ids if s in SKILLS])
    st.markdown(html, unsafe_allow_html=True)


def metric_funnel():
    cols = st.columns(7)
    vals = [
        ("Demandas", 8), ("Skills", 23), ("Em trajetória", 76), ("Concluíram", 54),
        ("Skill demonstrada", 46), ("Contratados", 29), ("Retidos", 22)
    ]
    for c, (label, val) in zip(cols, vals):
        c.metric(label, val)


def flow_strip():
    steps = [
        ("1", "Demanda", "Sinais do mercado"),
        ("2", "Skills Intelligence", "Competências validadas"),
        ("3", "Adaptive Trajectory", "Percurso recomendado"),
        ("4", "Intervenção", "Experiência formativa"),
        ("5", "Learning-to-Outcome", "Aprendizagem e inserção"),
        ("6", "Feedback", "Empresa e participante"),
        ("7", "Policy Experiment", "Reformular ou escalar"),
    ]
    cols = st.columns(7)
    for col, (n, title, desc) in zip(cols, steps):
        col.markdown(f'<div class="flow"><b>{n}. {title}</b><br><span class="small-muted">{desc}</span></div>', unsafe_allow_html=True)


def disclaimer():
    st.caption("MVP demonstrativo para submissão ao CPSI. Dados de participantes, empresas, coortes e resultados são sintéticos. Recomendações de alto impacto exigem revisão humana.")

# -----------------------------
# PAGES
# -----------------------------
def page_overview():
    page_header(
        "VISÃO GERAL",
        "NEXO Qualifica+",
        "Sistema operacional de inteligência e gestão adaptativa de trajetórias para qualificação e inserção produtiva.",
    )
    st.markdown(
        '<div class="hero"><h3>Hipótese do MVP</h3><p>Fechar o circuito entre demanda produtiva, competências, trajetória, intervenção, aprendizagem, outcome e nova decisão pública.</p></div>',
        unsafe_allow_html=True,
    )
    flow_strip()
    st.write("")
    metric_funnel()

    st.subheader("Decisões recomendadas pelo sistema")
    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown(
            '<div class="decision"><b>Recomendação gerencial</b><br><br>A trilha de operações logísticas apresenta boa conclusão, mas o segmento com barreira digital perde conversão antes da demonstração prática. <br><br><b>Ação sugerida:</b> testar inclusão digital curta + tutoria na próxima coorte, mantendo o desenho comparativo.</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown('<div class="card"><h4>Princípios</h4><p>✓ Human-in-the-loop</p><p>✓ Explicabilidade</p><p>✓ Rastreabilidade</p><p>✓ Aprendizado contínuo</p><p>✓ Neutralidade tecnológica</p></div>', unsafe_allow_html=True)

    st.subheader("O que o MVP prova")
    cols = st.columns(4)
    cards = [
        ("Skills Intelligence", "Converte linguagem do mercado em competências estruturadas e validadas."),
        ("Adaptive Trajectory", "Recomenda percursos explicáveis sem automatizar elegibilidade."),
        ("Learning-to-Outcome", "Liga intervenção e aprendizagem aos resultados profissionais."),
        ("Policy Experiment", "Compara intervenções e transforma evidência em decisão de política."),
    ]
    for col, (title, body) in zip(cols, cards):
        col.markdown(f'<div class="card"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)
    disclaimer()


def page_demand_skills():
    page_header(
        "SKILLS INTELLIGENCE",
        "Demanda & Competências",
        "Transforma sinais do setor produtivo em competências estruturadas, com validação humana antes de qualquer uso operacional.",
    )

    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("1. Registrar sinal de demanda")
        company = st.selectbox("Empresa / origem", ["Atlântico Logística", "Empresa Alfa", "Conexão RH", "Balcão de Empregos"])
        text = st.text_area("Descrição da necessidade", st.session_state.selected_demand_text, height=160)
        st.session_state.selected_demand_text = text
        if st.button("Analisar demanda", type="primary", use_container_width=True):
            add_evidence("demand_analyzed", "Gestor Público", f"Demanda analisada — origem: {company}", source=company)
            st.success("Demanda analisada. Competências sugeridas pelo motor semântico demonstrativo.")

    extracted = extract_skills(st.session_state.selected_demand_text)
    with right:
        st.subheader("2. Competências sugeridas")
        st.caption("No MVP, a extração é determinística para ser reproduzível. A arquitetura admite embeddings/LLM no piloto.")
        for r in extracted.to_dict("records"):
            status = st.session_state.validated_skills.get(r["skill_id"], r["status"])
            with st.container(border=True):
                a, b = st.columns([4, 1])
                a.markdown(f"**{r['competência_sugerida']}**  \n{r['tipo']} • confiança {r['confiança']:.0%} • gatilho: `{r['gatilho']}`")
                b.markdown(f"**{status}**")
                c1, c2, c3 = st.columns(3)
                if c1.button("Validar", key=f"val_{r['skill_id']}", use_container_width=True):
                    st.session_state.validated_skills[r["skill_id"]] = "Validada"
                    add_evidence("skill_validated", "Gestor Público", f"Competência validada: {r['competência_sugerida']}")
                    st.rerun()
                if c2.button("Remapear", key=f"rem_{r['skill_id']}", use_container_width=True):
                    st.session_state.validated_skills[r["skill_id"]] = "Remapeada"
                    add_evidence("skill_remapped", "Gestor Público", f"Competência remapeada: {r['competência_sugerida']}")
                    st.rerun()
                if c3.button("Rejeitar", key=f"rej_{r['skill_id']}", use_container_width=True):
                    st.session_state.validated_skills[r["skill_id"]] = "Rejeitada"
                    add_evidence("skill_rejected", "Gestor Público", f"Competência rejeitada: {r['competência_sugerida']}")
                    st.rerun()

    st.subheader("3. Taxonomia operacional para a demanda")
    accepted = required_skills_from_demand(extracted)
    skill_chips(accepted)
    st.info("Human-in-the-loop: o motor sugere; o agente público valida, remapeia ou rejeita. A decisão e sua evidência ficam registradas.")
    disclaimer()


def page_trajectory():
    page_header(
        "ADAPTIVE TRAJECTORY",
        "Trajetórias",
        "Lê competências, gaps e barreiras operacionais para sugerir o próximo percurso — com explicação e decisão humana obrigatória.",
    )

    names = PARTICIPANTS.set_index("participant_id")["name"].to_dict()
    pid = st.selectbox(
        "Participante demonstrativo",
        options=list(names.keys()),
        format_func=lambda x: f"{names[x]} ({x})",
        index=list(names.keys()).index(st.session_state.selected_participant),
    )
    st.session_state.selected_participant = pid
    p = participant_record(pid)
    extracted = extract_skills(st.session_state.selected_demand_text)
    demand_skill_ids = required_skills_from_demand(extracted)
    gaps, readiness = gap_analysis(pid, demand_skill_ids)
    rec = recommend_path(pid, demand_skill_ids)
    st.session_state.recommendations[pid] = rec

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Participante", p["name"])
    c2.metric("Prontidão estimada", f"{readiness:.0%}")
    c3.metric("Gaps críticos", int((gaps["gap"] > 0).sum()))
    c4.metric("Barreiras registradas", len(p["barriers"]))

    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("Leitura de percurso")
        st.dataframe(gaps[["competência", "nível_atual", "nível_requerido", "situação"]], use_container_width=True, hide_index=True)
        st.markdown("**Barreiras operacionais relevantes**")
        if p["barriers"]:
            for b in p["barriers"]:
                st.markdown(f'<span class="chip chip-warn">{b}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="chip chip-good">Nenhuma barreira crítica registrada</span>', unsafe_allow_html=True)

    with right:
        st.subheader("Recomendação explicável")
        st.markdown(f'<div class="card"><h4>{rec["pathway"]}</h4><p><b>Intensidade:</b> {rec["intensity"]}</p><p>{rec["rationale"]}</p></div>', unsafe_allow_html=True)
        st.markdown("**Competências faltantes**")
        skill_chips(rec["missing_skills"], css="chip chip-warn")
        st.markdown('<div class="explain"><b>Limite algorítmico</b><br>Esta recomendação não decide elegibilidade, acesso ou exclusão. Ela organiza evidências para revisão humana.</div>', unsafe_allow_html=True)

    st.subheader("Decisão humana")
    a, b, c = st.columns(3)
    if a.button("✓ Aceitar recomendação", type="primary", use_container_width=True):
        st.session_state.manager_decision = "Aceita"
        add_trajectory_event(pid, "pathway_accepted", f"Percurso aceito: {rec['pathway']}", "Gestor Público")
        st.success("Percurso aceito e registrado no Evidence Ledger.")
    if b.button("↔ Alterar percurso", use_container_width=True):
        st.session_state.manager_decision = "Alterada"
        add_trajectory_event(pid, "pathway_changed", "Recomendação alterada por revisão humana", "Gestor Público")
        st.warning("Alteração registrada. No piloto real, o motivo deverá ser obrigatório e estruturado.")
    if c.button("✕ Rejeitar recomendação", use_container_width=True):
        st.session_state.manager_decision = "Rejeitada"
        add_trajectory_event(pid, "pathway_rejected", "Recomendação rejeitada por revisão humana", "Gestor Público")
        st.error("Rejeição registrada para posterior análise de divergência humano-algoritmo.")

    if st.session_state.trajectory_events:
        st.subheader("Linha do tempo da trajetória")
        df = pd.DataFrame(st.session_state.trajectory_events)
        st.dataframe(df[df.participant_id == pid], use_container_width=True, hide_index=True)
    disclaimer()


def page_learning():
    page_header(
        "ENGENHARIA EDUCACIONAL",
        "Intervenção Formativa",
        "Converte gaps de competências em objetivos de aprendizagem, experiências e avaliações — sem virar um LMS.",
    )

    pid = st.session_state.selected_participant
    p = participant_record(pid)
    extracted = extract_skills(st.session_state.selected_demand_text)
    demand_skill_ids = required_skills_from_demand(extracted)
    rec = recommend_path(pid, demand_skill_ids)

    st.markdown(f"### Blueprint para {p['name']}")
    st.caption(f"Percurso recomendado: {rec['pathway']}")

    modules = rec["recommended_modules"]
    if not modules:
        st.success("Não há módulo técnico crítico sugerido para o conjunto atual de competências.")
    else:
        for sid in modules:
            bp = LEARNING_BLUEPRINTS.get(sid, {
                "objective": f"Desenvolver a competência {SKILLS[sid]['name']} em nível operacional.",
                "strategy": "Prática guiada + resolução de situação-problema",
                "assessment": "Avaliação prática estruturada",
                "hours": 8,
            })
            with st.container(border=True):
                st.markdown(f"#### {SKILLS[sid]['name']}")
                a, b = st.columns([3, 1])
                a.write(f"**Objetivo de aprendizagem:** {bp['objective']}")
                b.metric("Carga sugerida", f"{bp['hours']}h")
                st.write(f"**Estratégia:** {bp['strategy']}")
                st.write(f"**Avaliação:** {bp['assessment']}")

    st.subheader("Teste de desenho adaptativo")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><h4>Configuração A — Padrão</h4><p>Trilha técnica direta, sem apoio adicional.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><h4>Configuração B — Adaptativa</h4><p>Trilha técnica + preparação funcional/digital + acompanhamento conforme barreira registrada.</p></div>', unsafe_allow_html=True)

    if st.button("Registrar intervenção para o participante", type="primary"):
        add_trajectory_event(pid, "learning_intervention", "Blueprint formativo vinculado à trajetória", "Equipe Qualifica+")
        st.success("Intervenção registrada. O outcome poderá ser relacionado à decisão e à formação aplicada.")
    disclaimer()


def page_experiments():
    page_header(
        "LEARNING-TO-OUTCOME + POLICY EXPERIMENT",
        "Experimentos & Outcomes",
        "Relaciona intervenção, aprendizagem e resultado profissional; compara coortes e orienta continuar, reformular ou escalar.",
    )
    st.warning("Os resultados abaixo são sintéticos e servem somente para demonstrar a lógica experimental do MVP.")

    st.subheader("Hipótese H2")
    st.markdown(
        '> **Se** participantes com barreiras de permanência receberem acompanhamento estruturado durante a formação, **então** a conclusão e a conversão para inserção laboral tendem a melhorar, **porque** barreiras são tratadas antes da ruptura.'
    )

    st.dataframe(EXPERIMENT_DATA, use_container_width=True, hide_index=True)

    summary = experiment_summary()
    m = summary["metrics"]
    cols = st.columns(3)
    cols[0].metric("Conclusão A", f"{m['completion_A']:.0%}")
    cols[1].metric("Conclusão B", f"{m['completion_B']:.0%}", delta=f"+{summary['completion_gain']:.0%}")
    cols[2].metric("Retenção B", f"{m['retention_B']:.0%}")

    st.subheader("Decisão baseada em evidência")
    st.markdown(f'<div class="decision"><b>Recomendação do Policy Experiment Engine</b><br><br>{summary["recommendation"]}</div>', unsafe_allow_html=True)

    st.subheader("Outcome longitudinal — caso demonstrativo")
    pid = st.session_state.selected_participant
    p = participant_record(pid)
    outcome_steps = pd.DataFrame([
        ["Ingresso", "Registrado", "Cadastro Qualifica+"],
        ["Participação", "Registrado", "Eventos da trajetória"],
        ["Conclusão", "Demonstrativo", "Instituição formadora"],
        ["Competência demonstrada", "Demonstrativo", "Avaliação prática"],
        ["Encaminhamento", "Demonstrativo", "Balcão de Empregos"],
        ["Contratação", "Demonstrativo", "Empresa"],
        ["Permanência", "Demonstrativo", "Retorno empresarial / fonte autorizada"],
    ], columns=["etapa", "status", "fonte"])
    st.markdown(f"**Participante:** {p['name']}")
    st.dataframe(outcome_steps, use_container_width=True, hide_index=True)

    st.subheader("Evidence Ledger")
    if not st.session_state.evidence_log:
        st.info("Interaja com as páginas de Demanda, Trajetórias e Engenharia Educacional para gerar evidências no ledger.")
    else:
        for ev in reversed(st.session_state.evidence_log[-10:]):
            st.markdown(
                f'<div class="evidence"><b>{ev["event_type"]}</b> • {ev["timestamp"]}<br>{ev["description"]}<br><span class="small-muted">Ator: {ev["actor"]} • Fonte: {ev["source"]} • Hash: {ev["hash"]}</span></div>',
                unsafe_allow_html=True,
            )

    if st.button("Registrar decisão: continuar teste", type="primary"):
        add_evidence("experiment_decision", "Gestor Público", "Decisão: continuar teste com nova coorte antes de escala")
        st.success("Decisão registrada com trilha de evidência.")
    disclaimer()

# -----------------------------
# SIDEBAR / ROUTER
# -----------------------------
st.sidebar.markdown("# NEXO Qualifica+")
st.sidebar.caption("CPSI MVP v1")
st.sidebar.markdown("---")

pages = [
    "Visão Geral",
    "Demanda & Competências",
    "Trajetórias",
    "Engenharia Educacional",
    "Experimentos & Outcomes",
]
page = st.sidebar.radio("Navegação", pages)

st.sidebar.markdown("---")
st.sidebar.markdown("**Fluxo experimental**")
st.sidebar.caption("Demanda → Skills → Trajetória → Intervenção → Outcome → Evidência → Decisão")
st.sidebar.markdown("---")
st.sidebar.caption("Dados sintéticos • recomendações explicáveis • supervisão humana")

if page == "Visão Geral":
    page_overview()
elif page == "Demanda & Competências":
    page_demand_skills()
elif page == "Trajetórias":
    page_trajectory()
elif page == "Engenharia Educacional":
    page_learning()
elif page == "Experimentos & Outcomes":
    page_experiments()
