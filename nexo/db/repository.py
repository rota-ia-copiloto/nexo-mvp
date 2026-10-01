from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd

class Repository(ABC):
    is_persistent: bool = False

    @abstractmethod
    def table(self, name: str) -> pd.DataFrame: ...

    def participant(self, participant_id: str) -> pd.Series:
        df=self.table("participants")
        return df.loc[df.participant_id==participant_id].iloc[0]

    def company(self, company_id: str) -> pd.Series:
        df=self.table("companies")
        return df.loc[df.company_id==company_id].iloc[0]

    def outcome(self, outcome_id: str) -> pd.Series:
        df=self.table("outcomes")
        return df.loc[df.outcome_id==outcome_id].iloc[0]

    def get_demand(self, demand_id: str):
        return None

    def get_demand_skills(self, demand_id: str) -> pd.DataFrame:
        return pd.DataFrame()


    def get_skill_candidates(self, demand_id: str) -> pd.DataFrame:
        return pd.DataFrame()

    def save_skill_candidates(self, demand_id: str, candidates: list[dict], actor_id: str):
        raise NotImplementedError("Este backend não oferece persistência de candidatos de skills.")

    def review_skill_candidates(self, demand_id: str, reviews: list[dict], actor_id: str):
        raise NotImplementedError("Este backend não oferece revisão de candidatos de skills.")


    def get_embedding_documents(self, embedding_model: str, only_missing: bool = True) -> pd.DataFrame:
        return pd.DataFrame()

    def update_skill_embeddings(self, records: list[dict]):
        raise NotImplementedError("Este backend não oferece persistência vetorial.")

    def semantic_skill_search(self, embedding: list[float], threshold: float = 0.42, count: int = 3, embedding_model: str = "text-embedding-3-small") -> list[dict]:
        return []

    def save_demand(self, **kwargs):
        raise NotImplementedError("Este backend não oferece persistência de demandas.")

    def save_demand_skills(self, demand_id: str, skills: list[dict], actor_id: str):
        raise NotImplementedError("Este backend não oferece persistência de skills de demanda.")

    def validate_demand_skills(self, demand_id: str, validations: list[dict], actor_id: str):
        raise NotImplementedError("Este backend não oferece persistência de validação.")
