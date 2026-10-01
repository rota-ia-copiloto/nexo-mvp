from __future__ import annotations

import json
import pandas as pd
import streamlit as st

from nexo.ui.theme import header

DEMAND_ID = "DEMAND001"
ACTOR_ID = "empresa_alfa"


def _semantic_band(score: float) -> tuple[str, str]:
    if score >= 0.60:
        return "Forte", "candidato semanticamente consistente"
    if score >= 0.50:
        return "Moderada", "alternativa plausível; revisão humana importante"
    if score >= 0.45:
        return "Fraca", "apenas alternativa exploratória"
    return "Insuficiente", "não recomendar como candidato"


def _semantic_rows(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            value = []
    if not isinstance(value, list):
        return []
    return sorted(value, key=lambda x: float(x.get("similarity") or 0), reverse=True)[:3]


def render(ctx):
    # If Edge Functions are configured, use the real Supabase-backed company flow.
    if getattr(ctx, "edge", None) is not None:
        return _render_edge(ctx)
    return _render_legacy(ctx)


def _render_edge(ctx):
    header(
        "EMPRESAS",
        "Demanda empresarial",
        "Transforme uma necessidade de contratação em competências e pipeline local.",
    )

    try:
        state = ctx.edge.state(DEMAND_ID)
    except Exception as exc:
        st.error(f"Não foi possível carregar a demanda real do Supabase: {exc}")
        st.caption("Confira SUPABASE_URL e SUPABASE_EDGE_KEY no ambiente do Streamlit.")
        return

    company = state.get("company") or {"company_name": "Empresa Alfa", "sector": "Indústria Química", "employees": 850}
    demand = state.get("demand") or {}
    st.subheader(company.get("company_name", "Empresa Alfa"))
    a, b, c = st.columns(3)
    a.metric("Setor", company.get("sector") or "—")
    b.metric("Colaboradores", int(company.get("employees") or 0))
    c.metric("Status da demanda", str(demand.get("status") or "draft").upper())
    st.success("Fluxo real conectado ao Supabase: Edge Functions + PostgreSQL + pgvector.")

    st.markdown("### 1 · Necessidade de contratação")
    qcol, hcol = st.columns(2)
    quantity = qcol.number_input(
        "Quantidade de profissionais",
        min_value=1,
        value=int(demand.get("quantity") or 20),
        step=1,
        key="edge_quantity",
    )
    horizons = ["3 meses", "6 meses", "12 meses"]
    current_horizon = demand.get("horizon") or "6 meses"
    horizon = hcol.selectbox(
        "Horizonte",
        horizons,
        index=horizons.index(current_horizon) if current_horizon in horizons else 1,
        key="edge_horizon",
    )
    description = st.text_area(
        "Descrição da função",
        demand.get("description") or "Buscamos operadores de processo para acompanhar parâmetros da linha de produção, operar equipamentos industriais e seguir procedimentos de segurança.",
        height=150,
        key="edge_description",
    )

    left, right = st.columns([1, 1])
    if left.button("Salvar demanda", use_container_width=True):
        try:
            with st.spinner("Salvando no Supabase..."):
                ctx.edge.upsert_demand(DEMAND_ID, description, quantity, horizon, ACTOR_ID)
            st.success("Demanda salva e auditada.")
            st.rerun()
        except Exception as exc:
            st.error(f"Falha ao salvar: {exc}")

    if right.button("✨ Analisar com NEXO", type="primary", use_container_width=True):
        try:
            with st.spinner("Salvando, extraindo competências e normalizando semanticamente..."):
                ctx.edge.upsert_demand(DEMAND_ID, description, quantity, horizon, ACTOR_ID)
                result = ctx.edge.analyze_demand(DEMAND_ID, description, ACTOR_ID)
            st.session_state["last_occupation_summary"] = result.get("occupation_summary")
            st.success(f"{len(result.get('candidates') or [])} competências candidatas geradas para revisão humana.")
            st.rerun()
        except Exception as exc:
            st.error(f"Falha na análise: {exc}")

    summary = st.session_state.get("last_occupation_summary")
    if summary:
        st.info(f"**Síntese ocupacional gerada pelo NEXO:** {summary}")

    candidates = state.get("candidates") or []
    pending = [c for c in candidates if c.get("review_status") == "pending"]
    reviewed = [c for c in candidates if c.get("review_status") != "pending"]
    taxonomy = state.get("taxonomy") or []
    skill_name_by_id = {r["skill_id"]: r["skill_name"] for r in taxonomy}
    skill_options = [r["skill_id"] for r in taxonomy]

    st.markdown("### 2 · Revisão humana")
    st.caption(
        "O LLM extrai o termo; o pgvector recupera candidatos da taxonomia; a empresa valida, remapeia ou rejeita. "
        "Nenhuma sugestão vira requisito definitivo automaticamente."
    )
    st.metric("Pendentes de decisão", len(pending))

    if not pending:
        st.success("Todas as sugestões foram revisadas.")
    else:
        for row in pending:
            cid = str(row["candidate_id"])
            semantic = _semantic_rows(row.get("semantic_candidates"))
            proposed = row.get("proposed_skill_id")
            default_skill = proposed if proposed in skill_options else (semantic[0].get("skill_id") if semantic else None)
            with st.container(border=True):
                t1, t2 = st.columns([3, 1])
                t1.markdown(f"#### {row.get('raw_term')}")
                t1.markdown(f"Sugestão principal: **{row.get('proposed_label') or 'Revisão necessária'}**")
                t2.metric("Extração LLM", f"{float(row.get('confidence') or 0):.0%}")
                if row.get("evidence_excerpt"):
                    st.caption(f"Evidência na descrição: “{row['evidence_excerpt']}”")
                if row.get("rationale"):
                    st.caption(f"Justificativa: {row['rationale']}")

                score = float(row.get("normalization_score") or 0)
                band, note = _semantic_band(score)
                st.markdown(f"**Normalização:** `{row.get('normalization_method') or '—'}` · **{score:.0%} — {band}**")
                st.caption(note + ". Similaridade vetorial não equivale a requisito validado.")

                if semantic:
                    alt = pd.DataFrame(semantic)
                    alt.insert(0, "#", range(1, len(alt) + 1))
                    alt["Faixa"] = alt["similarity"].astype(float).map(lambda x: _semantic_band(x)[0])
                    alt["Similaridade"] = alt["similarity"].astype(float).map(lambda x: f"{x:.0%}")
                    show = alt[["#", "skill_id", "skill_name", "matched_text", "Similaridade", "Faixa"]].copy()
                    show.columns = ["#", "ID", "Skill NEXO", "Texto mais próximo", "Similaridade", "Faixa"]
                    with st.expander("Top 3 semântico", expanded=True):
                        st.dataframe(show, use_container_width=True, hide_index=True)

                c1, c2 = st.columns([2.2, 1.2])
                selected_skill = c1.selectbox(
                    "Competência final",
                    skill_options,
                    index=skill_options.index(default_skill) if default_skill in skill_options else 0,
                    format_func=lambda sid: f"{sid} · {skill_name_by_id.get(sid, sid)}",
                    key=f"edge_skill_{cid}",
                )
                req_types = ["mandatory", "desired", "suggested"]
                req_default = row.get("requirement_type") if row.get("requirement_type") in req_types else "suggested"
                req_type = c2.selectbox(
                    "Tipo",
                    req_types,
                    index=req_types.index(req_default),
                    key=f"edge_req_{cid}",
                )
                notes = st.text_input("Observação da empresa (opcional)", key=f"edge_note_{cid}")

                b1, b2, b3 = st.columns(3)
                if b1.button("✓ Validar", key=f"validate_{cid}", use_container_width=True):
                    action = "validate" if selected_skill == proposed else "remap"
                    _edge_review(ctx, cid, action, selected_skill, req_type, notes)
                if b2.button("↔ Alterar e validar", key=f"remap_{cid}", use_container_width=True):
                    _edge_review(ctx, cid, "remap", selected_skill, req_type, notes)
                if b3.button("✕ Rejeitar", key=f"reject_{cid}", use_container_width=True):
                    _edge_review(ctx, cid, "reject", None, req_type, notes)

    if reviewed:
        st.markdown("#### Histórico da revisão")
        rows = []
        for r in reviewed:
            final_id = r.get("final_skill_id")
            decision = r.get("review_status")
            if decision == "validated" and final_id == r.get("proposed_skill_id"):
                label = "Validado"
            elif decision == "validated":
                label = "Remapeado"
            else:
                label = "Rejeitado"
            rows.append({
                "Termo extraído": r.get("raw_term"),
                "Sugestão IA": r.get("proposed_label"),
                "Decisão": label,
                "Skill final": skill_name_by_id.get(final_id, final_id or "—"),
                "Revisado por": r.get("reviewed_by") or "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### 3 · Requisitos definitivos da demanda")
    validated = state.get("validated_skills") or []
    if validated:
        view = pd.DataFrame(validated)
        cols = [c for c in ["skill_name", "requirement_type", "confidence", "validated_by", "validated_at"] if c in view.columns]
        view = view[cols].copy()
        view.columns = ["Competência", "Tipo", "Confiança original", "Validada por", "Validada em"][:len(cols)]
        if "Confiança original" in view.columns:
            view["Confiança original"] = view["Confiança original"].astype(float).map(lambda x: f"{x:.0%}")
        st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma competência definitiva validada ainda.")

    if state.get("demand_validated"):
        st.success("Demanda validada: não há competências pendentes.")
        if st.button("Analisar capacidade da base →", type="primary"):
            st.session_state["show_real_capacity"] = True
        if st.session_state.get("show_real_capacity"):
            _render_capacity()
    else:
        st.caption("O botão de capacidade será habilitado quando todas as competências candidatas forem revisadas.")


def _edge_review(ctx, candidate_id, action, final_skill_id, requirement_type, notes):
    try:
        payload = {
            "candidate_id": candidate_id,
            "action": action,
            "requirement_type": requirement_type,
            "notes": notes or None,
        }
        if final_skill_id:
            payload["final_skill_id"] = final_skill_id
        with st.spinner("Gravando decisão humana no Supabase..."):
            result = ctx.edge.review(DEMAND_ID, ACTOR_ID, [payload])
        item = (result.get("results") or [{}])[0]
        if not item.get("ok", True):
            st.error(item.get("error") or "Não foi possível gravar a decisão.")
            return
        st.success("Decisão gravada e auditada.")
        st.rerun()
    except Exception as exc:
        st.error(f"Falha na revisão: {exc}")


def _render_legacy(ctx):
    """Preserva o fluxo anterior para demo local e conexão PostgreSQL direta."""
    header("EMPRESAS", "Demanda empresarial", "Transforme uma necessidade de contratação em competências e pipeline local.")
    company = ctx.repo.company("C001")
    st.subheader(company.company_name)
    a, b, c = st.columns(3)
    a.metric("Setor", company.sector); b.metric("Colaboradores", int(company.employees)); c.metric("Demanda demonstrativa", "20 vagas")
    persistent = getattr(ctx.repo, "is_persistent", False)
    st.info("Modo compatibilidade: demo local ou PostgreSQL direto.")
    saved = ctx.repo.get_demand(DEMAND_ID) if persistent else None
    default_text = saved.get("description") if saved else "Operar equipamentos industriais, acompanhar parâmetros de processo, seguir procedimentos de segurança, monitorar qualidade e registrar ocorrências."
    text = st.text_area("Descrição da função", default_text, height=150)
    if not persistent:
        if st.button("Analisar competências", type="primary"):
            st.session_state.alpha_analyzed = True; st.rerun()
        _render_demo(ctx, text)
        return
    st.warning("Para usar o novo fluxo visual por Edge Functions, configure SUPABASE_URL e SUPABASE_EDGE_KEY no ambiente.")


def _render_demo(ctx, text):
    if st.session_state.alpha_analyzed:
        df = ctx.skills.extract_demo(text)
        st.success("Análise simulada concluída.")
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("Validar conjunto de competências"):
            st.session_state.alpha_validated = True; st.rerun()
    if st.session_state.alpha_validated:
        _render_capacity()


def _render_capacity():
    st.markdown("### Capacidade local")
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Prontos agora", 6), ("Próximos", 19), ("Qualificáveis ≤80h", 31), ("Distância elevada", 144)]):
        col.metric(label, value)
    st.info(
        "**Trilha recomendada: 60h** — Controle de Processo, Segurança Industrial e Operação de Equipamentos. "
        "**31 participantes** poderiam atingir ≥75% dos requisitos estruturados."
    )
