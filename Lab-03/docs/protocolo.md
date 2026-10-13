# Protocolo do estudo — Lab 03 (Issue #93)

**Status:** janela definida pelo grupo em 07/10/2026, por solicitação de Gustavo.
Coleta habilitada; confirmação do professor e revisão conjunta ainda pendentes.
**Sprint:** Lab03S01.
**Configuração canônica:** [`config/estudo.json`](../config/estudo.json).

Este protocolo fixa as decisões operacionais antes da coleta. As hipóteses são
expectativas, não resultados. A proposta existente foi adotada com ajuste do
limite final para exatamente doze meses. A decisão e a ausência de confirmação
do professor estão registradas em `window_decision` na configuração. Não usar
datas do `examples/demo-api.json`, que contém dados inteiramente sintéticos.
Se o professor alterar a janela, registrar a revisão e repetir a coleta com a
nova configuração antes de comparar resultados.

## População e elegibilidade

- **População-alvo:** repositórios públicos open-source do GitHub com mais de
  1.000 estrelas e que usem GitHub Actions. A consulta de candidatos deve ser
  fatiada quando necessário para contornar o limite de 1.000 resultados por
  busca; registrar consulta, data e páginas/faixas usadas. Consultas com 1.000
  ou mais resultados são subdivididas recursivamente por data de criação e,
  em fatias de um dia, por faixa de estrelas. Se um único dia e uma estrela
  exata ainda alcançarem o limite, a coleta falha em vez de aceitar dados
  truncados. IDs repetidos entre fatias são deduplicados.
  O limiar implementado é `stargazers_count > 1000`, configurado em
  `config/estudo.json`.
- **Unidade de análise:** repositório. Releases e workflow runs são unidades
  observacionais das métricas.
- **Inclusão:** ter, dentro da janela, pelo menos 5 releases publicadas
  (`draft = false`, `prerelease = false`) e pelo menos 50 workflow runs válidos
  no default branch. Run válido para essa contagem é disparado por `push` e
  tem `conclusion` `success`, `failure`, `timed_out` ou `startup_failure`.
- **Exclusão:** repositório sem Actions, abaixo de qualquer um dos dois mínimos
  ou sem dados suficientes para confirmar os critérios. Contar cada exclusão
  no funil, com motivo; não completar a amostra com registros sintéticos.
- **Tamanho da amostra:** pipeline inicial de 100 repositórios para Lab03S01;
  amostra final de pelo menos 300 elegíveis para Lab03S02.
- **Seleção do piloto (decisão de 07/10/2026):** por solicitação de Gustavo,
  manter `cli/cli`, já validado, e selecionar outros 99 elegíveis por estrelas
  decrescentes e ID crescente nos empates. Usar `--include-repo cli/cli` para
  registrar essa inclusão intencional no funil, sem dispensar os filtros.
  A amostra é intencional e não deve ser apresentada como aleatória.
- **Busca incremental:** recuperar primeiro o prefixo por popularidade,
  completar os empates na fronteira e ampliar quando faltarem elegíveis.
  Registrar separadamente o total informado pela API, os candidatos
  recuperados e os avaliados. A busca exaustiva com subdivisão permanece como
  alternativa quando o prefixo solicitado alcança o teto de 1.000 da API.
- **Ordem do funil:** depois da busca e seleção por popularidade, verificar
  GitHub Actions antes de consultar contribuidores, releases ou workflow runs.
  Os mínimos de releases e runs são aplicados somente após as duas contagens.
  Registrar entradas, aprovados e exclusões por motivo em cada etapa. A idade
  coletada é a quantidade de dias entre `created_at` e o instante `collected_at`
  registrado pelo seletor.
- **Branch:** identificar e registrar `default_branch` por repositório. Usar
  somente runs desse branch. Registrar também o SHA do default branch observado
  na coleta, conforme a arquitetura. Não tratar o branch como reconstrução
  histórica.

## Janela, limites e unidades

- Janela adotada pelo grupo: início `2025-10-06T00:00:00-03:00`,
  fim exclusivo `2026-10-06T00:00:00-03:00`, fuso fixo `-03:00`.
  A configuração valida a duração de doze meses de calendário.
- A proposta original terminava em `2026-10-06T23:59:59-03:00`, excedendo
  doze meses. Ela permanece em `proposed_window` como histórico; somente
  `window` orienta a execução. A confirmação do professor permanece pendente.
- Todos os intervalos são **`[início, fim)`**: eventos no início entram;
  eventos exatamente no fim não entram. Releases e runs são selecionados por
  `published_at` e `created_at`, respectivamente.
- Para lead time, uma release anterior pode estar antes do início da janela;
  commits incluídos nas releases da janela também podem ter sido escritos
  antes dela. Usar `commit.author.date`, não limitar esses commits ao período.
- Deployment frequency: releases por semana, usando a duração efetiva da
  janela em semanas.
- Lead time: diferença entre `release.published_at` e `commit.author.date`,
  registrada em horas e também reportada em dias quando necessário. Calcular
  as medianas por release (a) e por commit (b).
- CFR: proporção entre 0 e 1, reportável também como percentual.
- Recuperação: horas entre `run_started_at` da primeira falha e `updated_at`
  do próximo sucesso no mesmo workflow.
- Nas RQs, reportar mediana e IQR. Em RQ05, reportar Spearman (ρ, p-valor e n);
  em RQ06, reportar teste, p-valor corrigido e tamanho de efeito; em RQ07,
  mudança de categoria e kappa ponderado.

## Métricas e variantes

- **RQ01 — frequência:** número de releases publicadas na janela dividido pela
  duração exata da janela em semanas (`segundos / 604800`). O corte de uma
  release por mês equivale a `12/52` releases por semana, assumindo 52 semanas
  por ano (mês médio de `52/12` semanas).
- **RQ02 — lead time:** comparar cada release da janela com sua release
  anterior, que pode estar fora da janela. Ignorar releases sem release
  anterior. Variante (a): mediana, por repositório, do intervalo entre a data
  da release e o commit mais antigo incluído nela. Variante (b): mediana dos
  intervalos de todos os commits incluídos nas releases.
- **RQ03 — CFR:** (a) runs de CI com falha dividido por runs válidos com falha
  ou sucesso; (b) releases que foram seguidas por release corretiva em até
  sete dias, dividido pelas releases avaliáveis. Uma release corretiva é
  identificada pela heurística de patch semver e/ou mensagens de commit com
  `revert`, `hotfix` ou `fix`; validar a heurística com a amostra-ouro. Releases
  nos sete dias finais são censuradas e não entram no denominador (b).
- **RQ04 — recuperação:** ordenar runs elegíveis por workflow. Episódio começa
  na primeira falha após sucesso e termina no próximo sucesso desse workflow.
  Falhas consecutivas pertencem ao mesmo episódio. Episódio ainda aberto no
  fim da janela é censurado no limite final; reportar contagem e proporção.
- **RQ05 — associação:** Spearman entre RQ01 e cada variante de CFR da RQ03;
  associação não será interpretada como causalidade.
- **RQ06 — subgrupos:** fatores previamente escolhidos: linguagem principal,
  quartis de estrelas e quartis do número de contribuidores. Para cada fator
  e métrica das RQ01–04, usar Kruskal-Wallis; se houver dois grupos, Mann-
  Whitney. Aplicar Holm às comparações múltiplas e reportar ε² ou Cliff's delta,
  conforme o teste.
- **RQ07 — sensibilidade:** classificar com os mesmos cortes DORA da atividade
  e comparar cada par de configurações por percentual de categorias alteradas
  e kappa de Cohen ponderado linear.

| Métrica (unidade) | Elite | High | Medium | Low |
|---|---:|---:|---:|---:|
| Frequência (releases/semana) | ≥ 7 | ≥ 1 e < 7 | ≥ 1/mês e < 1/semana | < 1/mês |
| Lead time (mediana, dias) | < 1 | ≥ 1 e < 7 | ≥ 7 e < 30 | ≥ 30 |
| CFR | ≤ 15% | > 15% e ≤ 30% | > 30% e ≤ 45% | > 45% |
| Recuperação (mediana, horas) | < 1 | ≥ 1 e < 24 | ≥ 24 e < 168 | ≥ 168 |

Para a classificação geral, converter Elite/High/Medium/Low em 4/3/2/1,
respectivamente; usar a mediana das quatro notas e arredondar para baixo.
Cada métrica sem observação ou com denominador zero fica sem categoria. A
classificação geral só é calculada quando as quatro métricas estão disponíveis;
não imputar zero nem atribuir categoria geral para resultados incompletos.
O relatório inclui numeradores/denominadores disponíveis e o motivo da
incompletude. Sem workflow runs coletados (modo amostra), ou se o repositório
não tiver nenhum episódio de falha recuperado, a recuperação fica sem categoria
(`no_failure_episodes` ou `all_failure_episodes_censored`) e a classificação
geral permanece incompleta, mesmo com as outras três métricas calculadas.

| Configuração | Unidade de entrega | Lead time | CFR |
|---|---|---|---|
| C1 (referência) | Releases publicadas | (a) por release | (a) baseado em CI |
| C2 | Releases publicadas e pré-releases | (b) por commit | (b) release corretiva |
| C3 | Tags | (b) por commit | (a) baseado em CI |

As combinações seguem o exemplo da atividade. Para C2, drafts continuam
excluídos. Para C3, usar a data do commit apontado pela tag; tags sem commit
resolvido não podem receber data presumida. Em C3, o CFR (a) continua baseado
nos workflow runs, sem reinterpretar tags como falhas de CI.

## Dados ausentes, falhas e censura

- Não imputar ausências com zero, não inferir datas e não substituir campos
  ausentes por valores do snapshot de demonstração.
- Runs com `conclusion` `cancelled`, `skipped`, `neutral`, `action_required`,
  `stale` ou vazio são ignorados nos cálculos de CFR e na contagem mínima, de
  acordo com a atividade.
- Campo essencial ausente ou inválido (por exemplo, `published_at`,
  `commit.author.date`, `run_started_at` ou `updated_at`) deve ser contado com
  motivo de exclusão. Para lead time, se a data de qualquer commit de uma
  comparação for inválida ou posterior à publicação, excluir a release inteira
  dessa métrica e não saltar para uma antecessora mais antiga.
- Releases sem SHA resolvido permanecem contabilizadas como exclusões; não
  atribuir SHA aproximado. `compare` com 404 é exclusão explícita, não lista
  vazia nem sucesso.
- Para RQ04, um run anterior à janela pode ser consultado apenas como contexto
  para saber se a primeira falha observada é posterior a um sucesso; não entra
  na amostra de métricas. Episódios iniciados antes do começo da janela são
  registrados como censura à esquerda e não contados como novos episódios.
  O mesmo vale se o `run_started_at` da primeira falha for anterior ao começo
  da janela, ainda que seu `created_at` esteja dentro dela.
  Um episódio iniciado dentro da janela sem sucesso observado até o fim é
  censurado à direita no fim da janela, mesmo que uma execução posterior venha
  a encerrá-lo.
- Implementação de RQ04 (`metrics/recovery.py`): o pipeline não consulta runs
  anteriores à janela. Falhas iniciais sem sucesso anterior *dentro da janela*
  não abrem episódio e são contadas em `leading_failures_without_prior_success`
  (censura à esquerda aproximada). A mediana usa só episódios recuperados;
  `censored_proportion` = censurados / episódios totais. O tempo usa
  `run_started_at` da primeira falha e `updated_at` do sucesso, sem substituir
  datas ausentes. Intervalos negativos ou sem datas são excluídos e contados
  em `exclusions`. Falhas iniciadas fora da janela são excluídas. Sucessos
  concluídos no limite final ou depois dele não encerram episódios; episódios
  abertos registram esse limite em `censored_at`.
- Workflow runs (`collectors/workflow_runs.py`): a janela é fatiada por mês (UTC);
  fatia com `total_count > 1000` é bisseccionada até caber; se não houver mais
  divisão possível na precisão de segundos da API, a coleta falha. A consulta
  arredonda limites fracionários e aplica o intervalo exato localmente; IDs
  repetidos são deduplicados. A elegibilidade usa esse mesmo coletor e usa
  o coletor de releases com verificação de ancestralidade no default branch.
  Runs ignorados e registros inválidos têm contagens separadas.
  Se o total mudar entre páginas ou a quantidade de IDs únicos não coincidir
  com o total informado, descartar a fatia inconsistente e consultar duas
  fatias menores. Registrar a recuperação em `pagination_repairs`. Se não
  houver divisão possível na precisão da API, interromper sem gravar resultado
  parcial; nunca aceitar silenciosamente páginas divergentes.
- Rate limit é esperado e não é erro: o cliente aguarda `X-RateLimit-Reset`
  (ou `Retry-After`) e repete a requisição; respostas 5xx e falhas de rede são
  repetidas com backoff exponencial (1 s, 2 s, 4 s, 8 s, 16 s, até 5 tentativas).
  Só rate limit persistente (20 esperas seguidas numa requisição) ou esgotamento
  das tentativas interrompem a coleta, que pode ser retomada pelo cache.
- Erros de autenticação, paginação truncada e falhas inesperadas
  da API interrompem a coleta com erro explícito. Não os registrar como
  ausência de dados nem como exclusão de repositório.
- Exceção conhecida de disponibilidade de metadados: quando o endpoint de
  contribuidores retorna a mensagem específica de que o histórico/lista é
  grande demais para ser listado pela API, excluir com
  `contributors_unavailable_api_limit` no funil. Não imputar a contagem.
  Outros HTTP 403 continuam sendo erros; limites de cota seguem a política
  de espera. Esta limitação foi observada em `torvalds/linux` no piloto.
- Manter contagens por motivo no funil e registrar os limites da janela
  aplicados a cada fonte.

## Hipóteses a priori

As hipóteses abaixo foram escritas antes de examinar resultados. Mantê-las
inalteradas após a coleta; qualquer revisão posterior deve ser identificada
como exploratória, datada e justificada.

| RQ | Hipótese informal |
|---|---|
| RQ01 | Há heterogeneidade na frequência de releases, com concentração de repositórios abaixo de uma entrega semanal, pois projetos podem agrupar mudanças em ciclos distintos. |
| RQ02 | A mediana de lead time por release tende a ser superior à mediana por commit, pois commits antigos podem elevar a primeira variante; não é uma relação matemática necessária. |
| RQ03 | CFR baseado em CI e CFR baseado em releases corretivas tendem a divergir, pois representam eventos distintos; não se prevê qual será maior. |
| RQ04 | Os tempos de recuperação têm distribuição assimétrica, com muitos episódios curtos e alguns longos; episódios sem encerramento na janela permanecem censurados. |
| RQ05 | Espera-se associação monotônica fraca ou não positiva entre frequência e CFR; testar separadamente cada variante de CFR, sem inferir causalidade. |
| RQ06 | Pelo menos uma métrica difere entre subgrupos de linguagem principal, quartis de estrelas ou quartis de contribuidores. |
| RQ07 | Parte dos repositórios muda de categoria DORA quando se alteram unidade de entrega, lead time ou CFR, sobretudo perto dos limites de classificação. |

## Execução e rastreabilidade

1. A decisão do grupo habilita a coleta com a janela acima; não representa
   confirmação do professor nem aprovação já realizada pelo trio.
2. Registrar a revisão conjunta e eventual confirmação ou correção do
   professor antes de interpretar os resultados finais.
3. Cada relatório inclui a configuração e seu SHA-256. O cache é separado
   por esse identificador; usar `--refresh-cache` para renovar respostas da
   mesma configuração. O cache registra o instante de obtenção das respostas.
4. Executar o piloto real de 100 elegíveis e registrar sua evidência no
   manifesto. Testes e snapshots sintéticos não comprovam essa entrega.
