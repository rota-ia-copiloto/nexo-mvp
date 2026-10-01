from __future__ import annotations

QUALIFICATION_DEMAND = [
    {"Ocupação":"Operador Logístico","Empresas demandantes":18,"Vagas":126,"Competências requeridas":"WMS; segurança; estoque","Gap estimado":"Alto","Prioridade":"Crítica"},
    {"Ocupação":"Soldador","Empresas demandantes":9,"Vagas":74,"Competências requeridas":"MIG/MAG; leitura técnica; segurança","Gap estimado":"Médio","Prioridade":"Alta"},
    {"Ocupação":"Assistente Administrativo","Empresas demandantes":32,"Vagas":98,"Competências requeridas":"Excel; ERP; atendimento","Gap estimado":"Médio","Prioridade":"Alta"},
    {"Ocupação":"Eletricista Industrial","Empresas demandantes":11,"Vagas":61,"Competências requeridas":"NR-10; comandos; leitura de diagramas","Gap estimado":"Alto","Prioridade":"Crítica"},
]

COMPETENCY_MATRIX = {
    "Operador Logístico":[
        {"Competência":"WMS / sistemas de armazém","Tipo":"Técnica","Nível requerido":4,"Nível médio local":2,"Gap":2,"Fonte":"Vagas + empresas"},
        {"Competência":"Controle de estoque","Tipo":"Técnica","Nível requerido":4,"Nível médio local":3,"Gap":1,"Fonte":"Vagas + empresas"},
        {"Competência":"Segurança operacional","Tipo":"Técnica","Nível requerido":3,"Nível médio local":2,"Gap":1,"Fonte":"Empresas"},
        {"Competência":"Organização","Tipo":"Socioemocional","Nível requerido":4,"Nível médio local":3,"Gap":1,"Fonte":"Empresas"},
    ],
    "Soldador":[
        {"Competência":"Soldagem MIG/MAG","Tipo":"Técnica","Nível requerido":4,"Nível médio local":2,"Gap":2,"Fonte":"Vagas + empresas"},
        {"Competência":"Leitura e interpretação técnica","Tipo":"Técnica","Nível requerido":3,"Nível médio local":2,"Gap":1,"Fonte":"Empresas"},
        {"Competência":"Segurança do trabalho","Tipo":"Técnica","Nível requerido":4,"Nível médio local":3,"Gap":1,"Fonte":"Vagas"},
    ],
    "Assistente Administrativo":[
        {"Competência":"Excel","Tipo":"Técnica","Nível requerido":4,"Nível médio local":2,"Gap":2,"Fonte":"Vagas"},
        {"Competência":"ERP","Tipo":"Técnica","Nível requerido":3,"Nível médio local":1,"Gap":2,"Fonte":"Empresas"},
        {"Competência":"Atendimento","Tipo":"Socioemocional","Nível requerido":3,"Nível médio local":3,"Gap":0,"Fonte":"Empresas"},
    ],
    "Eletricista Industrial":[
        {"Competência":"NR-10","Tipo":"Técnica","Nível requerido":4,"Nível médio local":2,"Gap":2,"Fonte":"Vagas"},
        {"Competência":"Comandos elétricos","Tipo":"Técnica","Nível requerido":4,"Nível médio local":2,"Gap":2,"Fonte":"Empresas"},
        {"Competência":"Leitura de diagramas","Tipo":"Técnica","Nível requerido":3,"Nível médio local":2,"Gap":1,"Fonte":"Empresas"},
    ],
}

LEARNING_PATHS = [
    {"Gap":"WMS / sistemas de armazém","Objetivo de aprendizagem":"Operar rotinas básicas de WMS em recebimento, endereçamento e expedição","Experiência formativa":"Laboratório prático + simulação de fluxo","Instrumento de avaliação":"Pré/pós-teste + tarefa prática","Meta":"+25% no domínio","Validação no trabalho":"Feedback da empresa em 30 dias"},
    {"Gap":"Leitura e interpretação técnica","Objetivo de aprendizagem":"Interpretar desenhos e símbolos técnicos aplicados à produção","Experiência formativa":"Oficina prática de 12h","Instrumento de avaliação":"Exercício aplicado","Meta":"80% de acerto","Validação no trabalho":"Supervisor / checklist"},
    {"Gap":"Excel","Objetivo de aprendizagem":"Executar controles operacionais com fórmulas, filtros e tabelas","Experiência formativa":"Desafio prático orientado a casos","Instrumento de avaliação":"Planilha-problema","Meta":"+20% no desempenho","Validação no trabalho":"Amostra de tarefa real"},
]

FUNNEL = [
    {"Etapa":"Alcance","Pessoas":1000},
    {"Etapa":"Interesse","Pessoas":620},
    {"Etapa":"Inscrição","Pessoas":470},
    {"Etapa":"Ingresso","Pessoas":390},
    {"Etapa":"Participação","Pessoas":340},
    {"Etapa":"Conclusão","Pessoas":286},
    {"Etapa":"Encaminhamento","Pessoas":201},
    {"Etapa":"Inserção","Pessoas":148},
    {"Etapa":"Permanência 90d","Pessoas":121},
]

EXPERIMENTS = [
    {"Experimento":"Trilha logística orientada por demanda","Hipótese":"Trilha por competências + acompanhamento ativo aumenta conclusão e inserção","População":"Desempregados 18–44 interessados em logística","Comparador":"Coorte anterior","Status":"Em avaliação","Decisão":"Reformular"},
    {"Experimento":"Mobilização territorial noturna","Hipótese":"Oferta noturna reduz perda entre inscrição e ingresso","População":"Adultos trabalhadores / informais","Comparador":"Linha de base","Status":"Validado","Decisão":"Escalar"},
]

EXPERIMENT_RESULTS = [
    {"Indicador":"Conclusão","Baseline":62,"Meta":75,"Resultado":78,"Unidade":"%"},
    {"Indicador":"Inserção em até 90 dias","Baseline":28,"Meta":40,"Resultado":43,"Unidade":"%"},
    {"Indicador":"Permanência em 180 dias","Baseline":67,"Meta":75,"Resultado":72,"Unidade":"%"},
    {"Indicador":"Ganho de competências","Baseline":0,"Meta":20,"Resultado":24,"Unidade":"%"},
]

EQUITY_FUNNEL = [
    {"Etapa":"Inscrição","Mulheres 35–49":70,"Grupo comparador":72},
    {"Etapa":"Ingresso","Mulheres 35–49":58,"Grupo comparador":66},
    {"Etapa":"Conclusão","Mulheres 35–49":65,"Grupo comparador":81},
    {"Etapa":"Inserção","Mulheres 35–49":33,"Grupo comparador":48},
]

BARRIERS = [
    {"Barreira":"Horário incompatível","Registros":38,"Medida adotada":"Turma noturna + flexibilização","Status":"Em teste"},
    {"Barreira":"Cuidado de filhos/dependentes","Registros":27,"Medida adotada":"Reorganização de horários e apoio de rede","Status":"Planejada"},
    {"Barreira":"Transporte / distância","Registros":21,"Medida adotada":"Territorialização de turmas","Status":"Em teste"},
    {"Barreira":"Conectividade","Registros":16,"Medida adotada":"Alternativa presencial / offline","Status":"Ativa"},
]

ECONOMICS = {
    "pilot_cost": 402000,
    "participants": 340,
    "completers": 286,
    "inserted": 148,
    "retained_90": 121,
    "comparator_cost_per_participant": 1180,
    "comparator_completion": 62,
    "comparator_insertion": 28,
}

EMPLOYER_FEEDBACK = [
    {"Empresa":"Empresa Alfa","Ocupação":"Operador Logístico","Aderência":82,"Gap apontado":"WMS","Mudança realizada":"Módulo WMS ampliado + prática","Retorno":"Positivo"},
    {"Empresa":"Empresa Beta","Ocupação":"Assistente Administrativo","Aderência":76,"Gap apontado":"ERP","Mudança realizada":"Caso prático de ERP incorporado","Retorno":"Em validação"},
    {"Empresa":"Empresa Gama","Ocupação":"Eletricista Industrial","Aderência":84,"Gap apontado":"Leitura de diagramas","Mudança realizada":"Oficina técnica reforçada","Retorno":"Positivo"},
]
