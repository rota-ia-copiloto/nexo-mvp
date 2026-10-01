from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from .embeddings import EmbeddingService

try:
    from openai import OpenAI
except ImportError:  # permits local/domain tests before optional SDK install
    OpenAI = None

PROMPT_VERSION = "skills_v1"


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


@dataclass
class TaxonomyMatch:
    skill_id: str | None
    skill_name: str
    score: float
    method: str


class SkillExtractionService:
    """LLM extraction + deterministic normalization against the NEXO taxonomy.

    The model extracts *raw competency concepts*. The model never decides which
    canonical NEXO skill becomes definitive. Canonicalization is performed by
    deterministic taxonomy matching and the company must review the candidate.
    """

    def __init__(self, repo, api_key: str | None = None, model: str | None = None):
        self.repo = repo
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        if self.api_key and OpenAI is None:
            raise RuntimeError("Pacote openai não instalado. Execute pip install -r requirements.txt.")
        self.client = OpenAI(api_key=self.api_key) if (self.api_key and OpenAI is not None) else None
        self.embeddings = EmbeddingService(repo, api_key=self.api_key)

    @property
    def enabled(self) -> bool:
        return bool(self.client)

    def _taxonomy_rows(self) -> list[dict[str, Any]]:
        skills = self.repo.table("skills")
        try:
            aliases = self.repo.table("skill_aliases")
        except Exception:
            aliases = None

        result = []
        for row in skills.to_dict("records"):
            result.append({
                "skill_id": row["skill_id"],
                "skill_name": row["skill_name"],
                "alias": row["skill_name"],
                "normalized": normalize_text(row["skill_name"]),
            })
        if aliases is not None and not aliases.empty:
            skill_names = dict(zip(skills.skill_id, skills.skill_name))
            for row in aliases.to_dict("records"):
                result.append({
                    "skill_id": row["skill_id"],
                    "skill_name": skill_names.get(row["skill_id"], row["skill_id"]),
                    "alias": row["alias"],
                    "normalized": normalize_text(row["alias"]),
                })
        return result

    def _match_taxonomy_with_semantic(self, raw_term: str) -> tuple[TaxonomyMatch, list[dict[str, Any]]]:
        target = normalize_text(raw_term)
        rows = self._taxonomy_rows()
        if not target:
            return TaxonomyMatch(None, raw_term, 0.0, "none"), []

        exact = [r for r in rows if r["normalized"] == target]
        if exact:
            r = exact[0]
            return TaxonomyMatch(r["skill_id"], r["skill_name"], 1.0, "exact_alias"), []

        best = None
        best_score = 0.0
        for r in rows:
            score = SequenceMatcher(None, target, r["normalized"]).ratio()
            tset, rset = set(target.split()), set(r["normalized"].split())
            if tset and rset:
                overlap = len(tset & rset) / max(len(tset), len(rset))
                score = max(score, overlap * 0.95)
                if len(rset) == 1:
                    token = next(iter(rset))
                    # Preserve strong handling for compact technology tokens/acronyms
                    # (ERP, SAP, SQL, Excel), but do not let generic nouns such as
                    # "inventário" bypass semantic retrieval merely by containment.
                    if token in tset and (len(token) <= 5 or token in {"excel", "python"}):
                        score = max(score, 0.94)
            if score > best_score:
                best, best_score = r, score

        # High lexical confidence is enough; otherwise semantic retrieval can
        # rescue paraphrases that share meaning but not wording.
        if best and best_score >= 0.86:
            return TaxonomyMatch(best["skill_id"], best["skill_name"], round(best_score, 4), "fuzzy_alias"), []

        semantic = []
        if self.embeddings.enabled:
            try:
                semantic = self.embeddings.semantic_candidates(raw_term, threshold=0.45, count=3)
            except Exception:
                # Semantic retrieval is an enhancement, not a single point of failure.
                semantic = []
        if semantic:
            top = semantic[0]
            semantic_score = float(top["similarity"] or 0)
            # Prefer semantic mapping when it has a meaningful lead.
            if semantic_score >= max(0.55, best_score + 0.03):
                return TaxonomyMatch(top["skill_id"], top["skill_name"], round(semantic_score, 4), "semantic_pgvector"), semantic

        if best and best_score >= 0.58:
            return TaxonomyMatch(best["skill_id"], best["skill_name"], round(best_score, 4), "fuzzy_alias"), semantic
        return TaxonomyMatch(None, raw_term, round(best_score, 4), "unmapped"), semantic

    def _match_taxonomy(self, raw_term: str) -> TaxonomyMatch:
        """Backward-compatible taxonomy match used by existing tests/callers."""
        match, _ = self._match_taxonomy_with_semantic(raw_term)
        return match

    def _extract_with_llm(self, description: str, occupation_name: str | None = None) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError(
                "OPENAI_API_KEY não configurada. Defina a chave no ambiente do servidor para ativar a extração real."
            )

        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "occupation_summary": {"type": "string"},
                "skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "raw_term": {"type": "string"},
                            "requirement_type": {
                                "type": "string",
                                "enum": ["mandatory", "desired", "suggested"],
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "evidence_excerpt": {"type": "string"},
                            "rationale": {"type": "string"},
                        },
                        "required": [
                            "raw_term",
                            "requirement_type",
                            "confidence",
                            "evidence_excerpt",
                            "rationale",
                        ],
                    },
                },
            },
            "required": ["occupation_summary", "skills"],
        }

        instructions = (
            "Você é um extrator de competências ocupacionais para uma política pública de qualificação. "
            "Extraia somente competências, conhecimentos, certificações ou capacidades realmente sustentadas pelo texto. "
            "Não invente requisitos. Distinga mandatory quando o texto indicar requisito essencial, desired quando indicar preferência, "
            "e suggested quando a competência for inferida com cautela a partir das atividades. "
            "evidence_excerpt deve reproduzir apenas um trecho curto do texto de origem. "
            "confidence representa confiança na EXTRAÇÃO do conceito, não adequação de candidato nem chance de contratação."
        )
        context = f"Ocupação informada: {occupation_name or 'não informada'}\nDescrição:\n{description}"

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=context,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "nexo_skill_extraction",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        return json.loads(response.output_text)

    def extract(self, description: str, occupation_name: str | None = None) -> list[dict[str, Any]]:
        description = (description or "").strip()
        if len(description) < 20:
            raise ValueError("A descrição é curta demais para uma extração confiável.")

        payload = self._extract_with_llm(description, occupation_name)
        candidates = []
        seen = set()
        for item in payload.get("skills", []):
            raw = item["raw_term"].strip()
            if not raw:
                continue
            taxonomy, semantic_candidates = self._match_taxonomy_with_semantic(raw)
            dedupe_key = taxonomy.skill_id or normalize_text(raw)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            # Combined confidence preserves the LLM's extraction confidence while
            # penalizing weak canonicalization. Human review is still mandatory.
            extraction_conf = float(item["confidence"])
            canonical_conf = taxonomy.score if taxonomy.skill_id else 0.35
            combined = round(min(1.0, extraction_conf * (0.65 + 0.35 * canonical_conf)), 4)

            candidates.append({
                "raw_term": raw,
                "proposed_skill_id": taxonomy.skill_id,
                "proposed_label": taxonomy.skill_name,
                "requirement_type": item["requirement_type"],
                "confidence": combined,
                "evidence_excerpt": item["evidence_excerpt"],
                "rationale": item["rationale"],
                "extraction_model": self.model,
                "prompt_version": PROMPT_VERSION,
                "normalization_method": taxonomy.method,
                "normalization_score": taxonomy.score,
                "semantic_candidates": semantic_candidates,
            })
        return candidates
