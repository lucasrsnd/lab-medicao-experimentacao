# Lab05 — Dicionário de dados

Issue: S01-03 (#183). Responsável: @gustavoprehl. Revisor: @lucasrsnd.

Gerado por [`scripts/coleta.py`](../scripts/coleta.py). Protocolo: [protocolo-coleta.md](protocolo-coleta.md).

## 1. Observações — `<nome>_<UTC>.csv`

Formato longo, uma linha por (tratamento, unidade, repetição, métrica). É a entrada de `analysis/` ([plano de análise](plano-analise.md), seção 1).

| Coluna | Tipo | Unidade | Escala | Origem |
|---|---|---|---|---|
| `tratamento` | texto | — | nominal | chave de `tratamentos` no arquivo de alvos |
| `unidade` | texto | — | nominal | item de `unidades` no arquivo de alvos |
| `repeticao` | inteiro ≥ 1 | — | ordinal (ordem da rodada) | plano de execução do coletor |
| `metrica` | texto | — | nominal | uma das métricas abaixo |
| `valor` | real, 3 casas | a da métrica | a da métrica | medição |

### Métricas

| `metrica` | Unidade | Escala | Direta/derivada | Entidade / atributo | Origem |
|---|---|---|---|---|---|
| `tempo_ms` | milissegundo | razão | direta | produto / tempo de resposta (externo) | `perf_counter` antes do `GET` e depois do corpo baixado |
| `ttfb_ms` | milissegundo | razão | direta | produto / latência até os cabeçalhos (externo) | `requests.Response.elapsed` |
| `tamanho_kb` | KiB (1024 bytes) | razão | direta | produto / tamanho da resposta (interno à resposta) | `len(corpo) / 1024`, após descompressão |

Só entram requisições bem-sucedidas (HTTP < 400) da fase de medição. Métricas do software escolhido serão acrescentadas aqui **[pendente: #182]**.

## 2. Log — `<nome>_<UTC>.log.jsonl`

Uma linha JSON por requisição, na ordem em que foi feita.

| Campo | Tipo | Unidade | Significado |
|---|---|---|---|
| `ordem` | inteiro | — | Posição da requisição na execução (1, 2, …) |
| `timestamp` | texto ISO 8601 | UTC | Fim da requisição |
| `fase` | texto | — | `aquecimento` (descartada) ou `medicao` |
| `tratamento`, `unidade` | texto | — | Como no CSV |
| `repeticao` | inteiro | — | Como no CSV; no aquecimento, índice do aquecimento (0 = aquecimento por unidade) |
| `url` | texto | — | URL requisitada (pública, sem parâmetros pessoais) |
| `ok` | booleano | — | HTTP < 400 |
| `status` | inteiro ou nulo | — | Código HTTP; nulo se a conexão falhou |
| `tentativa` | inteiro | — | Tentativas usadas (1 a 4) |
| `tempo_ms`, `ttfb_ms`, `tamanho_kb` | real | como acima | Ausentes quando a conexão falhou |
| `erro` | texto | — | Vazio, `HTTP 4xx` ou mensagem da exceção de rede |

## 3. Metadados — `<nome>_<UTC>.meta.json`

| Campo | Significado |
|---|---|
| `alvos`, `software`, `tratamentos`, `n_unidades` | Copiados do arquivo de alvos (software com versão exata) |
| `parametros` | `repeticoes`, `aquecimento`, `aquecer_unidades`, `semente`, `intervalo_s` efetivo, `timeout_s`, `user_agent` |
| `config_sha256` | Hash do arquivo de alvos, para saber se duas execuções usaram a mesma configuração |
| `ambiente` | Python, `requests`, SO, arquitetura, processador, commit do repositório e rede (`--rede`) |
| `inicio_utc`, `fim_utc`, `duracao_s` | Janela da coleta |
| `requisicoes`, `falhas_medicao` | Total de requisições (com aquecimento) e falhas na fase de medição |
| `validacao` | Resultado das checagens do protocolo (seção 7) |
