# Arquitetura inicial — S01 de Gustavo

## Dependências

~~~mermaid
flowchart LR
  CLI[CLI: parâmetros e saída] --> P[Pipeline]
  P --> R[Coletor de releases/tags]
  P --> C[Coletor de commits]
  R --> N[Normalização para domínio]
  C --> N
  N --> M[Métricas puras]
  M --> A[Análise e relatório]
  P --> A
  R --> G[GitHubClient: paginação]
  C --> G
  G --> T[Transport]
  T --> H[HTTP direto]
  T --> S[Snapshot offline]
~~~

`domain.py` concentra contratos sem dependências externas, com IDs explícitos
e timestamps timezone-aware em UTC. Coletores fazem a aquisição;
`normalization.py` adapta payloads REST para os contratos; métricas recebem
objetos de domínio e `analysis.report` projeta resultados para JSON.
`pipeline.run` coordena sem persistir; a CLI valida a configuração e grava
somente após sucesso.

A separação aplica responsabilidade única e inversão de dependência na fronteira HTTP. Há transportes de rede e snapshot, sem framework de injeção ou SDK GitHub.

## Contratos para integração

| Contrato | Conteúdo / obrigação |
|---|---|
| `Transport.get(url)` | `Response(data, headers)`; headers em minúsculas. Falhas geram exceção, nunca lista vazia. |
| `GitHubClient.pages(path, params)` | Páginas por `Link`, rejeitando ciclos e links externos. |
| `Window` | Intervalo com timezone `[start, end)`. Admite testes curtos; protocolo real deve fixar doze meses. |
| `ReleaseCatalog` | Branch/SHA observado, histórico, variantes na janela e exclusões. Histórico preserva `sha=None` para ref não resolvida. |
| `ReleaseChanges` | Release, antecessora, commits e eventual motivo de exclusão. |
| `LeadTimeResult` | Medianas em horas ou `None`, quantidades total/utilizada e exclusões por motivo. |
| `Repository` | ID, nome completo, default branch/SHA, estrelas, linguagem e data de criação UTC. |
| `Release` | ID, tag, SHA resolvido quando disponível, data de publicação UTC e metadados. |
| `Commit` | SHA, `author.date` UTC quando válido e mensagem. |
| `WorkflowRun` | IDs do run/workflow, branch, evento, conclusão e timestamps UTC. |
| `normalization.py` | Conversores de payloads REST para contratos validados do domínio. |
| `analysis.report` | Montagem da saída JSON a partir dos contratos e métricas. |
| JSON | `schema_version=1`; datas ISO 8601, unidades nos nomes e origem explícita. |

Lucas pode decorar/substituir `Transport` com cache, rate limit e retentativas (#95/#96). Davi pode chamar `pipeline.run` para os elegíveis e integrar funil (#97/#106). Runs e demais métricas devem usar os mesmos contratos de datas, exclusões e funções puras.

`configuration.py` carrega os arquivos JSON antes de executar. A configuração
do estudo bloqueia chamadas de rede até a janela oficial ser preenchida e
aprovada; `config/amostra.json` executa um repositório sintético por snapshot,
sem token ou fallback de rede.

## Decisões a ratificar no protocolo

1. Congelar o SHA do default branch e verificar ancestralidade. É o estado observado na coleta, não uma reconstrução histórica.
2. Ordenar releases por `published_at` e ID em empates. Principal e variante com pré-releases possuem cadeias próprias.
3. Percorrer histórico anterior ao fim da janela para não depender da ordem do endpoint. O custo aumenta com o histórico; cache fica no transporte.
4. Preservar a posição de releases com referência 404. Excluir essa release e a comparação seguinte que depender dela, sem saltar para antecessora mais antiga.
5. Excluir toda a release quando qualquer commit tem data inválida ou posterior à publicação, preservando os motivos.
6. Deduplicar releases por ID, tags por nome e commits por SHA dentro do compare. O mesmo commit em releases diferentes segue a definição por pares commit-release.
7. 404 esperado gera exclusão; rate limit, autenticação e truncamento interrompem a coleta. Recuperação operacional pertence a #95/#96.
8. `None` não significa zero nem Elite. CFR, recuperação e classificação DORA ainda não pertencem a este recorte.

O cálculo segue a RQ02 do enunciado. Compare paginado segue a [documentação REST do GitHub](https://docs.github.com/en/rest/commits/commits#compare-two-commits). As políticas complementares precisam de revisão do trio antes da coleta.
