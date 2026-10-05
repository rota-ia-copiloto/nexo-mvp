# NEXO Qualifica+ — CPSI MVP v1.2

MVP demonstrativo para submissão ao CPSI de qualificação profissional de Itajaí.

## Atualização v1.2 — inteligência ocupacional ampliada

A tela **Demanda & Competências** passou a usar uma base ocupacional local derivada da matriz oficial CBO/QBQ fornecida ao projeto.

### Base operacional carregada
- 2.673 ocupações CBO/QBQ
- perfil e síntese ocupacional
- conhecimentos priorizados
- habilidades priorizadas
- atitudes priorizadas
- nível de qualificação QBQ quando disponível

Arquivo: `occupational_knowledge.json.gz`

### Fontes de referência da arquitetura
- CBO — Classificação Brasileira de Ocupações / MTE
- QBQ — Quadro Brasileiro de Qualificações / MTE
- GBO — Guia Brasileiro de Ocupações / MTE-OIT
- CNCT — Catálogo Nacional de Cursos Técnicos / MEC
- Monitor de Profissões — MEC/ABDI
- ESCO — European Skills, Competences, Qualifications and Occupations

No MVP v1.2, **CBO/QBQ são a base operacional embarcada**. CNCT é usado para referências formativas demonstrativas. GBO, Monitor de Profissões e ESCO estão explicitados como camadas complementares de mercado, formação e enriquecimento/interoperabilidade previstas para o piloto.

## Fluxo do MVP

Demanda → ocupação CBO → competências QBQ → validação humana → trajetória → intervenção → outcome → decisão.

## Arquivos necessários no Streamlit

Na raiz do repositório:

- `app.py`
- `occupational_knowledge.json.gz`
- `requirements.txt`
- `README.md`

## Executar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Observação

Dados de participantes, empresas, coortes e resultados continuam sintéticos. A base ocupacional CBO/QBQ usada para ampliar o motor de demanda e competências é de referência oficial e foi transformada em formato compacto para o protótipo.
