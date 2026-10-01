from __future__ import annotations

import pandas as pd
from .skill_extraction import SkillExtractionService

ALPHA_SKILLS=[
 ("Segurança Industrial","Obrigatória",.98),("Operação de Equipamentos","Obrigatória",.96),("Controle de Processo","Obrigatória",.93),("Leitura de Procedimentos","Obrigatória",.91),("Monitoramento de Processos","Obrigatória",.88),("Controle de Qualidade","Obrigatória",.90),("Trabalho em Equipe","Desejável",.86),("Resolução de Problemas","Revisar",.72)
]

class SkillsService:
    def __init__(self, repo=None):
        self.repo = repo
        self.extractor = SkillExtractionService(repo) if repo is not None else None

    @property
    def llm_enabled(self) -> bool:
        return bool(self.extractor and self.extractor.enabled)

    def extract_real(self, text: str, occupation_name: str | None = None) -> list[dict]:
        if not self.extractor:
            raise RuntimeError("SkillsService foi criado sem repository.")
        return self.extractor.extract(text, occupation_name)

    def extract_demo(self,text:str)->pd.DataFrame:
        return pd.DataFrame(ALPHA_SKILLS,columns=["Competência","Classificação","Confiança"])
