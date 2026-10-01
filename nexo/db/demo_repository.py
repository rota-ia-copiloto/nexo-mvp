import pandas as pd
from nexo.config import settings
from nexo.data.demo_factory import make_demo_data
from .repository import Repository

class DemoRepository(Repository):
    def __init__(self):
        self._data=make_demo_data(settings.random_seed)
    def table(self,name:str)->pd.DataFrame:
        value=self._data.get(name)
        if not isinstance(value,pd.DataFrame):
            raise KeyError(f"Tabela demo inexistente: {name}")
        return value.copy()
