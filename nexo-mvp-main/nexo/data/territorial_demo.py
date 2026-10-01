"""Dados demonstrativos do Perfil Gestor.

Os valores abaixo existem apenas para demonstrar UX e lógica analítica do MVP.
As labels de fonte indicam os conectores previstos, não que os números tenham
sido carregados das fontes oficiais em tempo real.
"""

MUNICIPALITY = {
    "name": "Paulínia",
    "state": "SP",
    "ibge_code": "3536505",
}

TERRITORIAL_KPIS = {
    "population": 116_400,
    "working_age": 83_900,
    "economically_active": 69_600,
    "formal_jobs": 54_800,
    "formalization_rate": 78.7,
    "avg_formal_wage": 4_980,
}

AGE_GENDER = [
    {"Faixa etária": "18–24", "Mulheres": 5_900, "Homens": 6_400},
    {"Faixa etária": "25–34", "Mulheres": 9_600, "Homens": 10_300},
    {"Faixa etária": "35–44", "Mulheres": 10_100, "Homens": 10_800},
    {"Faixa etária": "45–54", "Mulheres": 7_200, "Homens": 7_700},
    {"Faixa etária": "55–64", "Mulheres": 4_500, "Homens": 4_300},
]

EDUCATION = [
    {"Escolaridade": "Fundamental", "Pessoas": 11_900},
    {"Escolaridade": "Médio", "Pessoas": 35_700},
    {"Escolaridade": "Técnico", "Pessoas": 8_600},
    {"Escolaridade": "Superior", "Pessoas": 13_400},
]

CAGED_MONTHLY = [
    {"Mês": "Nov/25", "Admissões": 1_780, "Desligamentos": 1_690},
    {"Mês": "Dez/25", "Admissões": 1_510, "Desligamentos": 1_640},
    {"Mês": "Jan/26", "Admissões": 1_940, "Desligamentos": 1_760},
    {"Mês": "Fev/26", "Admissões": 2_020, "Desligamentos": 1_810},
    {"Mês": "Mar/26", "Admissões": 2_180, "Desligamentos": 1_950},
    {"Mês": "Abr/26", "Admissões": 2_110, "Desligamentos": 2_020},
    {"Mês": "Mai/26", "Admissões": 2_240, "Desligamentos": 2_030},
    {"Mês": "Jun/26", "Admissões": 2_330, "Desligamentos": 2_120},
    {"Mês": "Jul/26", "Admissões": 2_410, "Desligamentos": 2_170},
    {"Mês": "Ago/26", "Admissões": 2_360, "Desligamentos": 2_140},
]

FORMAL_SECTORS = [
    {"Setor": "Indústria de transformação", "Vínculos": 17_400, "Saldo 12m": 620},
    {"Setor": "Serviços", "Vínculos": 14_900, "Saldo 12m": 510},
    {"Setor": "Comércio", "Vínculos": 8_300, "Saldo 12m": 190},
    {"Setor": "Construção", "Vínculos": 6_200, "Saldo 12m": 430},
    {"Setor": "Logística e transporte", "Vínculos": 4_900, "Saldo 12m": 350},
    {"Setor": "Outros", "Vínculos": 3_100, "Saldo 12m": 80},
]

OCCUPATION_MOVEMENT = [
    {"Ocupação": "Operador de Processo", "Admissões 12m": 486, "Saldo 12m": 128, "Tendência": "↑"},
    {"Ocupação": "Assistente de Logística", "Admissões 12m": 421, "Saldo 12m": 96, "Tendência": "↑"},
    {"Ocupação": "Técnico de Manutenção", "Admissões 12m": 278, "Saldo 12m": 74, "Tendência": "↑"},
    {"Ocupação": "Auxiliar de Produção", "Admissões 12m": 692, "Saldo 12m": 61, "Tendência": "→"},
    {"Ocupação": "Assistente Administrativo", "Admissões 12m": 318, "Saldo 12m": 38, "Tendência": "→"},
    {"Ocupação": "Técnico de Qualidade", "Admissões 12m": 186, "Saldo 12m": 52, "Tendência": "↑"},
]

INVESTMENTS = [
    {
        "Projeto": "Expansão Bioindustrial", "Setor": "Química / biotecnologia", "Fase": "Licenciamento",
        "Investimento (R$ mi)": 250, "Empregos estimados": 180, "Horizonte": "12–18 meses",
        "Skills críticas": "Operação de processo; segurança; qualidade; manutenção", "Prioridade": "Alta",
    },
    {
        "Projeto": "Novo centro logístico", "Setor": "Logística", "Fase": "Anunciado",
        "Investimento (R$ mi)": 120, "Empregos estimados": 320, "Horizonte": "9–15 meses",
        "Skills críticas": "Logística; estoque; ERP; empilhadeira; dados", "Prioridade": "Alta",
    },
    {
        "Projeto": "Modernização de planta", "Setor": "Indústria", "Fase": "Implantação",
        "Investimento (R$ mi)": 85, "Empregos estimados": 95, "Horizonte": "6–10 meses",
        "Skills críticas": "Automação; controle de processo; manutenção; qualidade", "Prioridade": "Alta",
    },
    {
        "Projeto": "Hub de serviços digitais", "Setor": "Tecnologia / serviços", "Fase": "Prospecção",
        "Investimento (R$ mi)": 48, "Empregos estimados": 140, "Horizonte": "18–24 meses",
        "Skills críticas": "Dados; suporte; CRM; Power BI; atendimento", "Prioridade": "Média",
    },
]

INVESTMENT_SKILL_DEMAND = [
    {"Skill": "Operação de Processo", "Demanda projetada": 145},
    {"Skill": "Segurança Industrial", "Demanda projetada": 132},
    {"Skill": "Logística Operacional", "Demanda projetada": 118},
    {"Skill": "ERP", "Demanda projetada": 104},
    {"Skill": "Manutenção Preventiva", "Demanda projetada": 96},
    {"Skill": "Controle de Qualidade", "Demanda projetada": 82},
    {"Skill": "Power BI", "Demanda projetada": 55},
]

VACANCY_KPIS = {
    "active_30d": 1284,
    "new_7d": 318,
    "companies": 146,
    "deduplicated": 224,
}

VACANCY_BY_OCCUPATION = [
    {"Ocupação": "Produção e operação", "Vagas": 312},
    {"Ocupação": "Logística", "Vagas": 248},
    {"Ocupação": "Administrativo", "Vagas": 174},
    {"Ocupação": "Manutenção", "Vagas": 122},
    {"Ocupação": "Qualidade", "Vagas": 96},
    {"Ocupação": "Atendimento / comercial", "Vagas": 184},
    {"Ocupação": "Dados / tecnologia", "Vagas": 72},
    {"Ocupação": "Outras", "Vagas": 76},
]

VACANCY_SKILLS = [
    {"Skill": "Excel", "Vagas": 286, "Variação 60d": "+18%"},
    {"Skill": "ERP", "Vagas": 241, "Variação 60d": "+26%"},
    {"Skill": "Logística Operacional", "Vagas": 198, "Variação 60d": "+14%"},
    {"Skill": "Segurança Industrial", "Vagas": 176, "Variação 60d": "+21%"},
    {"Skill": "Controle de Processo", "Vagas": 153, "Variação 60d": "+31%"},
    {"Skill": "SAP", "Vagas": 128, "Variação 60d": "+12%"},
    {"Skill": "Controle de Qualidade", "Vagas": 121, "Variação 60d": "+17%"},
    {"Skill": "Power BI", "Vagas": 88, "Variação 60d": "+29%"},
]

VACANCY_SOURCES = [
    {"Fonte": "Páginas de carreiras empresariais", "Itens": 438, "Status": "Conector previsto"},
    {"Fonte": "Portais de emprego abertos/autorizados", "Itens": 392, "Status": "Conector previsto"},
    {"Fonte": "SINE / canais públicos", "Itens": 214, "Status": "Conector previsto"},
    {"Fonte": "Diários oficiais / comunicados", "Itens": 86, "Status": "Conector previsto"},
    {"Fonte": "Demandas declaradas ao NEXO", "Itens": 154, "Status": "Disponível no MVP"},
]

SOURCE_CATALOG = [
    {"Fonte": "IBGE / SIDRA", "Uso no NEXO": "Demografia, idade, sexo, escolaridade e estrutura territorial", "Periodicidade": "Conforme indicador", "Status": "Conector planejado"},
    {"Fonte": "RAIS", "Uso no NEXO": "Estoque de vínculos, remuneração, estabelecimentos, setor e ocupação", "Periodicidade": "Anual", "Status": "Conector planejado"},
    {"Fonte": "Novo CAGED", "Uso no NEXO": "Admissões, desligamentos, saldo e dinâmica recente", "Periodicidade": "Mensal", "Status": "Conector planejado"},
    {"Fonte": "NEXO Empresas", "Uso no NEXO": "Demandas declaradas e competências validadas", "Periodicidade": "Contínua", "Status": "MVP funcional"},
]
