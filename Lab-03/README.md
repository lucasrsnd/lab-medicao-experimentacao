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

A janela oficial ainda aguarda confirmação do professor. Por isso,
`config/estudo.json` mantém `collection_allowed: false` e início/fim oficiais
vazios. A coleta real falha antes de fazer qualquer requisição enquanto essa
pré-condição não for atendida. Para testar apenas a configuração:

```powershell
python -m lab03 --config config/estudo.json --validate-config
```

Depois que o professor confirmar os limites e o trio revisar o protocolo,
atualize `window.start`, `window.end`, `window.timezone`, `status` para `ready`
e `collection_allowed` para `true` em `config/estudo.json`. O token deve ser
definido somente no ambiente do processo:

```powershell
$env:GITHUB_TOKEN = "seu-token"
python -m lab03 --config config/estudo.json --repo owner/repo --output data/repo.json
```

Para selecionar os 100 candidatos iniciais e gerar o funil de elegibilidade:

```powershell
python -m lab03 --config config/estudo.json --select-candidates --output data/funil.json
```

A busca usa o critério estrito `stars:>1000` da configuração. Consultas com
1.000 ou mais resultados são subdivididas por intervalos de criação; IDs
repetidos entre fatias são deduplicados. Se uma fatia diária ainda alcançar o
limite, ela é subdividida por faixas de estrelas; uma faixa de um único valor
que ainda exceda o limite interrompe a coleta sem aceitar resultados truncados.
O funil verifica Actions antes de consultar contribuidores, releases e runs;
somente depois das contagens de releases e runs aplica os mínimos de
elegibilidade. O resultado registra cada etapa, totais e motivos de exclusão.
`age_days_at_collection` é calculada de `created_at` até o instante de início
registrado em `collected_at`.

Não inclua tokens nos arquivos, argumentos do comando, fixtures, logs ou
commits. A saída é gravada atomicamente somente após uma coleta completa. Erros
da API, dados incompletos e falhas de rede encerram a execução sem produzir
resultado parcial. O `.gitignore` exclui `.env`, variantes `.env.*`, arquivos
`*.token`, `tokens/`, cache e dados gerados.

O transporte atual ainda não implementa a persistência/cache e a retomada das
issues #95 e #96; erros da API interrompem a execução. Não use esta versão como
coleta final de um estudo longo até esses pré-requisitos serem concluídos.

## Estrutura e contratos

- `src/lab03/domain.py`: contratos imutáveis de repositório, release, commit,
  tag, workflow run e janela. Os timestamps dos contratos são timezone-aware e
  normalizados para UTC pela função `timestamp`.
- `src/lab03/collectors/`: coleta de releases e commits.
- `src/lab03/normalization.py`: adaptação dos payloads REST para os contratos
  tipados de domínio.
- `src/lab03/metrics/`: funções puras para frequência de releases por semana
  exata, lead time em horas nas variantes por release e por commit, e
  classificação DORA com tratamento explícito de dados incompletos.
- `src/lab03/analysis/`: projeção dos contratos e métricas no relatório JSON.
- `src/lab03/pipeline.py`: orquestra os coletores, métricas e análise, sem
  persistência.
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
quando as quatro métricas têm denominadores não nulos; no pipeline atual, CFR
e recuperação permanecem sem coleta, portanto a categoria geral é marcada
como incompleta, nunca como zero ou Elite.
