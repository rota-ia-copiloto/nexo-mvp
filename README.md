# NEXO — MVP modular

Versão modular do protótipo Streamlit, preservando a demo e preparando a persistência em PostgreSQL/Supabase.

## Arquitetura

- `nexo/pages`: UI Streamlit
- `nexo/services`: regras de domínio (skills, matching, outcomes)
- `nexo/db`: abstração de repositório e backends demo/PostgreSQL
- `nexo/data`: catálogo e geração sintética
- `sql/schema.sql`: schema mínimo PostgreSQL/Supabase
- `tests`: testes de integridade

## Rodar em modo demo

```bash
pip install -r requirements.txt
streamlit run app.py
```

O backend padrão é `demo`; não requer banco externo.

## Conectar PostgreSQL/Supabase

1. Execute `sql/schema.sql` no banco.
2. Copie `.env.example` para `.env` ou configure variáveis no ambiente.
3. Defina `NEXO_DATA_BACKEND=postgres`.
4. Defina `DATABASE_URL` com a connection string PostgreSQL do projeto Supabase.
5. Rode `streamlit run app.py`.

> Nesta versão, o `PostgresRepository` já lê as tabelas do banco. A próxima etapa é criar migrations/seeds e substituir os writes de `session_state` por comandos persistentes transacionais.

## Exportar o mesmo dataset da demo para seed

```bash
PYTHONPATH=. python scripts/export_demo_csv.py
```

Isso gera `seed_csv/*.csv` com o universo determinístico da demo. Ele pode ser importado para as tabelas do Supabase após a execução de `sql/schema.sql`.

## Estratégia de migração

- `NEXO_DATA_BACKEND=demo`: repositório em memória, preserva a demonstração.
- `NEXO_DATA_BACKEND=postgres`: as páginas e serviços passam a ler o PostgreSQL usando a mesma interface `Repository`.
- A camada de UI não conhece Pandas sintético vs. PostgreSQL: ela conversa apenas com o repositório e os serviços de domínio.
- Os próximos writes reais (cadastro, validação de skills, eventos, decisões do auditor) devem ser implementados como métodos transacionais do repositório, sem alterar as páginas.


## Supabase real — projeto NEXO

Projeto criado em São Paulo (`sa-east-1`).

- Project ref: `xmndxhvbmmlfhicamobl`
- Project URL: `https://xmndxhvbmmlfhicamobl.supabase.co`
- Schema aplicado e seed carregado no PostgreSQL real.
- Primeiro fluxo persistente: **Empresa → Demanda → Skills sugeridas → Validação humana → audit_log**.

Para o Streamlit usar o PostgreSQL real, configure no ambiente do servidor:

```bash
NEXO_DATA_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://...
```

Obtenha a connection string no painel do Supabase e mantenha-a apenas como secret do servidor. Não publique senha de banco no Git ou no frontend.

### Segurança atual

Todas as tabelas em `public` estão com RLS habilitado e sem políticas para `anon`/`authenticated`. Isso é intencional nesta fase: o MVP persistente usa conexão server-side. Quando adicionarmos Supabase Auth, criaremos políticas por perfil (empresa, gestor, participante e auditor).

## Extração real de competências com LLM

O fluxo de Empresa deixou de promover automaticamente sugestões para `demand_skills`.

1. A descrição da função é enviada ao modelo via OpenAI Responses API com Structured Outputs.
2. O modelo extrai termos, tipo de requisito, confiança, trecho de evidência e justificativa.
3. O NEXO normaliza os termos contra `skills` + `skill_aliases`.
4. Os resultados são gravados em `demand_skill_candidates` com `review_status='pending'`.
5. A empresa confirma, remapeia ou rejeita cada candidato.
6. Somente candidatos humanos `validated` são promovidos para `demand_skills`.
7. Cada extração e cada decisão humana gera um registro em `audit_log`.

Variáveis necessárias no servidor:

```bash
NEXO_DATA_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6-luna
```

`OPENAI_API_KEY` e a senha do banco devem permanecer somente em secrets do servidor.

## Busca semântica de skills com pgvector

O NEXO usa uma estratégia em camadas para normalizar termos empresariais:

1. alias exato;
2. similaridade textual/fuzzy;
3. embeddings + pgvector para paráfrases e linguagem não padronizada;
4. validação humana obrigatória.

Configuração:

```bash
OPENAI_API_KEY=...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Na primeira busca semântica em modo PostgreSQL, os embeddings ausentes da taxonomia são gerados em lote e persistidos em `skill_embedding_documents`. As consultas posteriores geram apenas o embedding do termo novo e recuperam os candidatos mais próximos por similaridade cosseno. O resultado semântico é apenas uma sugestão; a skill definitiva só entra em `demand_skills` após revisão da empresa.

## Calibração inicial da recuperação semântica

Após a primeira indexação real da taxonomia no pgvector (139/139 documentos), dois testes exploratórios foram usados para calibrar a apresentação da similaridade:

- `acompanhar parâmetros da linha de produção` → **Monitoramento de Processos** ≈ 0,64;
- `trabalhar com sistemas integrados de gestão empresarial` → **ERP** ≈ 0,74, com **SAP** como alternativa secundária ≈ 0,52.

Faixas iniciais do MVP (a validar durante o CPSI):

- **≥ 0,60 — Forte**: candidato semanticamente consistente;
- **0,50–0,599 — Moderada**: alternativa plausível, exige revisão humana;
- **0,45–0,499 — Fraca**: alternativa exploratória;
- **< 0,45 — Insuficiente**: não exibir como candidato sem outro sinal.

Essas faixas são heurísticas experimentais, não probabilidades nem critérios automáticos de decisão. A empresa continua sendo responsável por validar, remapear ou rejeitar cada competência.
