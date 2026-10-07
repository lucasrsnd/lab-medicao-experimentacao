# Lab 03 — coleta de proxies DORA

O pipeline usa Python 3.12+, biblioteca padrão para HTTP (`urllib`) e testes
com `pytest`. Não usa PyGithub nem SDK de consulta à API do GitHub.

## Instalação e demonstração local

No diretório `Lab-03`, instale o pacote e dependências de desenvolvimento:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Execute a amostra pequena offline com um comando:

```powershell
python -m lab03 --config config/amostra.json --output data/demo.json
```

A configuração fixa um repositório e usa `examples/demo-api.json`, um snapshot
inteiramente sintético. A saída também é apenas demonstração; não a misture
com dados do estudo. O snapshot nunca faz fallback para a rede e não requer
token.

## Coleta real

A janela adotada pelo grupo em `config/estudo.json` vai de
`2025-10-06T00:00:00-03:00` até `2026-10-06T00:00:00-03:00`, com fim exclusivo.
A coleta está habilitada por decisão do grupo; a confirmação do professor
permanece pendente e está registrada em `window_decision`. Para validar:

```powershell
python -m lab03 --config config/estudo.json --validate-config
```

Se a janela for revisada, atualize a configuração e repita a coleta.
O token deve ser definido somente no ambiente do processo:

```powershell
$env:GITHUB_TOKEN = "seu-token"
python -m lab03 --config config/estudo.json --repo owner/repo --output data/repo.json
```

A consulta individual real coleta releases, commits e workflow runs e calcula
as quatro métricas disponíveis para C1, com motivos explícitos de incompletude.

Para coletar o piloto integrado de 100 repositórios elegíveis, gerar o funil e
salvar releases, commits, workflow runs e metadados:

```powershell
python -m lab03 --config config/estudo.json --pilot --output data/piloto.json
```

A busca usa o critério estrito `stars:>1000` da configuração. O seletor avalia
candidatos em ordem decrescente de estrelas e amplia a busca até reunir os 100
elegíveis; se a população disponível não for suficiente, falha sem gravar uma
saída parcial. O JSON registra o comando, a configuração, a versão do pipeline,
contagens por etapa, resultados por repositório e estatísticas do cache.
Respostas bem-sucedidas da API ficam em `data/cache.sqlite3`, ignorado pelo Git;
reexecutar o mesmo comando retoma a coleta sem repetir as requisições já
armazenadas. O cache separa respostas por SHA-256 da configuração, registrado
também em cada relatório junto aos valores utilizados. Para atualizar os dados
da mesma configuração, acrescente `--refresh-cache`; para manter uma execução
independente, use outro caminho em `--cache`. O cache registra quando obteve
cada resposta e guarda somente payloads e cabeçalhos de paginação, nunca o token.

Consultas com
1.000 ou mais resultados são subdivididas por intervalos de criação; IDs
repetidos entre fatias são deduplicados. Se uma fatia diária ainda alcançar o
limite, ela é subdividida por faixas de estrelas; uma faixa de um único valor
que ainda exceda o limite interrompe a coleta sem aceitar resultados truncados.
O funil verifica Actions antes de consultar contribuidores, releases e runs;
somente depois das contagens de releases e runs aplica os mínimos de
elegibilidade. Para cada repositório elegível, o piloto também persiste os
registros completos de workflow runs do default branch.
Elegibilidade e coleta final usam os mesmos coletores: releases precisam
pertencer ao histórico do default branch e runs são divididos por tempo para
evitar truncamento no limite de 1.000 resultados da API.
`age_days_at_collection` é calculada de `created_at` até o instante de início
registrado em `collected_at`.

Não inclua tokens nos arquivos, argumentos do comando, fixtures, logs ou
commits. A saída é gravada atomicamente somente após uma coleta completa. Erros da API,
dados incompletos e falhas de rede encerram a execução sem produzir resultado
parcial. O `.gitignore` exclui `.env`, variantes `.env.*`, arquivos `*.token`,
`tokens/`, cache e dados gerados.

## Estrutura e contratos

- `src/lab03/domain.py`: contratos imutáveis de repositório, release, commit,
  tag, workflow run e janela. Os timestamps dos contratos são timezone-aware e
  normalizados para UTC pela função `timestamp`.
- `src/lab03/collectors/`: seleção de candidatos, releases, commits e runs.
- `src/lab03/normalization.py`: adaptação dos payloads REST para os contratos
  tipados de domínio.
- `src/lab03/metrics/`: funções puras para frequência de releases por semana
  exata, lead time em horas nas variantes por release e por commit, e
  classificação DORA com tratamento explícito de dados incompletos.
- `src/lab03/analysis/`: projeção dos contratos e métricas no relatório JSON.
- `src/lab03/pipeline.py`: orquestra os coletores, métricas e análise de um
  repositório.
- `src/lab03/pilot.py`: integra seleção, elegibilidade, coleta de métricas e
  workflows para a amostra de 100.
- `src/lab03/cache.py`: persistência SQLite das respostas HTTP bem-sucedidas
  (e de 404/410/451) para retomada.
- `src/lab03/resilience.py`: espera automática por rate limit
  (`X-RateLimit-*`, `Retry-After`) e backoff exponencial para 5xx/rede. A CLI
  empilha `cache -> resiliência -> HTTP`; respostas em cache não gastam cota.
- `src/lab03/collectors/workflow_runs.py`: coleta os runs da janela fatiando
  por mês e subdividindo fatias que atingem o teto de 1.000 resultados.
- `src/lab03/github.py`: cliente REST próprio, paginação, transporte HTTP e
  snapshot offline.
- `src/lab03/configuration.py`: validação das configurações antes da execução.
- `tests/fixtures/contracts.json`: fixture sintética dos contratos
  normalizados; `examples/demo-api.json` contém respostas REST sintéticas para
  integração offline.

Execute a suíte no diretório `Lab-03`:

```powershell
python -m pytest
```

Frequência usa `releases na janela / (segundos da janela / 604800)`. Para
classificação, o corte de uma release por mês é convertido em `12/52` releases
por semana (mês médio de `52/12` semanas). A classificação geral só é emitida
quando as quatro métricas têm denominadores não nulos. CFR (a) e recuperação
vêm dos workflow runs (`metrics/change_failure_rate.py`, `metrics/recovery.py`);
sem runs, ou sem episódio de falha recuperado, a categoria geral é marcada
como incompleta, nunca como zero ou Elite.

Se a coleta for interrompida (rate limit persistente, queda de rede ou
`Ctrl+C`), rode o mesmo comando: o que já está no cache não é consultado de novo.

O manifesto em `config/manifesto-piloto.json` distingue validação sintética
de execução real. O piloto de 100 repositórios ainda precisa de evidência real;
testes locais não substituem essa entrega. O protocolo detalha as decisões em
[`docs/protocolo.md`](docs/protocolo.md).
