# Lab05 — Protocolo de coleta

Issue: S01-03 (#183). Responsável: @gustavoprehl. Revisor: @lucasrsnd.

> **Status:** protocolo válido para qualquer estudo por requisições HTTP. Os itens marcados **[pendente]** dependem da escolha do software (#181) e das métricas da proposta (#182). O piloto de fumaça ([piloto.md](piloto.md)) já seguiu este protocolo.

## 1. O que é coletado

Para cada requisição de medição, três medidas diretas, todas do **produto** (software medido) e de atributos **externos** (dependem do ambiente):

| Métrica | O que mede | Como |
|---|---|---|
| `tempo_ms` | Tempo total da resposta, do envio ao último byte do corpo | `time.perf_counter()` em volta do `GET` com o corpo baixado |
| `ttfb_ms` | Tempo até receber os cabeçalhos (aprox. *time to first byte*) | `Response.elapsed` do `requests` |
| `tamanho_kb` | Tamanho do corpo recebido (já descomprimido) | `len(corpo) / 1024` |

`tamanho_kb` funciona como **métrica de controle**: quando os tratamentos devem servir o mesmo conteúdo, tamanhos diferentes indicam que a comparação não é justa (página de erro, conteúdo diferente, versão errada).

Métricas específicas do software (ex.: número de recursos, pontuação de acessibilidade, erros) entram aqui depois de #182 **[pendente]**. Novas métricas devem manter o formato longo (seção 6).

## 2. De onde

Os alvos ficam num arquivo JSON em `scripts/alvos/` (modelo: [`modelo_externo.json`](../scripts/alvos/modelo_externo.json)):

- `tratamentos`: nome → URL com `{unidade}` (ex.: versão 1 × versão 2, app × site, configuração A × B);
- `unidades`: o que é medido em todos os tratamentos (páginas, consultas, endpoints). Medir a mesma unidade em todos os tratamentos torna o desenho **pareado** (plano de análise, seção 4);
- `software`: nome, versão exata e site oficial, copiados para os metadados de cada execução.

Software, tratamentos e unidades do estudo: **[pendente: #181, #182]**.

## 3. Como (procedimento)

1. Conferir os termos de uso e o `robots.txt` (seção 5) e registrar os links.
2. Registrar o ambiente: o coletor grava Python, `requests`, SO, CPU e commit do repositório em `.meta.json`. A rede é informada em `--rede` (tipo e velocidade contratada). Usar sempre a **mesma máquina e a mesma rede** em uma execução, sem outros downloads em andamento.
3. **Aquecimento** (descartado, mas registrado no log): `--aquecimento N` requisições por tratamento e `--aquecer-unidades` (uma por unidade e tratamento). O piloto mostrou que, sem aquecer cada unidade, a repetição 1 mede cache frio ([piloto.md](piloto.md), seção 3).
4. **Ordem aleatória** com semente fixa (`--semente`): em cada repetição as unidades são embaralhadas e, dentro de cada unidade, a ordem dos tratamentos também. Isso contrabalança cache e deriva temporal (rede mais lenta num horário).
5. **Intervalo** entre requisições (`--intervalo`), no mínimo 1 s para qualquer host externo (imposto pelo código).
6. **Falhas:** erros de rede, HTTP 429 e 5xx são repetidos até 4 vezes com backoff exponencial (2, 4, 8 s, adaptado do Lab01). Respostas 4xx e falhas definitivas **não** viram observação: ficam no log e contam em `falhas_medicao`.
7. Ao final o coletor valida os dados (seção 7) e encerra com erro se houver problemas.

## 4. Frequência e número de observações

| Parâmetro | Piloto (S01) | Coleta completa (S02) |
|---|---|---|
| Unidades | 20 | **[pendente: #182]** |
| Repetições por (unidade, tratamento) | 5 | definido pelo poder no piloto real (`n_necessario.csv`, plano de análise, seção 6), com folga de 20% para perdas |
| Aquecimento | 3 + 1 por unidade | idem |
| Execuções | 1 | 2 ou mais, em dias e horários diferentes, para checar estabilidade (validade de conclusão) |

Duração estimada: `python scripts/coleta.py <alvos>.json --estimar ...`. Conta em [piloto.md](piloto.md), seção 5.

## 5. Ética

Regras aplicadas a qualquer software escolhido:

- **Sem teste de carga em terceiros:** uma requisição por vez, no máximo **1 requisição/s** por host externo. O código não aceita intervalo menor para hosts que não sejam `localhost`/`127.0.0.1`.
- **robots.txt:** verificado automaticamente antes da coleta. Se qualquer URL estiver bloqueada, a coleta não começa (`PermissionError`).
- **Identificação:** `User-Agent` declara uso acadêmico e o limite de taxa.
- **Termos de uso:** lidos antes da coleta e registrados abaixo com link e data de acesso.
- **Dados pessoais:** nenhum. Só são gravados tempos, tamanhos, status HTTP e as URLs públicas da configuração. O corpo das respostas não é salvo. Nenhuma coleta exige login com conta real.
- **Estudo com participantes (se o caminho escolhido incluir):** termo de consentimento livre e esclarecido antes da sessão (objetivo, duração, voluntariedade, direito de desistir, anonimização); participantes identificados só por código (`P01`, `P02`…); contas fictícias criadas pelo grupo para as tarefas; nenhuma gravação de tela ou voz sem consentimento explícito.

| Verificação | Link | Acesso em | Resultado |
|---|---|---|---|
| Termos de uso do software | **[pendente: #181]** | | |
| `robots.txt` | **[pendente: #181]** | | |
| Política de API / limites publicados (se houver) | **[pendente: #181]** | | |

## 6. Formato de saída

Cada execução grava em `--saida` (`data/piloto/` na S01, `data/raw/` na S02):

| Arquivo | Conteúdo |
|---|---|
| `<nome>_<UTC>.csv` | Observações no formato longo do [plano de análise](plano-analise.md), seção 1 |
| `<nome>_<UTC>.log.jsonl` | Uma linha por requisição (aquecimento, medição e falhas) |
| `<nome>_<UTC>.meta.json` | Software, tratamentos, parâmetros, ambiente, duração e validação |

Colunas e unidades: [dicionario-dados.md](dicionario-dados.md).

## 7. Validação automática

| Checagem | Regra |
|---|---|
| Nulos | nenhum `valor` ausente |
| Duplicatas | uma linha por (tratamento, unidade, repeticao, metrica) |
| Faixa | nenhum valor negativo; `tempo_ms` ≤ timeout; `ttfb_ms` ≤ `tempo_ms` |
| Completude | observações obtidas / esperadas = 1 (senão, investigar as falhas no log) |
| Controle | `tamanho_kb` igual entre tratamentos quando o conteúdo deve ser o mesmo (conferido no piloto) |

Os problemas encontrados e os ajustes no protocolo são registrados em [piloto.md](piloto.md).
