import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    data_backend: str = os.getenv("NEXO_DATA_BACKEND", "demo")
    database_url: str | None = os.getenv("DATABASE_URL")
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_key: str | None = os.getenv("SUPABASE_ANON_KEY")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    random_seed: int = int(os.getenv("NEXO_RANDOM_SEED", "42"))

settings = Settings()
