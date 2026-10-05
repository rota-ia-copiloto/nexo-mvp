import hashlib
import json
import random
import gzip
import os
import re
import unicodedata
from difflib import SequenceMatcher
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
# OFFICIAL OCCUPATIONAL KNOWLEDGE LAYER
# -----------------------------
STOPWORDS = {
    "a","ao","aos","as","com","como","da","das","de","do","dos","e","em","entre","esta","este",
    "para","por","que","sem","ser","sua","suas","seu","seus","um","uma","uns","umas","preciso","precisa",
    "precisamos","profissional","profissionais","atuar","atuarem","vaga","vagas","contratar","contratacao",
    "trabalho","trabalhar","funcao","area","cargo","pessoa","pessoas"
}

SOURCE_REFERENCES = {
    "CBO": "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/pagina-inicial/",
    "QBQ": "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/quadro-brasileiro-de-qualificacoes-qbq",
    "GBO": "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/guia-brasileiro-de-ocupacoes",
    "CNCT": "https://cnct.mec.gov.br/",
    "MONITOR": "https://www.gov.br/mec/pt-br/centrais-de-conteudo/paineis-de-monitoramento-e-indicadores/monitor-de-profissoes",
    "ESCO": "https://esco.ec.europa.eu/pt/about-esco/what-esco",
}

CNCT_HINTS = [
    (["logistica", "estoque", "armazenagem", "expedicao"], "Técnico em Logística"),
    (["recrutamento", "recursos humanos", "pessoal"], "Técnico em Recursos Humanos"),
    (["enfermagem"], "Técnico em Enfermagem"),
    (["eletrotecnico", "eletricista", "eletrica"], "Técnico em Eletrotécnica"),
    (["desenvolvedor", "sistemas", "software", "programacao"], "Técnico em Desenvolvimento de Sistemas"),
    (["informatica", "suporte", "computacao"], "Técnico em Informática"),
    (["edificacoes", "obras civis", "construcao civil"], "Técnico em Edificações"),
    (["seguranca do trabalho", "seguranca ocupacional"], "Técnico em Segurança do Trabalho"),
    (["administracao", "administrativo", "escritorio"], "Técnico em Administração"),
    (["contabilidade", "contabil"], "Técnico em Contabilidade"),
    (["mecanica", "manutencao mecanica"], "Técnico em Mecânica"),
    (["mecatronica", "automacao"], "Técnico em Mecatrônica"),
    (["quimica", "processos quimicos", "petroquimica"], "Técnico em Química"),
    (["meio ambiente", "ambiental"], "Técnico em Meio Ambiente"),
]


def suggest_cnct_courses(text: str):
    t = normalize_text(text)
    found = []
    for triggers, course in CNCT_HINTS:
        if any(normalize_text(k) in t for k in triggers):
            found.append(course)
    return list(dict.fromkeys(found))[:3]


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def stem_token(token: str) -> str:
    # Stem leve apenas para aumentar cobertura lexical do MVP (ex.: recrutadores -> recrutador).
    t = token
    if len(t) > 6 and t.endswith("oes"):
        t = t[:-3] + "ao"
    elif len(t) > 5 and t.endswith("es"):
        t = t[:-2]
    elif len(t) > 4 and t.endswith("s"):
        t = t[:-1]
    return t


def meaningful_tokens(text: str):
    return {
        stem_token(t) for t in normalize_text(text).split()
        if len(t) >= 3 and t not in STOPWORDS
    }


@st.cache_data(show_spinner=False)
def load_occupational_knowledge():
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "occupational_knowledge.json.gz")
    if not os.path.exists(path):
        return {"metadata": {}, "occupations": []}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    for rec in data.get("occupations", []):
        rec["_title_norm"] = normalize_text(rec.get("occupation", ""))
        rec["_title_tokens"] = list(meaningful_tokens(rec.get("occupation", "")))
    return data


OCCUPATIONAL_KB = load_occupational_knowledge()
OCCUPATIONS = OCCUPATIONAL_KB.get("occupations", [])


OCCUPATION_ALIAS_CBO = {
    "recrutador": "351315",
    "recrutamento": "351315",
    "programador": "317110",
    "desenvolvedor": "317110",
    "desenvolvedor software": "317110",
    "rh": "252405",
    "recursos humanos": "252405",
    "auxiliar logistica": "414140",
    "empilhadeira": "782220",
    "operador empilhadeira": "782220",
    "tecnico enfermagem": "322205",
    "eletricista industrial": "715615",
}


def occupation_matches(text: str, top_n: int = 5):
    q_norm = normalize_text(text)
    q_tokens = meaningful_tokens(text)
    if not q_tokens:
        return []
    scored = []
    alias_boost = {}
    for alias, cbo in OCCUPATION_ALIAS_CBO.items():
        if normalize_text(alias) in q_norm:
            alias_boost[cbo] = max(alias_boost.get(cbo, 0), 35)
    for rec in OCCUPATIONS:
        title = rec.get("_title_norm", "")
        title_tokens = {stem_token(t) for t in rec.get("_title_tokens", [])}
        search_tokens = meaningful_tokens(rec.get("search_text", ""))
        title_overlap = len(q_tokens & title_tokens)
        context_overlap = len(q_tokens & search_tokens)
        # Aproxima palavras derivadas da mesma raiz (recrutador/recrutamento, administrar/administração).
        q_prefixes = {t[:6] for t in q_tokens if len(t) >= 6}
        title_prefixes = {t[:6] for t in title_tokens if len(t) >= 6}
        search_prefixes = {t[:6] for t in search_tokens if len(t) >= 6}
        prefix_title_overlap = len(q_prefixes & title_prefixes)
        prefix_context_overlap = len(q_prefixes & search_prefixes)
        score = (
            title_overlap * 10
            + prefix_title_overlap * 8
            + min(context_overlap, 8) * 1.35
            + min(prefix_context_overlap, 8) * 2.4
        )
        if title and (title in q_norm or q_norm in title):
            score += 15
        # Similaridade lexical recebe peso limitado; evita transformar o score em falsa probabilidade.
        ratio = SequenceMatcher(None, " ".join(sorted(q_tokens)), title).ratio()
        score += ratio * 5
        score += alias_boost.get(str(rec.get("cbo", "")), 0)
        if score > 2.5:
            scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return []
    max_score = scored[0][0]
    out = []
    for score, rec in scored[:top_n]:
        adherence = min(0.98, max(0.35, 0.45 + 0.50 * (score / max_score)))
        out.append({"score": score, "adherence": adherence, "record": rec})
    return out


def register_dynamic_skill(skill_id: str, name: str, skill_type: str, source: str, cbo: str = ""):
    SKILLS[skill_id] = {
        "name": name,
        "type": skill_type,
        "source": source,
        "cbo": cbo,
    }

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
    "SK013": {"name": "Recrutamento e seleção", "type": "Técnica"},
    "SK014": {"name": "Triagem de currículos", "type": "Técnica"},
    "SK015": {"name": "Entrevista por competências", "type": "Técnica"},
    "SK016": {"name": "Sistemas de recrutamento / ATS", "type": "Digital"},
    "SK017": {"name": "Análise de perfil", "type": "Técnica"},
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
    "recrutador": "SK013",
    "recrutadores": "SK013",
    "recrutamento": "SK013",
    "seleção": "SK013",
    "currículo": "SK014",
    "curriculos": "SK014",
    "triagem": "SK014",
    "entrevista": "SK015",
    "ats": "SK016",
    "sistema de recrutamento": "SK016",
    "perfil": "SK017",
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
        "demand_analyzed": False,
        "last_analyzed_text": "",
        "demand_quantity": 20,
        "demand_horizon": "Próximos 3 meses",
        "remap_target": {},
        "occupation_matches": [],
        "selected_cbo": None,
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
    """Relaciona demanda livre a ocupações CBO e competências QBQ.

    Núcleo oficial do MVP:
    - CBO: identificação/classificação ocupacional;
    - QBQ: perfil, conhecimentos, habilidades e atitudes por ocupação.

    GBO, Monitor de Profissões, CNCT e ESCO entram como camadas complementares
    de contexto de mercado, itinerários formativos e enriquecimento semântico.
    """
    rows = []
    seen = set()
    matches = occupation_matches(text, top_n=5)
    st.session_state.occupation_matches = [
        {
            "cbo": m["record"].get("cbo"),
            "occupation": m["record"].get("occupation"),
            "adherence": m["adherence"],
            "qualification_level": m["record"].get("qualification_level"),
            "summary": m["record"].get("summary"),
            "profile": m["record"].get("profile"),
        }
        for m in matches
    ]

    # Usa a ocupação mais aderente como referência principal e uma segunda quando muito próxima.
    selected = []
    if matches:
        selected.append(matches[0])
        if len(matches) > 1 and matches[1]["score"] >= matches[0]["score"] * 0.82:
            selected.append(matches[1])

    for match_rank, m in enumerate(selected):
        rec = m["record"]
        cbo = rec.get("cbo", "")
        occ = rec.get("occupation", "")
        base_conf = m["adherence"]
        # Habilidades recebem maior peso operacional; conhecimentos e atitudes complementam a matriz.
        components = [
            ("H", rec.get("skills", [])[:6], "Habilidade (QBQ)", 0.98),
            ("K", rec.get("knowledge", [])[:4], "Conhecimento (QBQ)", 0.92),
            ("A", rec.get("attitudes", [])[:2], "Atitude (QBQ)", 0.86),
        ]
        for kind, items, label, factor in components:
            for idx, item in enumerate(items):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                dedupe = normalize_text(name)
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                sid = f"QBQ_{cbo}_{kind}_{idx:02d}"
                register_dynamic_skill(sid, name, label, "QBQ/CBO", cbo)
                importance = float(item.get("importance", 0) or 0)
                importance_adj = min(1.0, max(0.6, importance / 5 if importance else 0.75))
                confidence = min(0.98, base_conf * factor * importance_adj + 0.08)
                rows.append({
                    "skill_id": sid,
                    "competência_sugerida": name,
                    "tipo": label,
                    "confiança": confidence,
                    "gatilho": f"CBO {cbo} — {occ}",
                    "fonte": "QBQ/CBO",
                    "status": st.session_state.validated_skills.get(sid, "Pendente"),
                })

    # Termos explícitos continuam úteis como complemento da linguagem livre da empresa.
    text_l = normalize_text(text)
    for keyword, skill_id in KEYWORD_TO_SKILL.items():
        if normalize_text(keyword) in text_l and skill_id not in seen:
            key_name = normalize_text(SKILLS[skill_id]["name"])
            if key_name in seen:
                continue
            seen.add(key_name)
            rows.append({
                "skill_id": skill_id,
                "competência_sugerida": SKILLS[skill_id]["name"],
                "tipo": SKILLS[skill_id]["type"],
                "confiança": 0.78,
                "gatilho": f"termo explícito: {keyword}",
                "fonte": "Demanda empresarial",
                "status": st.session_state.validated_skills.get(skill_id, "Pendente"),
            })

    return pd.DataFrame(rows, columns=[
        "skill_id", "competência_sugerida", "tipo", "confiança", "gatilho", "fonte", "status"
    ])


def required_skills_from_demand(df: pd.DataFrame) -> List[str]:
    accepted = []
    for r in df.to_dict("records"):
        sid = r["skill_id"]
        status = st.session_state.validated_skills.get(sid, r.get("status", "Pendente"))
        if status == "Validada":
            accepted.append(sid)
        elif isinstance(status, str) and status.startswith("Remapeada:"):
            accepted.append(status.split(":", 1)[1])
    if accepted:
        return list(dict.fromkeys(accepted))
    return df["skill_id"].tolist() if not df.empty else []


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
        "Demanda do setor produtivo",
        "Transforma uma necessidade empresarial em competências estruturadas e validadas por humanos antes de alimentar trajetórias ou formação.",
    )

    st.markdown(
        '<div class="explain"><b>Como ler esta tela:</b> a empresa descreve a necessidade → o NEXO sugere competências → o agente público valida, remapeia ou rejeita → somente as competências validadas entram na taxonomia operacional.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    st.subheader("1. Descreva a necessidade")
    c1, c2, c3 = st.columns([1.2, .6, .8])
    with c1:
        company = st.selectbox("Empresa / origem", ["Atlântico Logística", "Empresa Alfa", "Conexão RH", "Balcão de Empregos"])
    with c2:
        quantity = st.number_input("Quantidade prevista", min_value=1, max_value=5000, value=int(st.session_state.demand_quantity), step=1)
        st.session_state.demand_quantity = quantity
    with c3:
        horizon = st.selectbox(
            "Horizonte da contratação",
            ["Próximos 30 dias", "Próximos 3 meses", "Próximos 6 meses", "Próximos 12 meses"],
            index=1,
        )
        st.session_state.demand_horizon = horizon

    text = st.text_area(
        "Descrição da demanda",
        st.session_state.selected_demand_text,
        height=140,
        placeholder="Ex.: Preciso de 100 profissionais para atuarem como recrutadores...",
    )
    st.session_state.selected_demand_text = text

    if st.button("Analisar demanda", type="primary", use_container_width=True):
        # Nova análise = novo ciclo de validação. Evita carregar decisões de uma demanda anterior.
        if text.strip() != st.session_state.last_analyzed_text.strip():
            st.session_state.validated_skills = {}
            st.session_state.remap_target = {}
        st.session_state.last_analyzed_text = text
        st.session_state.demand_analyzed = True
        add_evidence(
            "demand_analyzed",
            "Gestor Público",
            f"Demanda analisada — origem: {company}; quantidade: {quantity}; horizonte: {horizon}",
            source=company,
        )
        st.success("Demanda analisada. Revise as competências sugeridas antes de incorporá-las à taxonomia operacional.")

    if not st.session_state.demand_analyzed:
        st.info("Preencha a demanda e clique em **Analisar demanda** para gerar sugestões de competências.")
        disclaimer()
        return

    extracted = extract_skills(st.session_state.last_analyzed_text)

    st.subheader("2. Ocupações de referência identificadas")
    matches = st.session_state.get("occupation_matches", [])
    if matches:
        match_df = pd.DataFrame([
            {
                "CBO": m["cbo"],
                "Ocupação de referência": m["occupation"],
                "Aderência lexical/contextual": f"{m['adherence']:.0%}",
                "Nível QBQ": m.get("qualification_level") or "—",
            }
            for m in matches[:5]
        ])
        st.dataframe(match_df, use_container_width=True, hide_index=True)
        principal = matches[0]
        st.session_state.selected_cbo = principal["cbo"]
        with st.expander(f"Ver perfil oficial da ocupação principal — CBO {principal['cbo']} · {principal['occupation']}"):
            st.markdown("**Síntese ocupacional**")
            st.write(principal.get("summary") or "Não disponível na base carregada.")
            st.markdown("**Perfil ocupacional**")
            st.write(principal.get("profile") or "Não disponível na base carregada.")
            st.caption("Referência principal: CBO + Quadro Brasileiro de Qualificações (QBQ).")
            course_hints = suggest_cnct_courses(" ".join([principal.get("occupation", ""), principal.get("summary", "")]))
            if course_hints:
                st.markdown("**Referências formativas potenciais no CNCT/MEC**")
                for course in course_hints:
                    st.markdown(f"- {course}")
                st.caption("Referência orientativa do MVP; no piloto, a associação CBO↔curso deve ser carregada diretamente do CNCT e validada pela engenharia educacional.")
    else:
        st.warning("Não foi possível associar a descrição a uma ocupação CBO com aderência mínima. Refine o texto com o título da função e suas principais atividades.")

    st.subheader("3. Competências identificadas pelo NEXO")
    st.caption("A ocupação é associada à CBO e as competências são trazidas do QBQ. O score exibido é aderência lexical/contextual do protótipo, não probabilidade estatística. No piloto, ESCO/embeddings/LLM podem ampliar sinônimos e equivalências, sempre com validação humana.")

    if extracted.empty:
        st.warning(
            "O MVP não encontrou competências com segurança suficiente nesta descrição. "
            "Isso é preferível a inventar uma competência genérica. No piloto, o motor semântico ampliará a cobertura e manterá revisão humana."
        )
    else:
        for r in extracted.to_dict("records"):
            skill_id = r["skill_id"]
            status = st.session_state.validated_skills.get(skill_id, "Pendente")
            with st.container(border=True):
                a, b = st.columns([4, 1])
                a.markdown(
                    f"**{r['competência_sugerida']}**  \n"
                    f"{r['tipo']} • aderência {r['confiança']:.0%} • fonte: **{r.get('fonte','NEXO')}**  \n"
                    f"Referência: `{r['gatilho']}`"
                )
                b.markdown(f"**Status: {status}**")

                if status == "Remapeando":
                    options = [sid for sid in SKILLS.keys() if sid != skill_id]
                    target = st.selectbox(
                        "Remapear para",
                        options=options,
                        format_func=lambda sid: SKILLS[sid]["name"],
                        key=f"remap_select_{skill_id}",
                    )
                    rc1, rc2 = st.columns(2)
                    if rc1.button("Confirmar remapeamento", key=f"confirm_rem_{skill_id}", use_container_width=True):
                        st.session_state.validated_skills[skill_id] = f"Remapeada:{target}"
                        st.session_state.remap_target[skill_id] = target
                        add_evidence(
                            "skill_remapped",
                            "Gestor Público",
                            f"Competência remapeada: {r['competência_sugerida']} → {SKILLS[target]['name']}",
                        )
                        st.rerun()
                    if rc2.button("Cancelar", key=f"cancel_rem_{skill_id}", use_container_width=True):
                        st.session_state.validated_skills[skill_id] = "Pendente"
                        st.rerun()
                else:
                    c1, c2, c3 = st.columns(3)
                    if c1.button("Validar", key=f"val_{skill_id}", use_container_width=True):
                        st.session_state.validated_skills[skill_id] = "Validada"
                        add_evidence("skill_validated", "Gestor Público", f"Competência validada: {r['competência_sugerida']}")
                        st.rerun()
                    if c2.button("Remapear", key=f"rem_{skill_id}", use_container_width=True):
                        st.session_state.validated_skills[skill_id] = "Remapeando"
                        st.rerun()
                    if c3.button("Rejeitar", key=f"rej_{skill_id}", use_container_width=True):
                        st.session_state.validated_skills[skill_id] = "Rejeitada"
                        add_evidence("skill_rejected", "Gestor Público", f"Competência rejeitada: {r['competência_sugerida']}")
                        st.rerun()

    st.subheader("4. Matriz de competências validada para esta demanda")
    operational = []
    for r in extracted.to_dict("records"):
        sid = r["skill_id"]
        status = st.session_state.validated_skills.get(sid, "Pendente")
        if status == "Validada":
            operational.append(sid)
        elif status.startswith("Remapeada:"):
            operational.append(status.split(":", 1)[1])

    if operational:
        # preserva ordem e remove duplicatas
        operational = list(dict.fromkeys(operational))
        skill_chips(operational)
        st.success(
            f"{len(operational)} competência(s) validada(s). Essas competências já podem alimentar análise de gaps, trajetórias e engenharia educacional."
        )
    else:
        st.info("Nenhuma competência foi incorporada ainda. Valide ou remapeie pelo menos uma sugestão acima.")

    st.info("**Human-in-the-loop:** o NEXO sugere; o agente público decide. Nenhuma competência é incorporada automaticamente à política.")

    with st.expander("Fontes de referência e como o NEXO as utiliza"):
        st.markdown(
            """
            **CBO — Classificação Brasileira de Ocupações:** identifica e codifica a ocupação de referência.  
            **QBQ — Quadro Brasileiro de Qualificações:** fornece perfil ocupacional, conhecimentos, habilidades, atitudes e nível de qualificação.  
            **GBO — Guia Brasileiro de Ocupações:** referência para leitura do conteúdo ocupacional e indicadores do mercado formal.  
            **CNCT/MEC — Catálogo Nacional de Cursos Técnicos:** referência para relacionar ocupações a itinerários e perfis de formação técnica.  
            **Monitor de Profissões MEC/ABDI:** referência para aproximar oferta educacional, ocupações e dinâmica de mercado.  
            **ESCO:** camada complementar para sinônimos, equivalências semânticas e relacionamento ocupação–competências em arquitetura interoperável.
            """
        )
        st.caption(f"No MVP v1.2, CBO/QBQ formam a base operacional local com {len(OCCUPATIONS):,} ocupações. As demais fontes orientam a camada complementar de mercado, formação e interoperabilidade do piloto.".replace(",", "."))
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
st.sidebar.caption("CPSI MVP v1.2 — CBO/QBQ")
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
