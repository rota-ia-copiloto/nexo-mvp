# NEXO Qualifica+ — Radar de Vagas demonstrativo

Pacote consolidado para integrar o Radar ao menu do NEXO mantendo intactos
os blocos funcionais anteriores.

## Arquivos
- `app.py`: cópia consolidada da versão de trabalho mais recente disponível
  nesta conversa (MVP v1.6), adicionando exclusivamente import, item de menu
  e roteador da página do Radar.
- `nexo_radar_vagas.py`: nova página com simulação de coleta HTML, parsing,
  campos normalizados, filtros, sugestões de skills e exportação CSV.
- `PATCH_SEGURO_APP_ATUAL.txt`: instruções para fazer a integração sobre um
  app.py do GitHub que possa ter alterações mais recentes.

## Como publicar no GitHub
1. Faça backup do `app.py` que já está no repositório (pode salvar ou usar
   o histórico de commits).
2. Faça upload de `nexo_radar_vagas.py` **na raiz**, junto de `app.py`.
3. Escolha uma das alternativas:
   - **Segura/recomendada:** edite o `app.py` atual usando
     `PATCH_SEGURO_APP_ATUAL.txt` (três mudanças pequenas).
   - **Substituição pronta:** somente se o `app.py` atual for a mesma versão
     v1.6 usada como referência, substitua-o pelo `app.py` deste pacote.
4. Não substitua `occupational_knowledge.json.gz`, `schema.sql`,
   `requirements.txt` nem outros arquivos do repositório.
5. Commit changes; depois verifique o aplicativo.

O arquivo `nexo_radar_vagas_demo.py` já enviado é um executável de demonstração
isolado; pode permanecer no repositório, mas o app integrado não depende dele.

## Limitações
Os registros de vagas são inteiramente sintéticos. O programa não faz
scraping da web, não usa dados pessoais reais e não persiste no Supabase.
A integração com o portal real dependerá de autorização/conformidade,
API ou coletor validado e conectores de dados.

## Testes
A alteração do arquivo principal foi comparada programaticamente com a
versão de trabalho utilizada como origem. Os módulos foram compilados e
as rotinas de parsing foram testadas com HTML fictício; a interface visual
completa depende do ambiente Streamlit de implantação.
