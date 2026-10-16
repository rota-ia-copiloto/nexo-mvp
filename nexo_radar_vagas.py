"""NEXO Qualifica+ | Radar de Vagas - demonstração local e offline.

Integração proposta para app.py:
    from nexo_radar_vagas import render_radar_vagas
    ...
    elif page == 'Radar de Vagas (demo)':
        render_radar_vagas()

NÃO ACESSA O PORTAL: demonstra parsing de HTML sintético, normalização,
regras de extração de competências, filtros, auditoria e exportação.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
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


def _styling():
    st.markdown("""
    <style>
    .radar-hero {background:linear-gradient(110deg,#071B3A 0%,#0D3765 63%,#174E70 100%);
      color:#fff;padding:24px 28px;border-radius:16px;margin-bottom:14px}
    .radar-hero h2 {color:#fff;margin:8px 0;font-size:1.85rem}
    .radar-hero p {color:#DDEBF7;margin:0}
    .radar-kicker {font-size:12px;letter-spacing:.13em;color:#B7D9F2;font-weight:700}
    .radar-pill {display:inline-block;background:#FDE3A7;color:#694500;border-radius:999px;
      padding:4px 10px;font-size:11px;font-weight:800;margin-bottom:10px}
    .radar-flow {padding:12px 10px;border-radius:12px;background:#F1F6FC;border:1px solid #DDE7F2;
      color:#183454;font-size:13px;min-height:86px}
    .radar-flow b {color:#0A2646}
    .radar-note {border-left:4px solid #D9A92E;background:#FFF9EB;padding:12px 16px;border-radius:8px}
    </style>
    """, unsafe_allow_html=True)


def render_radar_vagas():
    """Página de demonstração, pronta para integrar ao menu do NEXO."""
    _styling()
    st.markdown("""
      <div class="radar-hero">
        <div class="radar-kicker">NEXO QUALIFICA+ / INTELIGÊNCIA DE MERCADO</div>
        <div class="radar-pill">AMBIENTE DEMONSTRATIVO • SEM RASPAGEM REAL</div>
        <h2>Radar de Vagas | Itajaí</h2>
        <p>Do anúncio da vaga à inteligência de competências e decisões de qualificação.</p>
      </div>
    """, unsafe_allow_html=True)
    st.info("**Amostra totalmente sintética.** Nenhuma requisição é feita ao site de Itajaí. A coleta abaixo processa uma página HTML fictícia, apenas para demonstrar como o futuro conector funcionará.")

    if "radar_demo_ciclo" not in st.session_state:
        st.session_state.radar_demo_ciclo = 0
    if "radar_demo_validadas" not in st.session_state:
        st.session_state.radar_demo_validadas = {}

    top1, top2, top3 = st.columns([1.4, 1.25, 1])
    with top1:
        st.markdown("**Fonte prevista:** Balcão de Empregos — Itajaí/SC")
        st.caption("Modalidade preferencial futura: API ou exportação oficial; alternativa: scraping autorizado.")
    with top2:
        if st.button("↻ Simular nova coleta", type="primary", use_container_width=True):
            st.session_state.radar_demo_ciclo = min(2, st.session_state.radar_demo_ciclo + 1)
            st.toast("Parsing do HTML sintético realizado. Nenhum site externo foi acessado.")
    with top3:
        st.link_button("Consultar portal original ↗", PORTAL_URL, use_container_width=True)

    ciclo = st.session_state.radar_demo_ciclo
    quantidade = [8, 10, 12][ciclo]
    html = _fixture_html(DEMO_VAGAS[:quantidade])
    df, evi = _pipeline(html)
    if df.empty:
        st.error("A simulação não produziu registros.")
        return
    st.caption(f"Execução local #{ciclo+1} · {len(df)} registros fictícios processados · sem conexão de rede · extração por regra")

    contagem_skills = Counter(s for ls in df["Competências sugeridas"] for s in ls)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Registros capturados", f"{len(df)}", delta=f"+{2 if ciclo else 0} no ciclo" if ciclo else None)
    k2.metric("Postos anunciados", int(df["Postos"].sum()))
    k3.metric("Competências mapeadas", len(contagem_skills))
    k4.metric("Salário não informado", int(df["Salário (R$)"].isna().sum()))

    st.markdown("### Fluxo demonstrado")
    f1, f2, f3, f4 = st.columns(4)
    for col, title, detail in [(f1, "01 · Fonte", "Listagem HTML sintética"),
                               (f2, "02 · Captura", "Parser + ID de origem"),
                               (f3, "03 · Tratamento", "Limpeza + campos tabulares"),
                               (f4, "04 · Inteligência", "Regras de skills + validação")]:
        with col:
            st.markdown(f'<div class="radar-flow"><b>{title}</b><br>{detail}</div>', unsafe_allow_html=True)

    st.markdown("### Panorama da demanda simulada")
    a, b = st.columns([1.25, 1])
    with a:
        st.caption("Competências detectadas em descrições (número de anúncios, não número de pessoas)")
        freq = pd.DataFrame(contagem_skills.most_common(8), columns=["Competência", "Vagas"])
        st.bar_chart(freq.set_index("Competência"), horizontal=True, use_container_width=True)
    with b:
        st.caption("Postos anunciados por setor")
        area = df.groupby("Setor")["Postos"].sum().sort_values(ascending=False)
        st.bar_chart(area, use_container_width=True)

    st.markdown("### Vagas capturadas e estruturadas")
    fil1, fil2 = st.columns([1, 2])
    with fil1:
        options = ["Todos"] + sorted(df["Setor"].unique().tolist())
        setor = st.selectbox("Setor", options, key="radar_demo_setor")
    with fil2:
        texto = st.text_input("Buscar ocupação ou descrição", placeholder="Ex.: logística, dados, atendimento", key="radar_demo_busca")
    filtrado = df.copy()
    if setor != "Todos":
        filtrado = filtrado[filtrado["Setor"] == setor]
    if texto.strip():
        t = _sem_acento(texto)
        filtrado = filtrado[filtrado.apply(lambda r: t in _sem_acento(r["Ocupação"] + " " + r["Descrição original"]), axis=1)]
    view = filtrado[["ID de origem", "Ocupação", "Setor", "Postos", "Salário (R$)", "Bairro", "Nº competências"]].copy()
    st.dataframe(view, use_container_width=True, hide_index=True,
                 column_config={"Salário (R$)": st.column_config.NumberColumn(format="R$ %.2f")})
    st.download_button("↓ Exportar registros sintéticos (CSV)", df.drop(columns=["Competências sugeridas"]).to_csv(index=False).encode("utf-8-sig"),
                       file_name="nexo_radar_vagas_exemplo.csv", mime="text/csv", key="radar_demo_csv")

    st.markdown("### Inspeção de uma vaga e validação humana")
    ids = filtrado["ID de origem"].tolist()
    if not ids:
        st.warning("Nenhuma vaga corresponde ao filtro selecionado.")
    else:
        id_escolhido = st.selectbox("Escolher registro demonstrativo", ids,
            format_func=lambda id_: f"{id_} • {df.loc[df['ID de origem']==id_, 'Ocupação'].iloc[0]}",
            key="radar_demo_item")
        vaga = df.loc[df["ID de origem"] == id_escolhido].iloc[0]
        left, right = st.columns([1, 1.1])
        with left:
            st.markdown("**Texto de origem (sintético)**")
            st.text_area("Descrição como apareceu no HTML", vaga["Descrição original"], height=155, disabled=True)
            st.markdown("**Campos já normalizados**")
            st.json({"id_origem": vaga["ID de origem"], "titulo": vaga["Ocupação"],
                     "quantidade": int(vaga["Postos"]), "salario": None if pd.isna(vaga["Salário (R$)"]) else float(vaga["Salário (R$)"]),
                     "setor": vaga["Setor"], "cbo": "A validar", "fonte": "amostra fictícia"}, expanded=True)
        with right:
            st.markdown("**Competências sugeridas por regras lexicais**")
            evidencias = evi.get(id_escolhido, [])
            if evidencias:
                st.dataframe(pd.DataFrame(evidencias).rename(columns={"competencia":"Competência", "gatilho_textual":"Termo encontrado", "metodo":"Método"}),
                             hide_index=True, use_container_width=True)
                all_skills = vaga["Competências sugeridas"]
                atual = st.session_state.radar_demo_validadas.get(id_escolhido, [])
                escolhidas = st.multiselect("Validação do analista (apenas nesta sessão)", all_skills,
                                            default=[x for x in atual if x in all_skills], key=f"radar_validate_{id_escolhido}")
                if st.button("Registrar validação demonstrativa", key=f"radar_save_{id_escolhido}"):
                    st.session_state.radar_demo_validadas[id_escolhido] = escolhidas
                    st.success(f"{len(escolhidas)} competência(s) registrada(s) em memória de sessão; sem persistência em banco.")
            else:
                st.warning("Nenhuma competência identificada: necessita avaliação humana.")
            st.caption("A vinculação à CBO/QBQ e a confirmação das skills são etapas posteriores; não há classificação oficial automática nesta demo.")

    with st.expander("Ver uma amostra do HTML fictício interpretado pelo coletor"):
        st.code(_fixture_html(DEMO_VAGAS[:1]), language="html")
    with st.expander("O que falta para conectar o portal verdadeiro"):
        st.markdown("1. Solicitar API/exportação oficial ou validar autorização e regras para acesso automatizado.\n"
                    "2. Inspecionar a estrutura HTML real, paginação, políticas de acesso e cadência aceitável.\n"
                    "3. Criar coletor robusto, logs e alerta quando a estrutura da página mudar.\n"
                    "4. Persistir em PostgreSQL/Supabase, com identificação da fonte, deduplicação e histórico.\n"
                    "5. Acoplar taxonomia versionada CBO/QBQ, supervisão humana e controle de qualidade.\n"
                    "6. Conectar dados agregados ao módulo de planejamento de cursos e medir sua efetividade.")

    st.markdown('<div class="radar-note"><b>Limite interpretativo:</b> o volume de vagas e as competências extraídas são sinais de demanda. Não configuram, sozinhos, escassez de trabalhadores nem necessidades de qualificação comprovadas; para isso, o NEXO deverá cruzar esses sinais com diagnósticos de competências e outros dados.</div>', unsafe_allow_html=True)
