"""NEXO Qualifica+ | Resultados de Empregabilidade e Renda — MVP demonstrativo.

Compatível com app.py Streamlit e com nexo_planejamento_contratos.py.
As séries de emprego do Novo CAGED aqui geradas são SINTÉTICAS, NÃO OFICIAIS.
Importação de CSV e registros da rede permanecem exclusivamente na sessão.
Não permite identificação individual, nem atribuição causal a cursos.
"""
from __future__ import annotations

import io
import math
import random
from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

BASE_MES = pd.Timestamp("2026-09-01")  # referência DEMO; atualizar quando houver dado real autorizado

# As relações curso/CBO são ILUSTRATIVAS; devem ser validadas pelo gestor responsável.
OCUPACOES = [
    {"cbo":"782220", "ocupacao":"Operador de empilhadeira", "setor":"Logística", "base":54, "tendencia":0.32, "salario":2800},
    {"cbo":"414140", "ocupacao":"Auxiliar de logística", "setor":"Logística", "base":67, "tendencia":0.23, "salario":2280},
    {"cbo":"911305", "ocupacao":"Mecânico de manutenção industrial", "setor":"Indústria", "base":33, "tendencia":0.24, "salario":3550},
    {"cbo":"715615", "ocupacao":"Eletricista industrial", "setor":"Indústria", "base":29, "tendencia":0.31, "salario":3750},
    {"cbo":"351605", "ocupacao":"Técnico de segurança do trabalho", "setor":"Indústria", "base":21, "tendencia":0.08, "salario":3250},
    {"cbo":"411005", "ocupacao":"Auxiliar administrativo", "setor":"Serviços", "base":79, "tendencia":0.05, "salario":2260},
    {"cbo":"422105", "ocupacao":"Atendente/recepcionista", "setor":"Serviços", "base":64, "tendencia":-0.16, "salario":1900},
    {"cbo":"212405", "ocupacao":"Analista de sistemas (referência aproximada)", "setor":"Tecnologia", "base":19, "tendencia":0.30, "salario":4900},
    {"cbo":"317210", "ocupacao":"Suporte de tecnologia da informação", "setor":"Tecnologia", "base":24, "tendencia":0.20, "salario":2950},
    {"cbo":"521110", "ocupacao":"Vendedor do comércio", "setor":"Comércio", "base":95, "tendencia":0.10, "salario":2110},
    {"cbo":"421125", "ocupacao":"Operador de caixa", "setor":"Comércio", "base":58, "tendencia":-0.08, "salario":1970},
]
OCUP_BY_CBO = {r["cbo"]:r for r in OCUPACOES}
MAPEAMENTO_DEMO = {
    "OF01":["782220"], "OF02":["414140","782220"], "OF03":["911305"],
    "OF04":["715615"], "OF05":["351605"], "OF06":["411005"],
    "OF07":["422105"], "OF08":["212405"], "OF09":["317210"],
    "OF10":["521110"], "OF11":["421125"],
}


def demonstracao_caged() -> pd.DataFrame:
    """Dados simulados determinísticos de 24 competências mensais (sem fonte externa)."""
    rng = random.Random(246810)
    meses = pd.date_range(end=BASE_MES, periods=24, freq="MS")
    rows = []
    for i, mes in enumerate(meses):
        sazonal = 1 + 0.07 * math.sin(i * math.pi / 6)
        for occ in OCUPACOES:
            sentido = occ["tendencia"] * (i / 23)
            adm = max(0, int(round(occ["base"] * sazonal * (1 + sentido) + rng.randint(-6, 6))))
            des = max(0, int(round(occ["base"] * (0.96 + 0.04 * math.cos(i/4)) + rng.randint(-6, 6))))
            sal = max(0, int(round(occ["salario"] * (1 + 0.07 * i / 23) + rng.randint(-65, 65))))
            rows.append({"mes":mes, "cbo":occ["cbo"], "ocupacao":occ["ocupacao"],
                         "setor":occ["setor"], "admissoes":adm, "desligamentos":des,
                         "salario_medio_admissao":sal, "fonte":"SINTÉTICA / demonstração"})
    return pd.DataFrame(rows)


def preparar_csv_caged(conteudo: bytes) -> pd.DataFrame:
    """Aceita SOMENTE agregado municipal por mês/CBO; não recebe dados pessoais."""
    df = pd.read_csv(io.BytesIO(conteudo), sep=None, engine="python", dtype={"cbo":str})
    df.columns = [c.strip().lower() for c in df.columns]
    colunas = {"mes", "cbo", "admissoes", "desligamentos", "salario_medio_admissao"}
    faltantes = colunas - set(df.columns)
    if faltantes:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(sorted(faltantes)))
    if df.empty:
        raise ValueError("O arquivo não contém linhas")
    if len(df) > 100_000:
        raise ValueError("Arquivo acima do limite demonstrativo de 100 mil linhas")
    df["mes"] = pd.to_datetime(df["mes"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    df["cbo"] = df["cbo"].str.replace(r"\D", "", regex=True).str.zfill(6)
    for c in ("admissoes", "desligamentos", "salario_medio_admissao"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[list(colunas)].isna().any().any():
        raise ValueError("Há datas, CBOs ou números inválidos")
    if (df[["admissoes", "desligamentos", "salario_medio_admissao"]] < 0).any().any():
        raise ValueError("Admissões, desligamentos e salário não podem ser negativos")
    if not df["cbo"].str.fullmatch(r"\d{6}").all():
        raise ValueError("CBO deve conter seis dígitos")
    # Linhas desagregadas na mesma combinação mês/CBO são consolidadas; renda ponderada por admissões.
    df["massa_sal"] = df["salario_medio_admissao"] * df["admissoes"]
    df = df.groupby(["mes", "cbo"], as_index=False).agg({"admissoes":"sum", "desligamentos":"sum", "massa_sal":"sum"})
    df["salario_medio_admissao"] = df["massa_sal"] / df["admissoes"].replace(0, float("nan"))
    df["salario_medio_admissao"] = df["salario_medio_admissao"].fillna(0)
    df["ocupacao"] = df["cbo"].map(lambda c: OCUP_BY_CBO.get(c, {}).get("ocupacao", "Ocupação não mapeada"))
    df["setor"] = df["cbo"].map(lambda c: OCUP_BY_CBO.get(c, {}).get("setor", "Não classificado"))
    df["fonte"] = "CSV fornecido pelo operador (origem pendente de validação)"
    return df.drop(columns="massa_sal")


def periodos(base: pd.DataFrame, meses: int, setor: str, cbos: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if base.empty or not cbos:
        return base.iloc[0:0].copy(), base.iloc[0:0].copy()
    ultima = base["mes"].max()
    ini = ultima - pd.DateOffset(months=meses-1)
    ant_ini = ini - pd.DateOffset(months=meses)
    prev_fim = ini - pd.DateOffset(months=1)
    source = base[base["cbo"].isin(cbos)]
    if setor != "Todos os setores":
        source = source[source["setor"] == setor]
    atual = source[(source["mes"] >= ini) & (source["mes"] <= ultima)].copy()
    anterior = source[(source["mes"] >= ant_ini) & (source["mes"] <= prev_fim)].copy()
    return atual, anterior


def resumir_ocupacoes(atual: pd.DataFrame, anterior: pd.DataFrame) -> pd.DataFrame:
    linhas=[]
    if atual.empty:
        return pd.DataFrame(columns=["cbo", "ocupacao", "setor", "admissoes", "desligamentos", "saldo", "variacao_admissoes", "salario_medio_admissao"])
    anterior_adm=anterior.groupby("cbo")["admissoes"].sum().to_dict() if not anterior.empty else {}
    for cbo,g in atual.groupby("cbo"):
        adm=int(g["admissoes"].sum()); des=int(g["desligamentos"].sum())
        adm_ant=anterior_adm.get(cbo,0)
        var=(adm/adm_ant-1) if adm_ant > 0 else None
        wage=(g["salario_medio_admissao"]*g["admissoes"]).sum()/max(adm,1)
        linhas.append({"cbo":cbo,"ocupacao":g["ocupacao"].iloc[0],"setor":g["setor"].iloc[0],
                       "admissoes":adm,"desligamentos":des,"saldo":adm-des,
                       "variacao_admissoes":var,"salario_medio_admissao":float(wage) if adm else 0})
    return pd.DataFrame(linhas).sort_values("saldo",ascending=False)


def indicadores(atual:pd.DataFrame, anterior:pd.DataFrame) -> dict:
    adm=int(atual["admissoes"].sum()); des=int(atual["desligamentos"].sum())
    ant=int(anterior["admissoes"].sum());
    wage=float((atual["salario_medio_admissao"]*atual["admissoes"]).sum()/adm) if adm else 0
    return {"admissoes":adm, "desligamentos":des, "saldo":adm-des,
            "variacao":(adm/ant-1) if ant > 0 else None, "salario_medio_admissao":wage}


def _init():
    # Reuso dos cadastros já existentes no módulo Gestão das Ofertas de Qualificação.
    from nexo_planejamento_contratos import _init as iniciar_ofertas
    iniciar_ofertas()
    if "nexo_er_mapeamento" not in st.session_state:
        st.session_state["nexo_er_mapeamento"] = {k:list(v) for k,v in MAPEAMENTO_DEMO.items()}
    if "nexo_er_registros" not in st.session_state:
        st.session_state["nexo_er_registros"] = [
            {"curso_id":"OF01","instituicao":"Centro de Atendimento (fictício)","mes":"2026-08",
             "concluintes":32,"encaminhados":18,"contratacoes_relatadas":11,"renda_informada":2750.,"situacao":"Demonstrativo","origem":"SINTÉTICA"},
            {"curso_id":"OF02","instituicao":"Instituição Formadora A (fictícia)","mes":"2026-09",
             "concluintes":28,"encaminhados":19,"contratacoes_relatadas":12,"renda_informada":2340.,"situacao":"Demonstrativo","origem":"SINTÉTICA"},
            {"curso_id":"OF04","instituicao":"Centro de Atendimento (fictício)","mes":"2026-09",
             "concluintes":17,"encaminhados":12,"contratacoes_relatadas":8,"renda_informada":3600.,"situacao":"Demonstrativo","origem":"SINTÉTICA"},
        ]
    if "nexo_er_base_caged" not in st.session_state:
        st.session_state["nexo_er_base_caged"] = None


def _fmt_number(v) -> str:
    return f"{int(v):,}".replace(",", ".")


def _fmt_real(v) -> str:
    return f"R$ {float(v):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_var(v) -> str:
    return "Comparativo indisponível" if v is None or pd.isna(v) else f"{v:+.1%}".replace(".", ",")


def _safe(v) -> str:
    return escape(str(v if v is not None else ""))


def _styling():
    st.markdown('''<style>
      .er-hero{background:radial-gradient(circle at 85% 3%,#285b7e 0%,transparent 40%),linear-gradient(110deg,#0b1b3b,#194569);border-radius:18px;padding:28px 31px;color:#fff;margin-bottom:15px}
      .er-overline{font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#a7d9e7;font-weight:800}
      .er-hero h2{color:#fff!important;font-size:29px!important;font-weight:790!important;margin:8px 0!important}
      .er-hero p{color:#d6e6f7;font-size:13px;max-width:760px;margin:0}
      .er-kpi{border-radius:15px;border:1px solid #e5edf5;padding:18px;background:#fff;min-height:117px;box-shadow:0 5px 16px rgba(16,39,76,.04)}
      .er-kpi .tag{font-size:11px;color:#677a92;font-weight:650}.er-kpi .number{font-size:29px;font-weight:800;line-height:1.25;letter-spacing:-.03em;color:#152d50;margin:9px 0 6px}
      .er-kpi .description{color:#73869e;font-size:11px}.er-chapter{margin:23px 0 12px;color:#172f4f;font-size:20px;font-weight:760}
      .er-note{border:1px solid #dce8f4;border-radius:12px;background:#f3f8fd;padding:15px 17px;color:#315b80;font-size:13px;line-height:1.6;margin:15px 0}
      .er-alert{border:1px solid #f2e3bd;background:#fff9eb;padding:12px 16px;border-radius:11px;color:#795d26;font-size:12px;margin:12px 0}
      .er-hint{font-size:11px;color:#78889d;margin-top:2px}
      .er-pill{border-radius:999px;background:#eaf5f5;color:#15656a;padding:5px 10px;font-size:11px;font-weight:750}
      @media(max-width:750px){.er-hero{padding:20px}.er-hero h2{font-size:22px!important}.er-kpi{min-height:100px}.er-kpi .number{font-size:24px}}
    </style>''',unsafe_allow_html=True)


def _kpi(titulo,valor,descricao):
    st.markdown(f'<div class="er-kpi"><div class="tag">{_safe(titulo)}</div><div class="number">{_safe(valor)}</div><div class="description">{_safe(descricao)}</div></div>',unsafe_allow_html=True)


def _sec(titulo):
    st.markdown(f'<div class="er-chapter">{_safe(titulo)}</div>',unsafe_allow_html=True)


def _ofertas() -> pd.DataFrame:
    offers=pd.DataFrame(st.session_state.get("nexo_plan_courses", []))
    if offers.empty:
        return offers
    contracts=pd.DataFrame(st.session_state.get("nexo_plan_contracts", []))
    if not contracts.empty:
        offers=offers.merge(contracts[["id","numero"]], left_on="contrato_id",right_on="id",how="left",suffixes=("","_contrato"))
    else:
        offers["numero"]="Não informado"
    return offers


def _associados(offers:pd.DataFrame, mapeamento:dict) -> set[str]:
    return set(cbo for cid in offers["id"].tolist() for cbo in mapeamento.get(cid,[])) if not offers.empty else set()


def _course_summary(offers:pd.DataFrame, periods_cur:pd.DataFrame, periods_prev:pd.DataFrame, mapa:dict, registros:list) -> pd.DataFrame:
    rows=[]
    for _,o in offers.iterrows():
        cbos=set(mapa.get(o["id"],[])); subset=periods_cur[periods_cur["cbo"].isin(cbos)]
        prev=periods_prev[periods_prev["cbo"].isin(cbos)]
        s=indicadores(subset,prev)
        if not cbos or subset.empty: status="Sem mapeamento / evidência"
        elif s["saldo"] < 0 and (s["variacao"] or 0) < 0: status="Atenção à dinâmica"
        elif s["saldo"] > 0 and (s["variacao"] or 0) > 0: status="Dinâmica favorável"
        else: status="Monitorar evolução"
        reports=sum(1 for r in registros if r["curso_id"]==o["id"])
        rows.append({"Curso":o["curso"],"Contrato":o.get("numero","—"), "Setor":o["setor"],
                     "Vagas contratadas":int(o["contratadas"]),"Saldo de vagas formativas":max(0,int(o["contratadas"])-int(o["ocupadas"])),
                     "Ocupações associadas":", ".join(OCUP_BY_CBO.get(c,{}).get("ocupacao",f"CBO {c}") for c in sorted(cbos)) or "A validar",
                     "Saldo CAGED das ocupações":s["saldo"] if not subset.empty else None,
                     "Admissões":s["admissoes"] if not subset.empty else None,
                     "Remuneração admissão":s["salario_medio_admissao"] if not subset.empty else None,
                     "Situação":status,"Registros da rede":reports,"_id":o["id"]})
    return pd.DataFrame(rows)


def render_resultados_empregabilidade():
    """Entrada pública da nova página; não substitui outras funções do NEXO."""
    _init(); _styling()
    st.markdown('''<div class="er-hero"><div class="er-overline">NEXO QUALIFICA+ · Inteligência de Resultados</div>
      <h2>Resultados de Empregabilidade e Renda</h2>
      <p>O que mudou nas ocupações relacionadas aos cursos contratados — e quais evidências a rede já conseguiu registrar.</p></div>''',unsafe_allow_html=True)
    fonte = "Base sintética do CAGED (demonstração)" if st.session_state["nexo_er_base_caged"] is None else "CSV carregado nesta sessão (procedência a validar)"
    st.markdown(f'<div class="er-alert"><b>Ambiente demonstrativo.</b> {escape(fonte)} · vínculo curso–ocupação provisório · sem acesso à Carteira de Trabalho · não há mensuração causal de impacto.</div>',unsafe_allow_html=True)

    ofertas=_ofertas()
    if ofertas.empty:
        st.warning("Nenhum curso cadastrado em Gestão das Ofertas de Qualificação. Cadastre ofertas para ativar o monitoramento.")
        return
    period_choices={"3 meses":3,"6 meses":6,"12 meses":12}
    f1,f2,f3=st.columns([1,1,1.4])
    with f1: period_name=st.selectbox("Período histórico",list(period_choices), index=2,key="er_period")
    with f2: sector=st.selectbox("Setor", ["Todos os setores"]+sorted(ofertas["setor"].dropna().unique().tolist()),key="er_sector")
    with f3:
        opts=["Todos os contratos"]+sorted(ofertas["numero"].dropna().unique().tolist())
        contract=st.selectbox("Contrato",opts,key="er_contract")
    offers_filter=ofertas.copy()
    if sector!="Todos os setores": offers_filter=offers_filter[offers_filter["setor"]==sector]
    if contract!="Todos os contratos": offers_filter=offers_filter[offers_filter["numero"]==contract]
    mapa=st.session_state["nexo_er_mapeamento"]
    cbos=_associados(offers_filter,mapa)
    base=st.session_state["nexo_er_base_caged"]
    if base is None: base=demonstracao_caged()
    atual,anterior=periodos(base,period_choices[period_name],sector,cbos)
    metrics=indicadores(atual,anterior)
    occ_sum=resumir_ocupacoes(atual,anterior)
    curso_sum=_course_summary(offers_filter,atual,anterior,mapa,st.session_state["nexo_er_registros"])
    registros_filtrados=[r for r in st.session_state["nexo_er_registros"] if r["curso_id"] in offers_filter["id"].tolist()]
    periodo_max=base["mes"].max().strftime("%m/%Y") if not base.empty else "—"
    st.caption(f"Referência final disponível na base: {periodo_max} · Unidade geográfica esperada: Itajaí/SC · Saldo = admissões − desligamentos.")

    tabs=st.tabs(["Visão executiva","Mercado & ocupações","Cursos monitorados","Evidências da rede"])
    with tabs[0]:
        _sec("Panorama das ocupações relacionadas às ofertas")
        k1,k2,k3,k4=st.columns(4,gap="small")
        with k1:_kpi("Cursos monitorados",_fmt_number(len(offers_filter)),"Cursos selecionados na gestão da oferta")
        with k2:_kpi("Ocupações mapeadas",_fmt_number(len(cbos)),"CBOs únicos; sem dupla contagem")
        with k3:_kpi("Saldo de empregos",f'{metrics["saldo"]:+,}'.replace(",","."),"Admissões menos desligamentos")
        with k4:_kpi("Variação de admissões",_fmt_var(metrics["variacao"]),"Ante período de mesma duração")
        _sec("O que os dados sinalizam")
        if atual.empty:
            st.info("Sem registros de ocupações relacionadas na base ou no recorte selecionado.")
        else:
            npos=int((occ_sum["saldo"]>0).sum()); nneg=int((occ_sum["saldo"]<0).sum())
            top=occ_sum.iloc[0]["ocupacao"]
            st.markdown(f'<div class="er-note">No período, <b>{_fmt_number(len(occ_sum))} ocupações</b> vinculadas aos cursos selecionados foram monitoradas: <b>{npos} com saldo positivo</b> e <b>{nneg} negativo</b>. O maior saldo aparece em <b>{_safe(top)}</b>. Estes são sinais do mercado formal, não contratações comprovadas de ex-alunos.</div>',unsafe_allow_html=True)
            left,right=st.columns([1.4,1],gap="large")
            with left:
                st.markdown("**Evolução mensal do saldo de empregos**")
                by_month=atual.groupby("mes",as_index=False)[["admissoes","desligamentos"]].sum()
                by_month["Saldo"] = by_month["admissoes"]-by_month["desligamentos"]
                by_month["Mês"] = by_month["mes"].dt.strftime("%b/%y")
                st.bar_chart(by_month.set_index("Mês")[["Saldo"]],height=265,use_container_width=True)
            with right:
                st.markdown("**Sinais que merecem atenção**")
                if nneg: st.warning(f"{nneg} ocupação(ões) com saldo negativo no recorte.")
                else: st.success("Nenhuma ocupação com saldo negativo no período selecionado.")
                st.info(f"{len(registros_filtrados)} registro(s) agregados da rede vinculados aos cursos selecionados.")
                st.caption("Priorizar conferência da relação curso–CBO, qualidade dos dados e período de comparação.")
        _sec("Leitura para decisão pública")
        st.markdown("A dinâmica ocupacional ajuda a **priorizar investigação sobre o portfólio**. Para avaliar o efeito da formação sobre as pessoas, também são necessários registros de conclusão, encaminhamento e contratação, obtidos de fontes autorizadas e com critérios de validação.")

    with tabs[1]:
        _sec("Mercado formal nas ocupações relacionadas")
        st.caption("Comparação histórica por CBO. Um mesmo CBO associado a vários cursos é contado apenas uma vez nos totais executivos.")
        if atual.empty:
            st.info("Sem dados no período. Confira importação e mapeamentos.")
        else:
            k1,k2,k3=st.columns(3,gap="small")
            with k1:_kpi("Admissões",_fmt_number(metrics["admissoes"]),"Vínculos formais admitidos nas ocupações")
            with k2:_kpi("Desligamentos",_fmt_number(metrics["desligamentos"]),"Vínculos encerrados nas ocupações")
            with k3:_kpi("Remuneração média de admissão",_fmt_real(metrics["salario_medio_admissao"]),"Média ponderada pelas admissões")
            left,right=st.columns([1.2,1],gap="large")
            with left:
                st.markdown("**Admissões e desligamentos no período**")
                series=atual.groupby("mes")["admissoes"].sum().to_frame("Admissões")
                series["Desligamentos"]=atual.groupby("mes")["desligamentos"].sum()
                series.index=series.index.strftime("%b/%y")
                st.line_chart(series,height=300,use_container_width=True)
            with right:
                st.markdown("**Ocupações com maior saldo**")
                top=occ_sum.sort_values("saldo",ascending=False).head(7)
                st.bar_chart(top.set_index("ocupacao")[["saldo"]],height=300,use_container_width=True,horizontal=True)
            _sec("Detalhamento ocupacional")
            occ_display=occ_sum.copy()
            occ_display["Admissões vs. período anterior"]=occ_display["variacao_admissoes"].map(_fmt_var)
            occ_display["Remuneração de admissão"]=occ_display["salario_medio_admissao"].map(_fmt_real)
            occ_display=occ_display.rename(columns={"ocupacao":"Ocupação","cbo":"CBO","setor":"Setor","admissoes":"Admissões","desligamentos":"Desligamentos","saldo":"Saldo"})
            st.dataframe(occ_display[["Ocupação","CBO","Setor","Admissões","Desligamentos","Saldo","Admissões vs. período anterior","Remuneração de admissão"]],hide_index=True,use_container_width=True)
            st.caption("Remuneração média de admissão NÃO corresponde a aumento de renda dos egressos; saldo positivo NÃO comprova efeito dos cursos.")

    with tabs[2]:
        _sec("Cursos contratados × sinais de emprego")
        st.caption("Cursos e saldos de vagas formativas vêm do módulo Gestão das Ofertas. O saldo CAGED é do mercado formal nas ocupações relacionadas, não de seus alunos.")
        if curso_sum.empty:
            st.info("Não há cursos nos filtros selecionados.")
        else:
            show=curso_sum.drop(columns=["_id"]).copy()
            show["Remuneração admissão"]=show["Remuneração admissão"].map(lambda x: _fmt_real(x) if pd.notna(x) else "—")
            show["Saldo CAGED das ocupações"] = show["Saldo CAGED das ocupações"].map(lambda x: _fmt_number(x) if pd.notna(x) else "—")
            st.dataframe(show,hide_index=True,use_container_width=True,height=365)
            st.markdown("**Explorar curso e ocupações**")
            course_ids=offers_filter.set_index("id")["curso"].to_dict()
            selected=st.selectbox("Curso",list(course_ids),format_func=lambda x:course_ids[x],key="er_detail_course")
            row=curso_sum[curso_sum["_id"]==selected].iloc[0]
            c1,c2=st.columns([1,1],gap="large")
            with c1:
                st.markdown(f"**{row['Curso']}**")
                st.write(f"Contrato: {row['Contrato']} · Setor: {row['Setor']}")
                st.write(f"**Vagas formativas disponíveis:** {row['Saldo de vagas formativas']}")
                st.write(f"**Ocupações relacionadas (referência preliminar):** {row['Ocupações associadas']}")
            with c2:
                st.markdown("**Leitura gerencial**")
                st.info(f"{row['Situação']}. Cruzar esta dinâmica com o Radar de Vagas, o conteúdo do curso e os registros reais de encaminhamento antes de decidir ampliar ou revisar a oferta.")
            st.caption("O mesmo saldo CAGED pode aparecer em mais de um curso que compartilhe uma ocupação. Não somar as linhas dos cursos para formar um total municipal.")

    with tabs[3]:
        _sec("Evidências complementares da rede")
        st.markdown("Registro **agregado** por instituição e curso, sem nome, CPF ou dados pessoais de participantes. Lançamentos feitos aqui permanecem apenas nesta sessão.")
        aggregate=st.session_state["nexo_er_registros"]
        if registros_filtrados:
            df_registry=pd.DataFrame(registros_filtrados)
            df_registry["Curso"]=df_registry["curso_id"].map(offers_filter.set_index("id")["curso"].to_dict())
            st.dataframe(df_registry[["Curso","instituicao","mes","concluintes","encaminhados","contratacoes_relatadas","renda_informada","situacao","origem"]].rename(columns={"instituicao":"Instituição","mes":"Mês","concluintes":"Concluintes informados","encaminhados":"Encaminhamentos informados","contratacoes_relatadas":"Contratações relatadas","renda_informada":"Renda inicial declarada","situacao":"Situação","origem":"Origem"}),hide_index=True,use_container_width=True)
            st.download_button("Exportar registros agregados (CSV)",pd.DataFrame(registros_filtrados).to_csv(index=False).encode("utf-8-sig"),"nexo_registros_rede_demo.csv","text/csv",key="er_export")
        else:
            st.info("Ainda não há registros complementares para os cursos selecionados.")
        with st.expander("Adicionar registro da instituição",expanded=False):
            with st.form("er_form_registry",clear_on_submit=True):
                names=offers_filter.set_index("id")["curso"].to_dict()
                id_course=st.selectbox("Curso",list(names),format_func=lambda x:names[x],key="er_reg_course")
                instituicao=st.text_input("Instituição ou unidade responsável",max_chars=120)
                mes_ref=st.date_input("Mês de referência",value=BASE_MES.date())
                ca,cb,cc=st.columns(3)
                with ca: concl=st.number_input("Concluintes informados",min_value=0,step=1)
                with cb: encamin=st.number_input("Encaminhamentos informados",min_value=0,step=1)
                with cc: contrat=st.number_input("Contratações relatadas",min_value=0,step=1)
                renda=st.number_input("Renda inicial média declarada (R$, opcional)",min_value=0.,step=50.)
                submitted=st.form_submit_button("Registrar evidência agregada",type="primary")
                if submitted:
                    if not instituicao.strip():
                        st.error("Informe a instituição responsável.")
                    elif contrat > max(concl,encamin) and max(concl,encamin)>0:
                        st.error("Confira os quantitativos: contratações relatadas superiores a concluintes e encaminhados.")
                    else:
                        aggregate.append({"curso_id":id_course,"instituicao":instituicao.strip(),"mes":mes_ref.strftime("%Y-%m"),
                                          "concluintes":int(concl),"encaminhados":int(encamin),"contratacoes_relatadas":int(contrat),
                                          "renda_informada":float(renda),"situacao":"Pendente de validação","origem":"Informado manualmente nesta sessão"})
                        st.success("Registro agregado adicionado à sessão. Ainda não equivale a contratação verificada.")
                        st.rerun()
        with st.expander("Administração da base CAGED e vínculos curso–ocupação",expanded=False):
            st.markdown("**Importar agregado mensal por ocupação (CSV)**")
            st.caption("Campos: mes (AAAA-MM), cbo (6 dígitos), admissoes, desligamentos, salario_medio_admissao. Somente base agregada do município, sem CPF ou informação de trabalhadores.")
            upload=st.file_uploader("Selecione a base municipal autorizada",type=["csv"],key="er_caged_upload")
            if upload is not None and st.button("Conferir e usar CSV nesta sessão",key="er_use_caged"):
                try:
                    imported=preparar_csv_caged(upload.getvalue())
                    st.session_state["nexo_er_base_caged"] = imported
                    st.success(f"{len(imported)} agregações carregadas. Fonte declarada pelo operador, ainda não verificada.")
                    st.rerun()
                except (ValueError,UnicodeError,pd.errors.ParserError) as ex:
                    st.error(f"Não foi possível carregar: {ex}")
            if st.session_state["nexo_er_base_caged"] is not None and st.button("Retornar à simulação",key="er_restore"):
                st.session_state["nexo_er_base_caged"]=None
                st.rerun()
            st.markdown("**Vincular curso a ocupações (mapa sujeito a validação)**")
            offers_list=ofertas.set_index("id")["curso"].to_dict()
            cid=st.selectbox("Curso para ajustar vínculo",list(offers_list),format_func=lambda x:offers_list[x],key="er_map_course")
            pick=st.multiselect("Ocupações relacionadas",options=list(OCUP_BY_CBO),default=[x for x in mapa.get(cid,[]) if x in OCUP_BY_CBO],format_func=lambda c:f'{OCUP_BY_CBO[c]["ocupacao"]} · {c}',key=f"er_map_select_{cid}")
            if st.button("Aplicar vínculos nesta sessão",key="er_save_map"):
                mapa[cid]=pick
                st.success("Mapeamento atualizado somente nesta sessão; requer validação ocupacional.")
                st.rerun()
    st.divider()
    st.caption("NEXO Qualifica+ · ambiente demonstrativo · indicadores agregados · atualizações não persistidas · nenhuma inferência causal automática.")
