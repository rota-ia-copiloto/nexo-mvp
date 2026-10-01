SKILLS = [
    ("SK001","Microsoft Excel","Digital"),("SK002","Gestão de Estoque","Técnica"),("SK003","ERP","Digital"),
    ("SK004","SAP","Digital"),("SK005","Logística Operacional","Técnica"),("SK006","Segurança Industrial","Técnica"),
    ("SK007","Operação de Equipamentos","Técnica"),("SK008","Controle de Processo","Técnica"),("SK009","Leitura de Procedimentos","Técnica"),
    ("SK010","Monitoramento de Processos","Técnica"),("SK011","Controle de Qualidade","Técnica"),("SK012","Trabalho em Equipe","Transversal"),
    ("SK013","Resolução de Problemas","Transversal"),("SK014","Atendimento","Transversal"),("SK015","Rotinas Administrativas","Técnica"),
    ("SK016","Power BI","Digital"),("SK017","SQL","Digital"),("SK018","Python","Digital"),("SK019","Manutenção Preventiva","Técnica"),
    ("SK020","Leitura Técnica","Técnica"),("SK021","Hidráulica","Técnica"),("SK022","Pneumática","Técnica"),("SK023","NR-10","Certificação"),
    ("SK024","NR-12","Certificação"),("SK025","Metrologia","Técnica"),("SK026","Inspeção","Técnica"),("SK027","5S","Técnica"),
    ("SK028","Lean","Técnica"),("SK029","Comunicação","Transversal"),("SK030","Organização","Transversal"),("SK031","Planejamento","Transversal"),
    ("SK032","Gestão do Tempo","Transversal"),("SK033","Pacote Office","Digital"),("SK034","Análise de Dados","Digital"),
    ("SK035","Dashboards","Digital"),("SK036","Estatística Básica","Digital"),("SK037","CRM","Digital"),("SK038","Negociação","Transversal"),
    ("SK039","Vendas","Técnica"),("SK040","Logística Reversa","Técnica"),("SK041","Inventário","Técnica"),("SK042","Compras","Técnica"),
    ("SK043","Faturamento","Técnica"),("SK044","Documentação","Técnica"),("SK045","Gestão de Indicadores","Técnica"),
    ("SK046","Boas Práticas de Fabricação","Técnica"),("SK047","Raciocínio Lógico","Transversal")
]

OCCUPATIONS=[("O001","Assistente de Logística"),("O002","Operador de Processo"),("O003","Técnico de Manutenção"),("O004","Assistente Administrativo"),("O005","Analista de Dados Jr."),("O006","Auxiliar de Produção"),("O007","Técnico de Qualidade"),("O008","Atendimento ao Cliente")]

COMPANIES=[("C001","Empresa Alfa","Indústria Química",850),("C002","Beta Logística","Logística",420),("C003","Gamma Serviços","Serviços Empresariais",310),("C004","Delta Química","Indústria Química",620),("C005","Épsilon Tech","Tecnologia",180),("C006","Zeta Manutenção","Manutenção Industrial",260),("C007","Eta Comércio","Comércio",140),("C008","Theta Manufatura","Manufatura",530),("C009","Iota Serviços","Serviços Empresariais",220),("C010","Kappa Log","Logística",390),("C011","Lambda Química","Indústria Química",710),("C012","Mu Digital","Tecnologia",160),("C013","Nu Comércio","Comércio",125),("C014","Xi Manutenção","Manutenção Industrial",205),("C015","Omicron Manufatura","Manufatura",480),("C016","Pi Serviços","Serviços Empresariais",195),("C017","Rho Química","Indústria Química",640),("C018","Sigma Log","Logística",350)]

OCC_SKILLS={
 "O001":[("SK001",2,.25),("SK002",2,.25),("SK003",2,.25),("SK005",2,.25)],
 "O002":[("SK006",3,.18),("SK007",3,.18),("SK008",3,.18),("SK009",2,.14),("SK010",2,.12),("SK011",2,.10),("SK012",2,.05),("SK013",2,.05)],
 "O003":[("SK019",3,.22),("SK020",3,.18),("SK021",2,.15),("SK022",2,.15),("SK023",2,.15),("SK013",2,.15)],
 "O004":[("SK001",2,.25),("SK015",3,.30),("SK029",2,.15),("SK030",2,.15),("SK033",2,.15)],
 "O005":[("SK016",2,.22),("SK017",2,.22),("SK018",1,.14),("SK034",2,.18),("SK035",2,.14),("SK047",3,.10)],
 "O006":[("SK006",2,.20),("SK007",2,.20),("SK009",2,.15),("SK011",2,.15),("SK012",2,.15),("SK027",2,.15)],
 "O007":[("SK011",3,.25),("SK025",2,.15),("SK026",2,.20),("SK044",2,.15),("SK045",2,.15),("SK013",2,.10)],
 "O008":[("SK014",3,.30),("SK029",3,.20),("SK037",2,.15),("SK038",2,.10),("SK030",2,.10),("SK013",2,.15)]
}
COURSES=[("CRS001","Operações Logísticas + ERP",40,"O001"),("CRS002","Trilha Operador de Processo",60,"O002"),("CRS003","Manutenção Industrial Essencial",80,"O003"),("CRS004","Excel e Rotinas Administrativas",32,"O004"),("CRS005","Dados com Power BI e SQL",72,"O005"),("CRS006","Fundamentos de Produção",40,"O006"),("CRS007","Qualidade Industrial",48,"O007"),("CRS008","Atendimento e CRM",32,"O008"),("CRS009","NR-10 Preparatório",24,"O003"),("CRS010","Excel Intermediário",20,"O001"),("CRS011","Introdução ao SAP",24,"O001"),("CRS012","Comunicação e Trabalho em Equipe",16,"O008")]
COURSE_SKILLS={"CRS001":[("SK002",1),("SK003",2),("SK005",2)],"CRS002":[("SK008",2),("SK006",2),("SK007",2)],"CRS003":[("SK019",2),("SK020",2),("SK021",1),("SK022",1)],"CRS004":[("SK001",2),("SK015",2),("SK033",1)],"CRS005":[("SK016",2),("SK017",2),("SK034",2)],"CRS006":[("SK006",1),("SK007",1),("SK009",1),("SK027",1)],"CRS007":[("SK011",2),("SK025",1),("SK026",2)],"CRS008":[("SK014",2),("SK037",2),("SK029",1)],"CRS009":[("SK023",2)],"CRS010":[("SK001",1)],"CRS011":[("SK004",1),("SK003",1)],"CRS012":[("SK029",1),("SK012",1)]}
JOB_COUNTS={"O001":24,"O002":20,"O003":15,"O004":12,"O005":11,"O006":10,"O007":10,"O008":10}
SKILL_DEMAND_COUNTS={"Microsoft Excel":48,"Logística Operacional":39,"ERP":34,"Segurança Industrial":31,"Gestão de Estoque":29,"Controle de Processo":27,"Trabalho em Equipe":25,"Controle de Qualidade":23,"Power BI":19,"SAP":17}
GAP_COUNTS={"ERP":68,"SAP":52,"Logística Operacional":47,"Segurança Industrial":41,"Power BI":29,"Controle de Processo":27}
NEARBY_BY_OCC={"O001":31,"O002":18,"O003":9,"O004":46,"O005":16,"O006":32,"O007":14,"O008":42}
