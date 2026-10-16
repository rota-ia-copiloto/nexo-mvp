"""NEXO Qualifica+ | Radar Executivo de Vagas v2.

Módulo independente: a aplicação existente continua chamando render_radar_vagas().
Todas as vagas desta versão são sintéticas. Não realiza raspagem do portal.
"""

from __future__ import annotations

from collections import Counter
from collections import defaultdict
import calendar
import random
from datetime import datetime, timedelta
from html import escape
from html.parser import HTMLParser
import re
import unicodedata

import pandas as pd
import streamlit as st

PORTAL_URL = "https://empregos.itajai.sc.gov.br/buscar-vagas/controller/externo"

# DADOS EXCLUSIVAMENTE SINTÉTICOS (não correspondem a vagas publicadas).
DEMO_VAGAS = [
    dict(codigo="DEMO-001", titulo="Operador(a) de Empilhadeira", setor="Logística", quantidade=3,
         salario=2850, bairro="Cordeiros", data="15/10/2026", escolaridade="Ensino médio",
         descricao="Operar empilhadeira, movimentar mercadorias e organizar estoque com atenção à segurança operacional."),
    dict(codigo="DEMO-002", titulo="Auxiliar de Logística", setor="Logística", quantidade=4,
         salario=2250, bairro="Itaipava", data="15/10/2026", escolaridade="Ensino médio",
         descricao="Atuar com recebimento, conferência, separação e expedição de materiais, controle de estoque e planilhas."),
    dict(codigo="DEMO-003", titulo="Técnico(a) de Manutenção Industrial", setor="Indústria", quantidade=2,
         salario=3650, bairro="Salseiros", data="14/10/2026", escolaridade="Ensino técnico",
         descricao="Executar manutenção preventiva, diagnóstico de falhas, leitura de diagramas e manutenção elétrica e mecânica."),
    dict(codigo="DEMO-004", titulo="Assistente Administrativo(a)", setor="Serviços", quantidade=2,
         salario=2400, bairro="Centro", data="14/10/2026", escolaridade="Ensino médio",
         descricao="Organizar documentos, atualizar planilhas, prestar atendimento e usar sistemas de gestão administrativa."),
    dict(codigo="DEMO-005", titulo="Auxiliar de Produção", setor="Indústria", quantidade=5,
         salario=2200, bairro="Espinheiros", data="13/10/2026", escolaridade="Ensino fundamental",
         descricao="Apoiar linha de produção, inspecionar qualidade, organizar materiais e aplicar normas de segurança."),
    dict(codigo="DEMO-006", titulo="Atendente Comercial", setor="Comércio", quantidade=3,
         salario=None, bairro="Fazenda", data="13/10/2026", escolaridade="Ensino médio",
         descricao="Atendimento ao cliente, comunicação, vendas e registro das informações em sistema."),
    dict(codigo="DEMO-007", titulo="Eletricista Industrial", setor="Indústria", quantidade=2,
         salario=3900, bairro="São Vicente", data="12/10/2026", escolaridade="Ensino técnico",
         descricao="Instalação elétrica industrial, leitura de diagramas, manutenção preventiva e segurança do trabalho."),
    dict(codigo="DEMO-008", titulo="Assistente de Recursos Humanos", setor="Serviços", quantidade=1,
         salario=2800, bairro="Centro", data="12/10/2026", escolaridade="Ensino superior cursando",
         descricao="Apoiar recrutamento, organizar documentos, utilizar planilhas e realizar comunicação com candidatos."),
    dict(codigo="DEMO-009", titulo="Analista de Dados Júnior", setor="Tecnologia", quantidade=1,
         salario=3400, bairro="Centro", data="16/10/2026", escolaridade="Ensino superior",
         descricao="Criar relatórios em SQL, dashboards em Power BI e análises com planilhas, garantindo qualidade dos dados."),
    dict(codigo="DEMO-010", titulo="Auxiliar de Cozinha", setor="Serviços", quantidade=2,
         salario=2050, bairro="Fazenda", data="16/10/2026", escolaridade="Ensino fundamental",
         descricao="Preparação de alimentos, organização da cozinha, atendimento e boas práticas de higiene."),
    dict(codigo="DEMO-011", titulo="Conferente de Cargas", setor="Logística", quantidade=2,
         salario=2600, bairro="Itaipava", data="16/10/2026", escolaridade="Ensino médio",
         descricao="Conferência de cargas e documentos, inventário de estoque e uso de sistema de gestão."),
    dict(codigo="DEMO-012", titulo="Técnico(a) em Segurança do Trabalho", setor="Indústria", quantidade=1,
         salario=None, bairro="Cordeiros", data="16/10/2026", escolaridade="Ensino técnico",
         descricao="Aplicar normas de segurança, inspeção de riscos, orientar equipe e organizar documentação técnica."),
]

# Regras transparentes de demonstração. Não equivalem à taxonomia completa CBO/QBQ.
TERMOS_SKILLS = {
    "Gestão de estoques": ["estoque", "inventario", "armazen"],
    "Segurança do trabalho": ["seguranca", "riscos", "epi"],
    "Operação de equipamentos": ["empilhadeira", "equipamento", "maquina"],
    "Conferência de materiais": ["conferencia", "conferente", "recebimento"],
    "Expedição e logística": ["expedicao", "logistica", "cargas", "mercadorias"],
    "Leitura técnica": ["diagramas", "leitura tecnica", "procedimentos"],
    "Manutenção industrial": ["manutencao", "falhas", "mecanica"],
    "Elétrica industrial": ["eletrica", "eletricista"],
    "Pacote Office / planilhas": ["planilhas", "excel"],
    "Sistemas de gestão": ["sistema", "erp"],
    "Atendimento ao cliente": ["atendimento", "cliente", "atendente"],
    "Comunicação profissional": ["comunicacao", "comunicar"],
    "Processos produtivos": ["producao", "linha de producao"],
    "Controle de qualidade": ["qualidade", "inspecionar"],
    "Vendas": ["vendas", "comercial"],
    "Recrutamento e seleção": ["recrutamento", "candidatos"],
    "Análise de dados": ["dados", "analises", "relatorios"],
    "SQL": ["sql"],
    "Visualização de dados": ["power bi", "dashboards"],
    "Boas práticas de higiene": ["higiene", "alimentos"],
}


def _sem_acento(txt: str) -> str:
    return unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode("ascii").lower()


def _fixture_html(vagas: list[dict]) -> str:
    """Imita uma listagem HTML genérica, sem reproduzir a estrutura do portal real."""
    cards = []
    for v in vagas:
        campos = "".join(
            f'<div data-field="{escape(k)}">{escape(str(v[k]) if v[k] is not None else "")}</div>'
            for k in ("codigo", "titulo", "setor", "quantidade", "salario", "bairro", "data", "escolaridade", "descricao")
        )
        cards.append(f'<article class="vaga-card">{campos}</article>')
    return "<main>\n" + "\n".join(cards) + "\n</main>"


class _VagaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.item = None
        self.field = None
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and "vaga-card" in a.get("class", "").split():
            self.item = {}
        elif self.item is not None and a.get("data-field"):
            self.field = a["data-field"]
            self.buffer = []

    def handle_data(self, data):
        if self.field is not None:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "div" and self.field is not None and self.item is not None:
            self.item[self.field] = "".join(self.buffer).strip()
            self.field = None
            self.buffer = []
        if tag == "article" and self.item is not None:
            self.rows.append(self.item)
            self.item = None


def _extrair_skills(titulo: str, descricao: str) -> tuple[list[str], list[dict]]:
    corpus = _sem_acento(titulo + " " + descricao)
    result, evidence = [], []
    for skill, terms in TERMOS_SKILLS.items():
        encontradas = [termo for termo in terms if _sem_acento(termo) in corpus]
        if encontradas:
            result.append(skill)
            evidence.append({"competencia": skill, "gatilho_textual": ", ".join(encontradas), "metodo": "Regra lexical demonstrativa"})
    return result, evidence


def _pipeline(fonte_html: str) -> tuple[pd.DataFrame, dict[str, list[dict]]]:
    parser = _VagaParser()
    parser.feed(fonte_html)
    unique = {}
    evidencias = {}
    for r in parser.rows:
        codigo = r.get("codigo", "")
        if not codigo:
            continue
        skills, details = _extrair_skills(r.get("titulo", ""), r.get("descricao", ""))
        evidencias[codigo] = details
        try:
            salario = float(r["salario"]) if r.get("salario") else None
        except ValueError:
            salario = None
        unique[codigo] = {
            "ID de origem": codigo,
            "Ocupação": r.get("titulo", ""),
            "Setor": r.get("setor", "Não informado"),
            "Postos": int(r.get("quantidade", 0) or 0),
            "Salário (R$)": salario,
            "Bairro": r.get("bairro", ""),
            "Atualização": r.get("data", ""),
            "Escolaridade": r.get("escolaridade", ""),
            "Descrição original": r.get("descricao", ""),
            "Competências sugeridas": skills,
            "Nº competências": len(skills),
            "CBO": "A validar",
            "Fonte": "HTML simulado / estrutura ilustrativa",
        }
    return pd.DataFrame(unique.values()), evidencias



# --------------------------------------------------------------------------
# DADOS HISTÓRICOS DEMONSTRATIVOS
# --------------------------------------------------------------------------
# Série sintética reproduzível que viabiliza testar filtros e tendências.
# Em produção, substituir APENAS esta fonte pelo conector governado (API/ETL).
DATA_REFERENCIA = datetime(2026, 10, 16)
JANELAS = {"30 dias": 30, "90 dias": 90, "6 meses": 183, "12 meses": 365}

REQUISITOS_POR_OCUPACAO = {
    "Operador(a) de Empilhadeira": ["Experiência anterior", "Curso de operação de empilhadeira"],
    "Auxiliar de Logística": ["Experiência anterior", "Informática básica"],
    "Técnico(a) de Manutenção Industrial": ["Formação técnica", "Experiência anterior"],
    "Assistente Administrativo(a)": ["Informática básica", "Experiência anterior"],
    "Auxiliar de Produção": ["Disponibilidade de turnos"],
    "Atendente Comercial": ["Experiência anterior", "Informática básica"],
    "Eletricista Industrial": ["Formação técnica", "Experiência anterior", "NR-10"],
    "Assistente de Recursos Humanos": ["Informática básica", "Formação em andamento"],
    "Analista de Dados Júnior": ["Formação superior", "Conhecimento em SQL"],
    "Auxiliar de Cozinha": ["Boas práticas de higiene"],
    "Conferente de Cargas": ["Experiência anterior", "Informática básica"],
    "Técnico(a) em Segurança do Trabalho": ["Formação técnica", "Registro profissional"],
    "Operador(a) de Caixa": ["Informática básica", "Disponibilidade de turnos"],
    "Vendedor(a) Interno(a)": ["Experiência anterior", "Informática básica"],
    "Mecânico(a) de Manutenção": ["Formação técnica", "Experiência anterior"],
    "Soldador(a)": ["Qualificação em soldagem", "Experiência anterior"],
    "Técnico(a) de Suporte de TI": ["Formação técnica", "Atendimento ao usuário"],
}

CATALOGO_EXTRA = [
    dict(titulo="Operador(a) de Caixa", setor="Comércio", quantidade=2, salario=2150,
         bairro="Centro", escolaridade="Ensino médio", descricao="Atendimento ao cliente, operação de sistema, controle de caixa e comunicação profissional."),
    dict(titulo="Vendedor(a) Interno(a)", setor="Comércio", quantidade=3, salario=2750,
         bairro="Fazenda", escolaridade="Ensino médio", descricao="Prospecção, vendas, relacionamento com cliente e registro em sistema de gestão."),
    dict(titulo="Mecânico(a) de Manutenção", setor="Indústria", quantidade=2, salario=3850,
         bairro="São Vicente", escolaridade="Ensino técnico", descricao="Manutenção mecânica preventiva, diagnóstico de falhas, segurança e leitura de diagramas."),
    dict(titulo="Soldador(a)", setor="Indústria", quantidade=2, salario=3600,
         bairro="Cordeiros", escolaridade="Ensino médio", descricao="Operação de equipamentos, leitura técnica, inspeção de qualidade e normas de segurança."),
    dict(titulo="Técnico(a) de Suporte de TI", setor="Tecnologia", quantidade=1, salario=3200,
         bairro="Centro", escolaridade="Ensino técnico", descricao="Atendimento ao usuário, manutenção de equipamentos e sistema de gestão."),
]


def _historico_sintetico() -> pd.DataFrame:
    rng = random.Random(4216)
    catalogo = DEMO_VAGAS + CATALOGO_EXTRA
    registros = []
    # 24 meses prévios + vagas-base no mês de referência; série não é histórico real.
    for deslocamento in range(24, 0, -1):
        anomes = DATA_REFERENCIA.year * 12 + DATA_REFERENCIA.month - 1 - deslocamento
        ano, mes0 = divmod(anomes, 12)
        mes = mes0 + 1
        total_no_mes = rng.randint(9, 16)
        for indice in range(total_no_mes):
            original = dict(rng.choice(catalogo))
            dia = rng.randint(1, calendar.monthrange(ano, mes)[1])
            original.update({
                "codigo": f"SIM-{ano}{mes:02d}-{indice+1:03d}",
                "data": f"{dia:02d}/{mes:02d}/{ano}",
                "quantidade": max(1, int(original["quantidade"]) + rng.choice([-1, 0, 0, 0, 1, 2])),
            })
            registros.append(original)
    registros.extend(dict(v) for v in DEMO_VAGAS)
    df, _ = _pipeline(_fixture_html(registros))
    df["Data"] = pd.to_datetime(df["Atualização"], format="%d/%m/%Y", errors="coerce")
    df["Requisitos sinalizados"] = df["Ocupação"].map(lambda x: REQUISITOS_POR_OCUPACAO.get(x, []))
    df["Experiência solicitada"] = df["Requisitos sinalizados"].map(lambda x: "Experiência anterior" in x)
    return df.sort_values("Data", ascending=False).reset_index(drop=True)


def _periodo(df: pd.DataFrame, dias: int, setor: str = "Todos", termo: str = "") -> pd.DataFrame:
    inicio = DATA_REFERENCIA - timedelta(days=dias)
    out = df[(df["Data"] > inicio) & (df["Data"] <= DATA_REFERENCIA)].copy()
    if setor != "Todos":
        out = out[out["Setor"] == setor]
    termo = _sem_acento(termo.strip())
    if termo:
        out = out[out.apply(lambda r: termo in _sem_acento(" ".join([
            str(r["Ocupação"]), str(r["Descrição original"]), str(r["Setor"]),
            " ".join(r["Competências sugeridas"]), " ".join(r["Requisitos sinalizados"]),
        ])), axis=1)]
    return out


def _freq_lista(df: pd.DataFrame, coluna: str) -> Counter:
    contagem = Counter()
    for lista in df[coluna]:
        contagem.update(set(lista))  # Frequência em anúncios distintos, não em pessoas ou postos.
    return contagem


def _fmt_int(v: int) -> str:
    return f"{int(v):,}".replace(",", ".")


def _html_text(v: object) -> str:
    return escape(str(v or ""))


def _metric(label: str, val: str, detail: str, icon: str) -> None:
    st.markdown(f"""
    <div class="nv2-metric">
      <div class="nv2-metric-head"><span>{_html_text(label)}</span><span class="nv2-metric-icon">{_html_text(icon)}</span></div>
      <div class="nv2-metric-value{' nv2-metric-long' if len(val) > 18 else ''}">{_html_text(val)}</div>
      <div class="nv2-metric-detail">{_html_text(detail)}</div>
    </div>
    """, unsafe_allow_html=True)


def _bars(items: list[tuple[str, int]], top: int = 7, unit: str = "anúncios") -> None:
    if not items:
        st.caption("Sem ocorrências para os filtros atuais.")
        return
    top_items = items[:top]
    vmax = max(v for _, v in top_items) or 1
    for name, count in top_items:
        width = 100 * count / vmax
        st.markdown(f"""
        <div class="nv2-rank">
          <div class="nv2-rank-label"><span title="{_html_text(name)}">{_html_text(name)}</span><b>{_fmt_int(count)}</b></div>
          <div class="nv2-track"><div class="nv2-fill" style="width:{width:.1f}%"></div></div>
        </div>
        """, unsafe_allow_html=True)
    if unit == "anúncios":
        st.caption("Frequência por anúncio; um anúncio pode citar várias competências.")
    else:
        st.caption(f"Contagem de {unit} no período selecionado.")


def _section(title: str, eyebrow: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="nv2-section-title">
       <div class="nv2-section-eyebrow">{_html_text(eyebrow)}</div>
       <h3>{_html_text(title)}</h3>
       {f'<p>{_html_text(subtitle)}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


ESTRATEGIAS = {
    "Logística": ("Logística e operações", "Revisar conteúdos de estoque, expedição e operação segura de equipamentos."),
    "Indústria": ("Manutenção e processos industriais", "Examinar aderência das trilhas técnicas às competências operacionais recorrentes."),
    "Comércio": ("Comércio e atendimento", "Avaliar componentes de atendimento, comunicação e ferramentas digitais."),
    "Serviços": ("Administração e serviços", "Observar requisitos digitais e práticas administrativas na oferta existente."),
    "Tecnologia": ("Competências digitais", "Analisar aderência de percursos de dados, sistemas e suporte técnico."),
}


def _css():
    st.markdown("""
    <style>
      .nv2-hero {padding:27px 30px 26px;border-radius:19px;color:#fff;
        background:radial-gradient(circle at 87% 20%,rgba(73,149,213,.24),transparent 36%),
          linear-gradient(116deg,#071B3A 0%,#102F56 55%,#174B70 100%); margin-bottom:12px;
        box-shadow:0 10px 25px rgba(7,27,58,.08)}
      .nv2-hero .nv2-eyebrow {color:#B3D7F6;letter-spacing:.14em;font-weight:800;font-size:11px}
      .nv2-hero h2 {color:#fff!important;font-weight:760;font-size:2.0rem;margin:9px 0 5px!important;line-height:1.2}
      .nv2-hero p {color:#DCECF8!important;font-size:14px;margin:0!important;max-width:720px}
      .nv2-context {display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:10px 0 16px;
        color:#66788D;font-size:12px}
      .nv2-dot {width:7px;height:7px;background:#E5B652;display:inline-block;border-radius:50%;margin-right:4px}
      .nv2-filter-label {font-size:12px;color:#46566B;font-weight:700}
      .nv2-metric {padding:18px 20px 16px;background:#fff;border:1px solid #E4EAF1;
        border-radius:14px; min-height:132px;box-shadow:0 4px 14px rgba(7,27,58,.038);}
      .nv2-metric-head {display:flex;align-items:center;justify-content:space-between;gap:8px;
        color:#6C798C;font-size:12px;font-weight:650}
      .nv2-metric-icon {background:#F0F5FD;border-radius:8px;padding:5px 7px;color:#2E6497;font-size:13px}
      .nv2-metric-value {font-size:30px;line-height:1.25;font-weight:760;color:#102949;
        margin:8px 0 3px;letter-spacing:-.025em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .nv2-metric-long {font-size:21px;white-space:normal;line-height:1.25;min-height:36px}
      .nv2-metric-detail {font-size:12px;color:#738298}
      .nv2-section-title {margin:26px 0 12px}
      .nv2-section-eyebrow {letter-spacing:.13em;color:#3869A1;font-size:10px;font-weight:800;text-transform:uppercase}
      .nv2-section-title h3 {font-size:1.35rem;color:#102949;margin:3px 0 4px!important;font-weight:750}
      .nv2-section-title p {color:#7C8797;font-size:13px;margin:0}
      .nv2-summary {border-left:3px solid #3D78C9;background:#F2F6FC;border-radius:0 12px 12px 0;
        padding:13px 17px;margin:16px 0 2px;color:#284563;font-size:14px;line-height:1.6}
      .nv2-summary b {color:#0E3059}
      .nv2-card-heading {font-size:14px;color:#193858;font-weight:750;margin:4px 0 12px}
      .nv2-rank {margin-bottom:12px}
      .nv2-rank-label {display:flex;align-items:center;justify-content:space-between;gap:10px;
        color:#44556B;font-size:12px;margin-bottom:5px}
      .nv2-rank-label span {overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .nv2-rank-label b {color:#1D446B;white-space:nowrap}
      .nv2-track {height:7px;border-radius:20px;background:#ECF1F7;overflow:hidden}
      .nv2-fill {height:100%;border-radius:20px;background:linear-gradient(90deg,#346CB7,#6BA1DE)}
      .nv2-insight {border:1px solid #E3EBF3;border-radius:14px;background:#FFFFFF;
        padding:17px 19px;min-height:175px;box-shadow:0 4px 14px rgba(7,27,58,.03)}
      .nv2-insight-k {font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#47739E;font-weight:800}
      .nv2-insight h4 {color:#153451!important;font-size:15px;margin:6px 0!important}
      .nv2-insight p {color:#64748B;font-size:12px;line-height:1.55;margin:9px 0}
      .nv2-insight-foot {border-top:1px solid #EEF2F7;padding-top:10px;color:#1F5990;font-size:12px;font-weight:650}
      .nv2-pill {display:inline-block;border-radius:999px;background:#EAF1FA;color:#28588E;
        font-size:11px;font-weight:700;padding:5px 9px;margin:4px 3px 5px 0}
      .nv2-tech {color:#708092;font-size:12px}
      @media(max-width:900px){.nv2-hero{padding:20px 18px}.nv2-hero h2{font-size:1.6rem}
        .nv2-metric{min-height:115px}.nv2-metric-value{font-size:24px}}
    </style>
    """, unsafe_allow_html=True)


def render_radar_vagas() -> None:
    """Renderiza o painel executivo sem alterar o app.py já integrado."""
    _css()
    st.markdown("""
    <div class="nv2-hero">
       <div class="nv2-eyebrow">NEXO QUALIFICA+ &nbsp; / &nbsp; INTELIGÊNCIA DE MERCADO</div>
       <h2>Radar de Vagas | Itajaí</h2>
       <p>O que o mercado procura — e o que isso sinaliza para o planejamento da qualificação.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="nv2-context">
      <span><span class="nv2-dot"></span> <b>Dados ilustrativos</b> · série histórica sintética</span>
      <span>Fonte futura: Portal de Empregos de Itajaí</span>
      <span>Referência da simulação: 16/10/2026</span>
    </div>
    """, unsafe_allow_html=True)

    base = _historico_sintetico()
    periodos = list(JANELAS)
    c1, c2, c3 = st.columns([1, 1, 1.65], gap="medium")
    with c1:
        periodo = st.selectbox("Período analisado", periodos, index=3, key="nv2_periodo")
    with c2:
        setor = st.selectbox("Setor econômico", ["Todos"] + sorted(base["Setor"].unique().tolist()), key="nv2_setor")
    with c3:
        texto = st.text_input("Buscar ocupação ou competência", placeholder="Ex.: manutenção, logística, Office...", key="nv2_busca")

    dias = JANELAS[periodo]
    df = _periodo(base, dias, setor, texto)
    if df.empty:
        st.warning("Não há anúncios demonstrativos no período e filtros selecionados. Experimente ampliar o período ou limpar a busca.")
        return

    postos = int(df["Postos"].sum())
    anuncios = len(df)
    sector_freq = df.groupby("Setor")["Postos"].sum().sort_values(ascending=False)
    occ_freq = df.groupby("Ocupação")["Postos"].sum().sort_values(ascending=False)
    skills = _freq_lista(df, "Competências sugeridas")
    requisitos = _freq_lista(df, "Requisitos sinalizados")

    _section("Visão executiva", "01 / Panorama", "Uma leitura imediata da demanda registrada no período selecionado.")
    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        _metric("Postos anunciados", _fmt_int(postos), f"Em {anuncios} anúncios de vagas", "↗")
    with k2:
        _metric("Anúncios cadastrados", _fmt_int(anuncios), "Registros distintos no período", "▤")
    with k3:
        lider = str(sector_freq.index[0])
        _metric("Setor em destaque", lider, f"{_fmt_int(sector_freq.iloc[0])} postos anunciados", "◈")
    with k4:
        nome_skill, qtd_skill = skills.most_common(1)[0] if skills else ("Não identificado", 0)
        _metric("Competência recorrente", nome_skill, f"Presente em {qtd_skill} anúncios", "✦")

    destaque_ocupacao = str(occ_freq.index[0])
    st.markdown(f"""
    <div class="nv2-summary"><b>Em síntese:</b> a maior demanda em postos está em
      <b>{_html_text(lider)}</b>. A ocupação mais recorrente é
      <b>{_html_text(destaque_ocupacao)}</b>, e a competência mais citada nas descrições é
      <b>{_html_text(nome_skill)}</b>. Esses sinais podem orientar a revisão da oferta formativa,
      após confronto com dados dos participantes e cursos existentes.</div>
    """, unsafe_allow_html=True)

    _section("Histórico e distribuição da demanda", "02 / Mercado", "Evolução dos postos anunciados e concentração por setor e ocupação.")
    h1, h2 = st.columns([1.6, 1], gap="large")
    with h1:
        st.markdown('<div class="nv2-card-heading">Evolução dos postos anunciados</div>', unsafe_allow_html=True)
        frequencia = "W-MON" if dias <= 90 else "MS"
        tmp = df[["Data", "Postos"]].copy().set_index("Data").sort_index()
        grupos = tmp.resample(frequencia)["Postos"].sum()
        if frequencia == "MS":
            grupos.index = [f"{calendar.month_abbr[d.month]}/{str(d.year)[-2:]}" for d in grupos.index]
        else:
            grupos.index = [d.strftime("%d/%m") for d in grupos.index]
        st.bar_chart(grupos, use_container_width=True, height=270, color="#3A73C2")
        st.caption("Total de postos por mês (ou semana em períodos curtos). Não representa contratações realizadas.")
    with h2:
        st.markdown('<div class="nv2-card-heading">Setores com maior demanda</div>', unsafe_allow_html=True)
        _bars([(str(k), int(v)) for k,v in sector_freq.items()], top=6, unit="postos anunciados")
        st.markdown('<div class="nv2-card-heading" style="margin-top:19px">Ocupações mais frequentes</div>', unsafe_allow_html=True)
        _bars([(str(k), int(v)) for k,v in occ_freq.items()], top=5, unit="postos anunciados")

    _section("Competências e requisitos", "03 / Perfil das vagas", "O que aparece com maior frequência nas descrições e exigências da amostra.")
    p1, p2 = st.columns(2, gap="large")
    with p1:
        st.markdown('<div class="nv2-card-heading">Competências sinalizadas</div>', unsafe_allow_html=True)
        _bars(skills.most_common(8), top=8, unit="anúncios")
    with p2:
        st.markdown('<div class="nv2-card-heading">Requisitos mais recorrentes</div>', unsafe_allow_html=True)
        _bars(requisitos.most_common(6), top=6, unit="anúncios")
        escolar = df["Escolaridade"].value_counts().head(3)
        st.markdown('<div class="nv2-card-heading" style="margin-top:15px">Escolaridade mais citada</div>', unsafe_allow_html=True)
        st.markdown("".join(
            f'<span class="nv2-pill">{_html_text(k)} · {_fmt_int(v)}</span>' for k, v in escolar.items()
        ), unsafe_allow_html=True)
        experiencia = int(df["Experiência solicitada"].sum())
        st.caption(f"Experiência anterior sinalizada em {experiencia} de {anuncios} anúncios da amostra.")

    _section("Sinais para a qualificação", "04 / Apoio à decisão",
             "Pistas para analisar o portfólio de cursos; não são recomendações automáticas de contratação.")
    colunas = st.columns(min(3, len(sector_freq)), gap="medium")
    for col, (setor_nome, total) in zip(colunas, list(sector_freq.items())[:3]):
        base_setor = df[df["Setor"] == setor_nome]
        skill_top = _freq_lista(base_setor, "Competências sugeridas").most_common(1)
        topo = skill_top[0][0] if skill_top else "Não identificada"
        trilha, sugestao = ESTRATEGIAS.get(setor_nome, ("Oferta profissional", "Revisar aderência com os cursos existentes."))
        with col:
            st.markdown(f"""
            <div class="nv2-insight">
              <div class="nv2-insight-k">{_fmt_int(total)} postos · {_html_text(setor_nome)}</div>
              <h4>{_html_text(trilha)}</h4>
              <p><b>Competência recorrente:</b> {_html_text(topo)}</p>
              <div class="nv2-insight-foot">{_html_text(sugestao)}</div>
            </div>
            """, unsafe_allow_html=True)
    st.caption("Para identificar lacunas reais de qualificação, cruzar esses sinais com competências dos participantes, disponibilidade de cursos, conclusão e inserção laboral.")

    _section("Consulta às vagas registradas", "05 / Explorar", "Vagas agrupadas por ocupação ou consulta simplificada aos anúncios.")
    aba1, aba2 = st.tabs(["Ocupações consolidadas", "Anúncios cadastrados"])
    with aba1:
        resumo = df.groupby(["Ocupação", "Setor"], as_index=False).agg(
            Anúncios=("ID de origem", "nunique"), Postos=("Postos", "sum")
        ).sort_values(["Postos", "Anúncios"], ascending=False)
        st.dataframe(resumo, use_container_width=True, hide_index=True, height=340)
    with aba2:
        anuncios_view = df.copy()
        anuncios_view["Competências"] = anuncios_view["Competências sugeridas"].map(lambda xs: ", ".join(xs[:3]) if xs else "Não identificado")
        anuncios_view["Requisitos"] = anuncios_view["Requisitos sinalizados"].map(lambda xs: ", ".join(xs[:2]) if xs else "Não informado")
        anuncios_view["Data"] = anuncios_view["Data"].dt.strftime("%d/%m/%Y")
        cols = ["Ocupação", "Setor", "Postos", "Escolaridade", "Requisitos", "Competências", "Data"]
        st.dataframe(anuncios_view[cols], use_container_width=True, hide_index=True, height=340)
        registros = anuncios_view[["ID de origem"] + cols].to_csv(index=False).encode("utf-8-sig")
        st.download_button("↓ Exportar anúncios filtrados (CSV)", data=registros,
                           file_name="nexo_radar_vagas_demo_filtradas.csv", mime="text/csv", key="nv2_export")

    with st.expander("Sobre os dados e a futura integração com o portal", expanded=False):
        st.markdown("""
        **Base demonstrativa:** todas as observações, datas, vagas, quantidades, salários e requisitos
        são fictícios; a série histórica foi gerada apenas para ilustrar a leitura de tendências.
        Nenhuma requisição é feita ao portal municipal e não há persistência em banco.

        **Produção:** substituir a fonte sintética por API/exportação oficial, ou coletor autorizado;
        registrar a data de publicação, atualização e retirada de cada vaga, a fonte e o identificador;
        deduplicar, versionar e validar competências com taxonomia CBO/QBQ e supervisão humana.

        **Como interpretar:** "Anúncios" são registros distintos; "postos" somam as quantidades
        anunciadas. Competências e requisitos representam **frequência em anúncios**, não número
        de trabalhadores, postos ou lacunas formativas comprovadas.
        """)
        st.link_button("Consultar portal original ↗", PORTAL_URL)
        with st.expander("Ver amostra do HTML fictício e método de captura"):
            st.code(_fixture_html(DEMO_VAGAS[:1]), language="html")
