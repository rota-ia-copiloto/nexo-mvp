from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class EdgeFunctionClient:
    """Small server-side client for the NEXO Supabase Edge Functions.

    The API key is never rendered in Streamlit. Configure it through an environment
    variable/secret in the deployment environment.
    """

    base_url: str
    api_key: str
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "EdgeFunctionClient | None":
        url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
        # Prefer a legacy anon JWT for verify_jwt Edge Functions; accept the modern
        # publishable variable too for deployments where the gateway supports it.
        key = (
            os.getenv("SUPABASE_EDGE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or ""
        )
        if not url or not key:
            return None
        return cls(url, key)

    def invoke(self, function_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/functions/v1/{function_name}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "apikey": self.api_key,
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
                msg = data.get("error") or body
            except Exception:
                msg = body
            raise RuntimeError(f"Supabase Edge Function {function_name} retornou HTTP {exc.code}: {msg}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Não foi possível acessar a Edge Function {function_name}: {exc.reason}") from exc

        if isinstance(data, dict) and data.get("ok") is False:
            raise RuntimeError(str(data.get("error") or f"Falha em {function_name}"))
        return data

    def state(self, demand_id: str) -> dict[str, Any]:
        return self.invoke("nexo-demand-state", {"demand_id": demand_id})


    def upsert_demand(
        self,
        demand_id: str,
        description: str,
        quantity: int,
        horizon: str,
        actor_id: str,
        company_id: str = "C001",
        occupation_id: str = "O002",
    ) -> dict[str, Any]:
        return self.invoke(
            "nexo-upsert-demand",
            {
                "demand_id": demand_id,
                "description": description,
                "quantity": int(quantity),
                "horizon": horizon,
                "actor_id": actor_id,
                "company_id": company_id,
                "occupation_id": occupation_id,
            },
        )

    def analyze_demand(
        self,
        demand_id: str,
        description: str,
        actor_id: str,
    ) -> dict[str, Any]:
        return self.invoke(
            "nexo-analyze-demand",
            {"demand_id": demand_id, "description": description, "actor_id": actor_id},
        )

    def review(self, demand_id: str, actor_id: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        return self.invoke(
            "nexo-review-demand-skills",
            {"demand_id": demand_id, "actor_id": actor_id, "decisions": decisions},
        )
