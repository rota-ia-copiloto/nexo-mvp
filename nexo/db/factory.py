from nexo.config import settings
from .demo_repository import DemoRepository
from .postgres_repository import PostgresRepository

def get_repository():
    if settings.data_backend.lower() in {"postgres","supabase"}:
        return PostgresRepository()
    return DemoRepository()
