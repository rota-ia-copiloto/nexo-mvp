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
        "demand_company": "Conexão RH",
        "remap_target": {},
        "occupation_matches": [],
        "selected_cbo": None,
        "candidate_profiles": {},
        "qualifica_recommendations": {},
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
        "Inteligência territorial, demanda produtiva e gestão adaptativa de trajetórias para qualificação e inserção produtiva.",
    )

    # ------------------------------------------------------------
    # BLOCO TERRITORIAL-ECONÔMICO — valores demonstrativos do MVP
    # ------------------------------------------------------------
    st.subheader("Contexto territorial e econômico")
    st.caption(
        "Indicadores demonstrativos para o MVP. Na implantação, este bloco deverá ser alimentado por fontes oficiais e registros municipais, "
        "com atualização conforme a periodicidade de cada base."
    )

    territorial = st.columns(6)
    territorial_metrics = [
        ("Saldo Novo Caged — 12m", "+2.340", "Empregos formais", "Novo Caged"),
        ("Estoque formal", "98.420", "Vínculos ativos", "RAIS / Novo Caged"),
        ("PIB municipal", "R$ 47,8 bi", "Referência econômica", "IBGE"),
        ("PIB per capita", "R$ 180 mil", "Referência econômica", "IBGE"),
        ("Novos investimentos", "R$ 1,8 bi", "Monitorados", "Radar municipal"),
        ("Empregos potenciais", "1.250", "Associados a investimentos", "Empresas / projetos"),
    ]
    for col, (label, value, help_text, source) in zip(territorial, territorial_metrics):
        col.metric(label, value, help=help_text)
        col.caption(f"Fonte: {source}")

    st.markdown(
        '<div class="card"><b>Leitura territorial:</b> o NEXO combina indicadores de emprego, estrutura econômica e novos investimentos para contextualizar a demanda por competências antes de recomendar intervenções formativas.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown("#### Pressões de demanda no território")
        pressure_df = pd.DataFrame(
            [
                {"Setor": "Logística e operações", "Sinal": "Alta", "Indicador demonstrativo": "+420 vagas / 12m", "Implicação": "Reforçar competências operacionais e digitais"},
                {"Setor": "Serviços empresariais e RH", "Sinal": "Média-alta", "Indicador demonstrativo": "+180 vagas / 12m", "Implicação": "Recrutamento, atendimento e ferramentas digitais"},
                {"Setor": "Manutenção industrial", "Sinal": "Alta", "Indicador demonstrativo": "3 investimentos monitorados", "Implicação": "Formação técnica e certificações"},
            ]
        )
        st.dataframe(pressure_df, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### Investimentos monitorados")
        investments_df = pd.DataFrame(
            [
                {"Projeto": "Expansão logística", "Horizonte": "12–18 meses", "Empregos potenciais": 420},
                {"Projeto": "Nova operação de serviços", "Horizonte": "6–12 meses", "Empregos potenciais": 180},
                {"Projeto": "Ampliação industrial", "Horizonte": "18–24 meses", "Empregos potenciais": 650},
            ]
        )
        st.dataframe(investments_df, use_container_width=True, hide_index=True)

    st.divider()

    # ------------------------------------------------------------
    # HIPÓTESE E CIRCUITO EXPERIMENTAL DO MVP
    # ------------------------------------------------------------
    st.markdown(
        '<div class="hero"><h3>Hipótese do MVP</h3><p>Fechar o circuito entre contexto territorial, demanda produtiva, competências, trajetória, intervenção, aprendizagem, outcome e nova decisão pública.</p></div>',
        unsafe_allow_html=True,
    )
    flow_strip()
    st.write("")

    st.subheader("Pipeline experimental do NEXO")
    st.caption("Os indicadores abaixo são sintéticos e demonstram o funcionamento do circuito do MVP.")
    metric_funnel()

    st.subheader("Decisões recomendadas pelo sistema")
    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown(
            '<div class="decision"><b>Recomendação gerencial</b><br><br>Os sinais territoriais indicam pressão de demanda em operações logísticas, enquanto o experimento mostra boa conclusão da trilha, mas perda de conversão no segmento com barreira digital antes da demonstração prática. <br><br><b>Ação sugerida:</b> testar inclusão digital curta + tutoria na próxima coorte e acompanhar se a intervenção reduz o gap de conversão para contratação.</div>',
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

    st.caption(
        "Fontes previstas para produção: Novo Caged, RAIS, IBGE, registros municipais, radar de investimentos, empresas e parceiros. "
        "Os valores territoriais exibidos nesta versão são demonstrativos; dados reais deverão ser integrados na etapa de implantação/piloto."
    )
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
        company = st.selectbox("Empresa / origem", ["Atlântico Logística", "Empresa Alfa", "Conexão RH", "Balcão de Empregos"], index=["Atlântico Logística", "Empresa Alfa", "Conexão RH", "Balcão de Empregos"].index(st.session_state.get("demand_company", "Conexão RH")))
        st.session_state.demand_company = company
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


def _income_support_signal(income_range: str) -> bool:
    return income_range in {"Sem renda", "Até R$ 1.000"}


def _infer_skills_from_occupation(occupation_text: str) -> List[str]:
    """Retorna nomes de habilidades QBQ associadas à ocupação anterior informada."""
    if not occupation_text.strip():
        return []
    matches = occupation_matches(occupation_text, top_n=1)
    if not matches:
        return []
    rec = matches[0]["record"]
    names = []
    for item in rec.get("skills", [])[:8]:
        name = str(item.get("name", "")).strip()
        if name:
            names.append(name)
    return names


def _competence_overlap(name: str, candidates: List[str]) -> bool:
    n = normalize_text(name)
    nt = meaningful_tokens(n)
    for c in candidates:
        cn = normalize_text(c)
        ct = meaningful_tokens(cn)
        if n == cn or (nt and ct and len(nt & ct) >= max(1, min(len(nt), len(ct)) // 2)):
            return True
    return False


def diagnose_candidate(profile: Dict, demand_skill_ids: List[str]) -> Dict:
    demanded = [SKILLS[sid]["name"] for sid in demand_skill_ids if sid in SKILLS]
    self_declared = profile.get("self_declared_skills", [])
    inferred = _infer_skills_from_occupation(profile.get("last_occupation", ""))

    evidence_rows = []
    covered = 0
    for name in demanded:
        sources = []
        if _competence_overlap(name, self_declared):
            sources.append("Autodeclarada")
        if _competence_overlap(name, inferred):
            sources.append("Inferida da experiência (CBO/QBQ)")
        if sources:
            covered += 1
        evidence_rows.append({
            "competência demandada": name,
            "evidência atual": " + ".join(sources) if sources else "Sem evidência registrada",
            "situação": "Com evidência" if sources else "Gap a verificar/desenvolver",
        })

    alignment = covered / max(len(demanded), 1)
    barriers = []
    if _income_support_signal(profile.get("personal_income", "")) or profile.get("income_urgency") == "Alta":
        barriers.append("Pressão econômica / necessidade imediata de renda")
    if profile.get("digital_access") in {"Internet instável", "Somente smartphone", "Sem acesso regular"}:
        barriers.append("Acesso digital limitado")
    if profile.get("digital_autonomy") in {"Baixa", "Muito baixa"}:
        barriers.append("Baixa autonomia digital")
    if profile.get("transport_barrier"):
        barriers.append("Restrição de transporte / deslocamento")
    if int(profile.get("commute_minutes", 0) or 0) >= 60:
        barriers.append("Tempo elevado de deslocamento")
    if profile.get("care_responsibility"):
        barriers.append("Responsabilidade de cuidado")
    if profile.get("schedule_restriction"):
        barriers.append("Restrição de horário")

    years_exp = float(profile.get("years_experience", 0) or 0)
    months_out = int(profile.get("months_out", 0) or 0)
    first_job = bool(profile.get("first_job"))
    career_change = bool(profile.get("career_change"))
    age = int(profile.get("age", 0) or 0)

    if first_job or years_exp < 1:
        experience_status = "Primeiro acesso / experiência inicial"
    elif years_exp >= 3:
        experience_status = "Experiência consolidada"
    else:
        experience_status = "Experiência em construção"

    if alignment >= .67:
        skills_status = "Aderência elevada às competências da demanda"
    elif alignment >= .34:
        skills_status = "Aderência parcial — há gaps focalizados"
    else:
        skills_status = "Baixa aderência atual — requer desenvolvimento"

    digital_status = "Adequado" if profile.get("digital_access") == "Internet e dispositivo adequados" and profile.get("digital_autonomy") in {"Alta", "Média"} else "Requer apoio"
    mobility_status = "Requer ajuste" if profile.get("transport_barrier") or int(profile.get("commute_minutes", 0) or 0) >= 60 else "Adequada"
    permanence_status = "Requer acompanhamento" if len(barriers) >= 2 else "Sem barreira crítica identificada"

    # Regras explicáveis para o MVP. No piloto, esta camada pode incorporar IA supervisionada.
    if first_job and (age <= 24 or years_exp < 1) and len(barriers) >= 1:
        initial = "Qualifica+ Travessias"
        next_step = "Qualifica+ Conecta"
        rationale = "Trajetória profissional inicial combinada a necessidade de preparação e mediação mais intensiva."
    elif len(barriers) >= 2:
        initial = "Qualifica+ Inclusão"
        next_step = "Qualifica+ Conecta"
        rationale = "Foram identificadas barreiras concretas de participação/permanência que devem ser tratadas antes ou junto da qualificação técnica."
    elif months_out >= 12 or career_change:
        initial = "Qualifica+ Novos Rumos"
        next_step = "Qualifica+ Conecta"
        rationale = "Há ruptura, afastamento prolongado ou intenção de reconstrução/transição profissional."
    else:
        initial = "Qualifica+ Conecta"
        next_step = "Conexão direta com trilha aderente e oportunidades produtivas"
        rationale = "O perfil apresenta condições de participação e potencial de conexão mais direta com demandas produtivas."

    dimensions = [
        ("Experiência profissional", experience_status),
        ("Competências frente à demanda", skills_status),
        ("Acesso e autonomia digital", digital_status),
        ("Mobilidade territorial", mobility_status),
        ("Condições de permanência", permanence_status),
    ]

    return {
        "demanded_skills": demanded,
        "evidence_rows": evidence_rows,
        "alignment": alignment,
        "barriers": list(dict.fromkeys(barriers)),
        "dimensions": dimensions,
        "initial_journey": initial,
        "next_journey": next_step,
        "rationale": rationale,
        "inferred_skills": inferred,
    }


def page_trajectory():
    page_header(
        "DIAGNÓSTICO & TRAJETÓRIA",
        "Perfil, diagnóstico e jornada Qualifica+",
        "A pessoa informa sua trajetória, condições de participação, competências e objetivos. O NEXO organiza as evidências e sugere uma jornada para revisão humana.",
    )

    st.info(
        "**Princípio metodológico:** o NEXO não atribui uma nota geral de empregabilidade nem classifica vulnerabilidade como destino. "
        "Ele identifica ativos, gaps e barreiras concretas para apoiar uma decisão compartilhada sobre a trajetória."
    )

    names = PARTICIPANTS.set_index("participant_id")["name"].to_dict()
    pid = st.selectbox(
        "Participante demonstrativo",
        options=list(names.keys()),
        format_func=lambda x: f"{names[x]} ({x})",
        index=list(names.keys()).index(st.session_state.selected_participant),
    )
    st.session_state.selected_participant = pid
    seed = participant_record(pid)

    extracted = extract_skills(st.session_state.selected_demand_text)
    demand_skill_ids = required_skills_from_demand(extracted)
    demand_skill_names = [SKILLS[sid]["name"] for sid in demand_skill_ids if sid in SKILLS]

    existing = st.session_state.candidate_profiles.get(pid, {})

    st.markdown("### Preenchimento do perfil")
    st.caption("Etapas: 1. Perfil → 2. Trajetória profissional → 3. Condições de participação → 4. Competências → 5. Objetivos → 6. Diagnóstico → 7. Jornada sugerida")

    with st.form(f"candidate_profile_{pid}"):
        st.markdown("#### 1. Perfil")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Nome", value=existing.get("name", seed["name"]))
        age = c2.number_input("Idade", min_value=16, max_value=80, value=int(existing.get("age", seed["age"])))
        neighborhood = c3.text_input("Bairro / região de residência", value=existing.get("neighborhood", ""), placeholder="Ex.: Cidade Nova")
        c1, c2, c3 = st.columns(3)
        education = c1.selectbox("Escolaridade", ["Fundamental incompleto", "Fundamental completo", "Ensino Médio", "Técnico", "Superior incompleto", "Superior completo"], index=2)
        employment_status = c2.selectbox("Situação atual de trabalho", ["Desempregada(o)", "Emprego formal", "Trabalho informal", "Autônoma(o)", "Primeiro emprego"])
        availability = c3.multiselect("Disponibilidade", ["Manhã", "Tarde", "Noite", "Finais de semana"], default=existing.get("availability_slots", ["Manhã", "Tarde"]))

        st.markdown("#### 2. Trajetória profissional")
        c1, c2, c3 = st.columns(3)
        last_occupation = c1.text_input("Última ocupação / ocupação atual", value=existing.get("last_occupation", ""), placeholder="Ex.: Auxiliar de estoque")
        years_experience = c2.number_input("Anos aproximados de experiência profissional", min_value=0.0, max_value=50.0, step=0.5, value=float(existing.get("years_experience", 1.0)))
        months_out = c3.number_input("Meses fora do mercado formal", min_value=0, max_value=240, value=int(existing.get("months_out", 6)))
        c1, c2 = st.columns(2)
        first_job = c1.checkbox("Busca primeiro emprego / não possui experiência profissional relevante", value=existing.get("first_job", False))
        career_change = c2.checkbox("Deseja reconstruir a trajetória ou mudar de área", value=existing.get("career_change", False))

        st.markdown("#### 3. Condições socioeconômicas e de participação")
        c1, c2, c3 = st.columns(3)
        personal_income = c1.selectbox("Faixa de renda individual atual", ["Sem renda", "Até R$ 1.000", "R$ 1.001 a R$ 2.000", "R$ 2.001 a R$ 4.000", "Acima de R$ 4.000", "Prefiro não responder"])
        household_income = c2.selectbox("Faixa de renda familiar", ["Até R$ 2.000", "R$ 2.001 a R$ 4.000", "R$ 4.001 a R$ 8.000", "Acima de R$ 8.000", "Prefiro não responder"])
        income_urgency = c3.selectbox("Urgência de geração de renda", ["Baixa", "Média", "Alta"])

        c1, c2, c3 = st.columns(3)
        digital_access = c1.selectbox("Acesso digital", ["Internet e dispositivo adequados", "Somente smartphone", "Internet instável", "Sem acesso regular"])
        digital_autonomy = c2.selectbox("Autonomia para usar ferramentas digitais", ["Alta", "Média", "Baixa", "Muito baixa"])
        commute_minutes = c3.number_input("Tempo máximo aceitável de deslocamento (min.)", min_value=0, max_value=180, value=int(existing.get("commute_minutes", 45)))

        c1, c2, c3 = st.columns(3)
        transport_barrier = c1.checkbox("Possui dificuldade relevante de transporte/deslocamento", value=existing.get("transport_barrier", False))
        care_responsibility = c2.checkbox("Possui responsabilidade de cuidado que afeta disponibilidade", value=existing.get("care_responsibility", False))
        schedule_restriction = c3.checkbox("Possui restrição importante de horário", value=existing.get("schedule_restriction", False))

        st.markdown("#### 4. Competências")
        st.caption("As competências abaixo vêm da demanda atualmente analisada. A pessoa informa quais reconhece possuir; outras evidências podem ser inferidas da experiência ocupacional via CBO/QBQ e posteriormente validadas por avaliação, certificado, formador ou empregador.")
        self_declared_skills = st.multiselect(
            "Quais destas competências você considera possuir?",
            demand_skill_names,
            default=[s for s in existing.get("self_declared_skills", []) if s in demand_skill_names],
        )

        st.markdown("#### 5. Objetivos")
        c1, c2 = st.columns(2)
        main_goal = c1.selectbox("Principal objetivo neste momento", ["Encontrar emprego rapidamente", "Conseguir primeiro emprego", "Mudar de área", "Retomar trajetória profissional", "Melhorar renda", "Obter qualificação técnica", "Empreender"])
        desired_area = c2.text_input("Área ou ocupação de interesse", value=existing.get("desired_area", ""), placeholder="Ex.: Logística, RH, manutenção")

        consent = st.checkbox("Confirmo que as informações poderão ser usadas para orientar minha trajetória no programa e gerar análises agregadas para melhoria da política, observadas as regras de proteção de dados.", value=True)
        submitted = st.form_submit_button("Gerar diagnóstico e jornada sugerida", type="primary", use_container_width=True)

    if submitted:
        profile = {
            "name": name, "age": age, "neighborhood": neighborhood, "education": education,
            "employment_status": employment_status, "availability_slots": availability,
            "last_occupation": last_occupation, "years_experience": years_experience,
            "months_out": months_out, "first_job": first_job, "career_change": career_change,
            "personal_income": personal_income, "household_income": household_income,
            "income_urgency": income_urgency, "digital_access": digital_access,
            "digital_autonomy": digital_autonomy, "commute_minutes": commute_minutes,
            "transport_barrier": transport_barrier, "care_responsibility": care_responsibility,
            "schedule_restriction": schedule_restriction, "self_declared_skills": self_declared_skills,
            "main_goal": main_goal, "desired_area": desired_area, "consent": consent,
            "baseline_timestamp": now_iso(),
        }
        st.session_state.candidate_profiles[pid] = profile
        diagnosis = diagnose_candidate(profile, demand_skill_ids)
        st.session_state.qualifica_recommendations[pid] = diagnosis
        add_trajectory_event(pid, "candidate_diagnosis", f"Diagnóstico preenchido; jornada sugerida: {diagnosis['initial_journey']}", "Participante + NEXO")
        st.success("Diagnóstico registrado. A recomendação abaixo é explicável e depende de validação humana.")

    profile = st.session_state.candidate_profiles.get(pid)
    diagnosis = st.session_state.qualifica_recommendations.get(pid)
    if not profile or not diagnosis:
        st.warning("Preencha o formulário e clique em **Gerar diagnóstico e jornada sugerida** para produzir a análise. Nenhuma característica é atribuída automaticamente antes do preenchimento.")
        disclaimer()
        return

    st.markdown("---")
    st.markdown("### 6. Diagnóstico NEXO")
    c1, c2 = st.columns([1, 1.15])
    with c1:
        st.markdown("#### Perfil de participação")
        dim_df = pd.DataFrame(diagnosis["dimensions"], columns=["dimensão", "leitura"])
        st.dataframe(dim_df, use_container_width=True, hide_index=True)

        st.markdown("#### Barreiras concretas identificadas")
        if diagnosis["barriers"]:
            for item in diagnosis["barriers"]:
                st.markdown(f'<span class="chip chip-warn">{item}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="chip chip-good">Nenhuma barreira crítica registrada</span>', unsafe_allow_html=True)

        st.markdown("#### Linha de base para outcomes")
        b1, b2 = st.columns(2)
        b1.metric("Situação de trabalho", profile["employment_status"])
        b2.metric("Renda individual", profile["personal_income"])
        st.caption("Essa linha de base permitirá acompanhar posteriormente contratação, permanência, renda, transição ocupacional e progressão.")

    with c2:
        st.markdown("#### Evidências de competências frente à demanda")
        comp_df = pd.DataFrame(diagnosis["evidence_rows"])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        with st.expander("Competências inferidas da experiência anterior"):
            if diagnosis["inferred_skills"]:
                for s in diagnosis["inferred_skills"]:
                    st.write(f"• {s}")
                st.caption("Inferência baseada na ocupação declarada e no referencial CBO/QBQ; precisa de validação posterior.")
            else:
                st.write("Nenhuma competência foi inferida da ocupação anterior.")

    st.markdown("### 7. Jornada sugerida")
    j1, j2 = st.columns([1.15, .85])
    with j1:
        st.markdown(
            f'<div class="decision"><b>Jornada inicial sugerida</b><br><br><span style="font-size:1.35rem;font-weight:700">{diagnosis["initial_journey"]}</span>'
            f'<br><br>{diagnosis["rationale"]}<br><br><b>Próxima passagem potencial:</b> {diagnosis["next_journey"]}</div>',
            unsafe_allow_html=True,
        )
    with j2:
        st.markdown('<div class="card"><h4>Matriz de Passagem</h4><p>A recomendação não fixa a pessoa em uma categoria. O percurso pode avançar, ser reorganizado ou retornar a uma etapa mais protetiva conforme novas evidências.</p></div>', unsafe_allow_html=True)

    st.markdown("#### Decisão humana compartilhada")
    a, b, c = st.columns(3)
    if a.button("✓ Validar trajetória", type="primary", use_container_width=True):
        st.session_state.manager_decision = "Validada"
        add_trajectory_event(pid, "pathway_accepted", f"Trajetória validada: {diagnosis['initial_journey']}", "Gestor / equipe técnica")
        st.success("Trajetória validada e registrada no Evidence Ledger.")
    if b.button("↔ Ajustar trajetória", use_container_width=True):
        st.session_state.manager_decision = "Ajuste solicitado"
        add_trajectory_event(pid, "pathway_changed", "Trajetória ajustada após revisão humana/compartilhada", "Gestor / equipe técnica")
        st.warning("Ajuste registrado. No piloto, o motivo deverá ser obrigatório e estruturado.")
    if c.button("✕ Não adotar recomendação", use_container_width=True):
        st.session_state.manager_decision = "Não adotada"
        add_trajectory_event(pid, "pathway_rejected", "Recomendação não adotada após revisão humana", "Gestor / equipe técnica")
        st.error("Decisão registrada para análise posterior da divergência humano-sistema.")

    st.markdown("### Como esse diagnóstico alimenta a gestão pública")
    g1, g2, g3, g4 = st.columns(4)
    g1.markdown('<div class="card"><h4>Oferta</h4><p>Agrega gaps recorrentes para orientar quais qualificações ofertar.</p></div>', unsafe_allow_html=True)
    g2.markdown('<div class="card"><h4>Conteúdo</h4><p>Mostra quais competências e barreiras exigem ajuste de currículo e apoio.</p></div>', unsafe_allow_html=True)
    g3.markdown('<div class="card"><h4>Território</h4><p>Permite analisar residência, mobilidade, acesso digital e disponibilidade.</p></div>', unsafe_allow_html=True)
    g4.markdown('<div class="card"><h4>Efetividade</h4><p>Conecta linha de base a emprego, permanência, renda e progressão.</p></div>', unsafe_allow_html=True)

    if st.session_state.trajectory_events:
        with st.expander("Linha do tempo da trajetória"):
            df = pd.DataFrame(st.session_state.trajectory_events)
            st.dataframe(df[df.participant_id == pid], use_container_width=True, hide_index=True)
    disclaimer()


def page_learning():
    page_header(
        "PLANEJAMENTO DA OFERTA & ENGENHARIA EDUCACIONAL",
        "O que contratar, ampliar ou atualizar",
        "Cruza demanda produtiva, competências requeridas e diagnósticos agregados das jornadas para apoiar decisões de oferta e revisão curricular.",
    )

    st.info(
        "**Como ler esta tela:** mercado informa o que precisa → diagnósticos mostram o que a população atendida já possui e onde estão os gaps → "
        "o NEXO transforma esse cruzamento em prioridades de contratação, ampliação e atualização de matrizes formativas."
    )

    extracted = extract_skills(st.session_state.selected_demand_text)
    demand_skill_ids = required_skills_from_demand(extracted)
    demand_skill_names = [SKILLS[sid]["name"] for sid in demand_skill_ids if sid in SKILLS]
    matches = occupation_matches(st.session_state.selected_demand_text, top_n=3)
    top_occ = matches[0]["record"] if matches else {}
    occ_name = top_occ.get("occupation", "Demanda ocupacional em análise")
    cbo = top_occ.get("cbo", "—")
    quantity = int(st.session_state.get("demand_quantity", 0) or 0)
    horizon = st.session_state.get("demand_horizon", "—")
    company = st.session_state.get("demand_company", "Origem não registrada")

    # Diagnósticos preenchidos nesta sessão constituem a camada de oferta humana.
    diagnoses = st.session_state.get("qualifica_recommendations", {})
    profiles = st.session_state.get("candidate_profiles", {})
    diag_items = [(pid, d) for pid, d in diagnoses.items() if pid in profiles]

    gap_counter = {}
    barrier_counter = {}
    journey_counter = {}
    alignments = []
    for pid, d in diag_items:
        alignments.append(float(d.get("alignment", 0)))
        journey = d.get("initial_journey", "Não classificada")
        journey_counter[journey] = journey_counter.get(journey, 0) + 1
        for b in d.get("barriers", []):
            barrier_counter[b] = barrier_counter.get(b, 0) + 1
        for row in d.get("evidence_rows", []):
            if row.get("situação", "").startswith("Gap"):
                skill = row.get("competência demandada", "Competência não identificada")
                gap_counter[skill] = gap_counter.get(skill, 0) + 1

    n_profiles = len(diag_items)
    potential_candidates = sum(1 for _, d in diag_items if float(d.get("alignment", 0)) >= .34)
    mean_alignment = sum(alignments) / len(alignments) if alignments else 0

    st.markdown("### 1. Panorama da demanda produtiva")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Demanda sinalizada", quantity)
    m2.metric("Ocupação de referência", occ_name[:28] + ("…" if len(occ_name) > 28 else ""))
    m3.metric("CBO", cbo)
    m4.metric("Horizonte", horizon)
    st.caption(f"Origem: **{company}**. As competências abaixo derivam da demanda analisada e dos referenciais CBO/QBQ, após validação humana.")
    if demand_skill_names:
        st.markdown("**Competências mais relevantes para a demanda atual**")
        for s in demand_skill_names[:10]:
            st.markdown(f'<span class="chip">{s}</span>', unsafe_allow_html=True)
    else:
        st.warning("Ainda não há competências operacionais associadas à demanda. Valide a demanda na página Demanda & Competências.")

    st.markdown("### 2. O que os diagnósticos individuais revelam em conjunto")
    a, b, c, d = st.columns(4)
    a.metric("Diagnósticos agregados", n_profiles)
    b.metric("Potencialmente aderentes", potential_candidates)
    c.metric("Aderência média à demanda", f"{mean_alignment:.0%}" if n_profiles else "—")
    d.metric("Gaps distintos observados", len(gap_counter))

    if n_profiles:
        left, right = st.columns(2)
        with left:
            st.markdown("#### Gaps de competências mais recorrentes")
            gap_df = pd.DataFrame(
                sorted(gap_counter.items(), key=lambda x: x[1], reverse=True),
                columns=["competência", "pessoas com gap"],
            )
            if gap_df.empty:
                st.success("Nenhum gap recorrente identificado entre os diagnósticos preenchidos.")
            else:
                gap_df["% dos diagnósticos"] = (gap_df["pessoas com gap"] / n_profiles * 100).round(0).astype(int).astype(str) + "%"
                st.dataframe(gap_df.head(10), use_container_width=True, hide_index=True)
        with right:
            st.markdown("#### Barreiras que afetam desenho e permanência")
            bar_df = pd.DataFrame(
                sorted(barrier_counter.items(), key=lambda x: x[1], reverse=True),
                columns=["barreira", "ocorrências"],
            )
            if bar_df.empty:
                st.info("Nenhuma barreira recorrente registrada nos diagnósticos atuais.")
            else:
                bar_df["% dos diagnósticos"] = (bar_df["ocorrências"] / n_profiles * 100).round(0).astype(int).astype(str) + "%"
                st.dataframe(bar_df.head(8), use_container_width=True, hide_index=True)

        st.markdown("#### Distribuição das jornadas Qualifica+")
        journey_df = pd.DataFrame(
            sorted(journey_counter.items(), key=lambda x: x[1], reverse=True),
            columns=["jornada", "participantes"],
        )
        journey_df["%"] = (journey_df["participantes"] / n_profiles * 100).round(0).astype(int).astype(str) + "%"
        st.dataframe(journey_df, use_container_width=True, hide_index=True)
    else:
        st.warning(
            "Ainda não há diagnósticos preenchidos nesta sessão. Preencha ao menos um perfil em **Diagnóstico & Trajetória** para que o NEXO passe a cruzar demanda produtiva e características da população atendida."
        )

    st.markdown("### 3. Prioridades de oferta formativa")
    cnct = suggest_cnct_courses(st.session_state.selected_demand_text)
    suggested_course = cnct[0] if cnct else f"Trilha de qualificação — {occ_name}"
    top_gaps = [x[0] for x in sorted(gap_counter.items(), key=lambda x: x[1], reverse=True)[:4]] or demand_skill_names[:4]
    digital_need = any("digital" in normalize_text(k) for k in barrier_counter.keys())
    care_or_schedule = any(any(term in normalize_text(k) for term in ["cuidado", "horario", "deslocamento", "transporte"]) for k in barrier_counter.keys())

    if quantity >= 30 and (not n_profiles or potential_candidates >= max(1, n_profiles // 3)):
        current_action = "Contratar / abrir turma piloto"
        priority = "Alta"
    elif quantity >= 10:
        current_action = "Estruturar oferta focalizada"
        priority = "Média"
    else:
        current_action = "Monitorar demanda antes de abrir turma"
        priority = "Exploratória"

    portfolio = pd.DataFrame([
        {
            "ocupação / família": occ_name,
            "demanda sinalizada": quantity,
            "pessoas diagnosticadas": n_profiles,
            "potencialmente aderentes": potential_candidates,
            "gaps prioritários": ", ".join(top_gaps[:3]) if top_gaps else "A validar",
            "ação recomendada": current_action,
            "prioridade": priority,
        },
        {
            "ocupação / família": "Operações logísticas (exemplo demonstrativo)",
            "demanda sinalizada": 120,
            "pessoas diagnosticadas": 86,
            "potencialmente aderentes": 64,
            "gaps prioritários": "ERP; gestão de estoque; expedição",
            "ação recomendada": "Contratar trilha de 40–60h",
            "prioridade": "Alta",
        },
        {
            "ocupação / família": "Eletricidade industrial (exemplo demonstrativo)",
            "demanda sinalizada": 40,
            "pessoas diagnosticadas": 24,
            "potencialmente aderentes": 18,
            "gaps prioritários": "Leitura técnica; segurança; prática aplicada",
            "ação recomendada": "Ampliar oferta técnica / validar certificações",
            "prioridade": "Média",
        },
    ])
    st.dataframe(portfolio, use_container_width=True, hide_index=True)
    st.caption("A primeira linha responde à demanda atualmente analisada. As linhas adicionais são demonstrativas para evidenciar como o módulo consolida um portfólio de decisões quando múltiplos sinais forem integrados.")

    st.markdown("### 4. Engenharia educacional: o que a matriz precisa conter ou revisar")
    curriculum_rows = []
    for skill in (top_gaps or demand_skill_names[:6]):
        curriculum_rows.append({
            "competência / conteúdo": skill,
            "pressão da demanda": "Alta" if skill in top_gaps[:3] else "Média",
            "gap na população": "Alto" if skill in top_gaps[:3] and n_profiles else "A validar",
            "decisão curricular": "Adicionar ou ampliar prática aplicada" if skill in top_gaps[:3] else "Manter e monitorar",
        })
    if digital_need:
        curriculum_rows.append({
            "competência / conteúdo": "Inclusão e autonomia digital",
            "pressão da demanda": "Transversal",
            "gap na população": "Recorrente",
            "decisão curricular": "Inserir módulo de base / apoio digital antes ou junto da trilha técnica",
        })
    if care_or_schedule:
        curriculum_rows.append({
            "competência / conteúdo": "Desenho de participação e permanência",
            "pressão da demanda": "—",
            "gap na população": "Barreira operacional",
            "decisão curricular": "Rever horários, formato, tutoria e estratégias de permanência",
        })
    curriculum_df = pd.DataFrame(curriculum_rows)
    if curriculum_df.empty:
        st.info("Valide competências e preencha diagnósticos para gerar recomendações de matriz formativa.")
    else:
        st.dataframe(curriculum_df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="card"><h4>Oferta sugerida</h4><p><b>{suggested_course}</b></p>'
            f'<p>Ação: {current_action}</p><p>Competências críticas: {", ".join(top_gaps[:4]) if top_gaps else "a validar"}.</p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        journey_note = ", ".join([f"{k}: {v}" for k, v in sorted(journey_counter.items(), key=lambda x: x[1], reverse=True)]) if journey_counter else "sem diagnósticos agregados"
        st.markdown(
            f'<div class="card"><h4>Desenho pedagógico por perfil agregado</h4><p>{journey_note}</p>'
            f'<p>O desenho da oferta deve variar em intensidade de apoio, inclusão digital, prática, tutoria e acompanhamento conforme as jornadas predominantes — sem criar um curso artesanal por pessoa.</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 5. Como outcomes atualizam a oferta")
    st.markdown(
        '<div class="decision"><b>Learning-to-Outcome loop</b><br><br>'
        'Demanda do mercado → matriz formativa → formação → aprendizagem → contratação/permanência/renda → feedback empresarial e do participante → revisão de conteúdo, metodologia ou decisão de escala.'
        '<br><br><b>Uso gerencial:</b> cursos com boa conclusão mas baixa contratação exigem revisão de aderência; cursos com contratação mas baixa permanência exigem revisão de competências, preparação funcional ou acompanhamento.</div>',
        unsafe_allow_html=True,
    )

    if st.button("Registrar recomendação de oferta", type="primary"):
        add_evidence(
            "training_portfolio_recommendation",
            "Gestor Público",
            f"Oferta recomendada: {suggested_course}; ação: {current_action}; prioridade: {priority}",
            source="NEXO — Planejamento da Oferta",
        )
        st.success("Recomendação de oferta registrada no Evidence Ledger.")

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
st.sidebar.caption("CPSI MVP v1.5 — oferta + diagnóstico + CBO/QBQ")
st.sidebar.markdown("---")

pages = [
    "Visão Geral",
    "Demanda & Competências",
    "Diagnóstico & Trajetória",
    "Planejamento & Engenharia",
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
elif page == "Diagnóstico & Trajetória":
    page_trajectory()
elif page == "Planejamento & Engenharia":
    page_learning()
elif page == "Experimentos & Outcomes":
    page_experiments()
