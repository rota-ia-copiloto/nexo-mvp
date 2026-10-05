# NEXO Qualifica+ — CPSI MVP v1

MVP demonstrativo para submissão ao CPSI de qualificação profissional de Itajaí.

## Tese do produto

O MVP testa o menor circuito integrado necessário para demonstrar a hipótese de inovação pública:

**demanda do mercado → competências → diagnóstico do participante → recomendação de trajetória → intervenção formativa → acompanhamento → outcome → feedback → nova decisão pública**.

O NEXO não é apresentado como LMS, portal de vagas ou ERP. A camada tecnológica existe para testar quatro motores integrados:

1. **Skills Intelligence** — traduz sinais do mercado em competências estruturadas e validadas;
2. **Adaptive Trajectory** — recomenda percursos explicáveis sob revisão humana;
3. **Learning-to-Outcome** — liga intervenção e aprendizagem aos resultados profissionais;
4. **Policy Experiment Engine** — compara intervenções e transforma evidências em decisão.

## Navegação do MVP

- Visão Geral
- Demanda & Competências
- Trajetórias
- Engenharia Educacional
- Experimentos & Outcomes

## O que funciona de verdade no protótipo

- entrada textual de demanda empresarial;
- extração determinística de competências como proxy reproduzível do futuro motor semântico;
- human-in-the-loop para validar, remapear ou rejeitar skills;
- gap analysis de participante vs. demanda;
- recomendação explicável de percurso;
- registro de decisão humana;
- blueprint de engenharia educacional por skill gap;
- registro longitudinal de eventos;
- Evidence Ledger com hash demonstrativo;
- comparação de duas coortes sintéticas e recomendação de continuidade/reformulação.

## Dados

Todos os dados são sintéticos e destinados somente à demonstração. O MVP não deve ser apresentado como evidência empírica de resultado.

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Pode ser publicado no Streamlit Community Cloud apontando o app para `app.py`.

## Próxima evolução para piloto CPSI

- PostgreSQL/Supabase para persistência real;
- pgvector e embeddings para Skills Intelligence;
- LLM/NLP com validação humana para extração e normalização de competências;
- autenticação e RBAC;
- integrações com fontes municipais/autorizadas;
- experiment management e indicadores calibrados após baseline;
- LGPD, logging, versionamento de modelos e trilha de auditoria completa.
