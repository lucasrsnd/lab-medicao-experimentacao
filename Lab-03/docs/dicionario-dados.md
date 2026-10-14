# Dicionário e validação dos artefatos CSV

Este dicionário descreve as exportações efetivas de `lab03.variants` para a
issue #117. Os arquivos usam UTF-8 e cabeçalho. Uma chave vazia representa
ausência; zero numérico é um valor observado. As métricas mantêm sua unidade
nos nomes ou na coluna `*_unidade_denominador`.

## `variantes_metricas.csv`

Chave composta única: (`repositorio`, `variante`). Dataset final: ao menos 300
repositórios distintos, com exatamente uma linha para cada C1, C2 e C3. Origem:
JSONs de coleta `--full` e complementos da API, conforme manifesto
`variantes.json`.

| Coluna | Tipo/unidade | Definição |
|---|---|---|
| `repositorio` | `owner/name` | `metadata.full_name` do repositório. |
| `variante` | enum C1/C2/C3 | Combinação de unidade de entrega, lead time e CFR definida em `protocolo.md`. |
| `unidade_entrega` | enum | C1 releases publicadas; C2 releases e pré-releases; C3 commits entregues por tags. |
| `lead_time_variante` | enum | C1 por release; C2/C3 por commit. |
| `cfr_variante` | enum | C1/C3 runs CI; C2 release corretiva. |
| `*_valor` | varia por métrica | Frequência em releases/semana; lead time/recuperação em horas; CFR como proporção [0,1]. Célula vazia é ausência; `0` é resultado observado. |
| `*_numerador` | contagem ou vazio | Contagem que origina a métrica, quando aplicável. Frequência: entregas; CFR: falhas. |
| `*_denominador` | contagem/unidade ou vazio | Duração em semanas, releases, commits, runs CI, releases avaliáveis ou episódios recuperados, conforme variante. |
| `*_unidade_denominador` | enum | `weeks`, `releases`, `commits`, `valid_ci_runs`, `evaluable_releases` ou `recovered_episodes`. |
| `*_categoria` | Elite/High/Medium/Low ou vazio | Categoria por métrica segundo os cortes DORA do protocolo; vazia quando não classificável. |
| `*_motivo_ausencia` | código ou vazio | Motivo obrigatório quando `*_valor` está vazio; vazio quando a métrica foi observada. |
| `cfr_b_releases_censored` | inteiro ou vazio | Releases sem sete dias completos de acompanhamento, somente em C2. Vazio para as variantes CI ou complemento não coletado. Zero é ausência de censura observada. |
| `recovery_episodes_censored` | inteiro ou vazio | Episódios de recuperação censurados à direita; calculado como episódios totais menos recuperados. |
| `categoria_geral` | Elite/High/Medium/Low ou vazio | Mediana das quatro pontuações, arredondada para baixo; vazia se incompleta. |
| `pontos_gerais` | inteiro 1–4 ou vazio | Pontuação da categoria geral. |
| `status_geral` | enum | `classified` ou `incomplete`. |
| `metricas_ausentes` | lista separada por `;` | Métricas que impediram classificação geral. |
| `validacoes_pendentes` | lista separada por `;` | Validações não concluídas, como `corrective_release_heuristic_gold_sample`. |
| `complemento_disponivel` | booleano ou vazio | Indica se os dados de tags/pré-releases necessários a C2/C3 foram coletados. |

Unidades por variante:

| Métrica | C1 | C2 | C3 |
|---|---|---|---|
| Frequência | semanas | semanas | semanas |
| Lead time | releases | commits | commits |
| CFR | `valid_ci_runs` | `evaluable_releases` | `valid_ci_runs` |
| Recuperação | `recovered_episodes` | `recovered_episodes` | `recovered_episodes` |

`recovery_episodes_censored` e `cfr_b_releases_censored` registram censura
separadamente da célula vazia de uma métrica. Assim, uma métrica igual a zero,
uma ausente (`*_motivo_ausencia`) e uma observação censurada não são
intercambiáveis.

## `rq07_classificacoes.csv`

Uma linha por `repositorio`, chave única e cobertura igual à dos 300+
repositórios de `variantes_metricas.csv`. Para cada variante, contém
`C1_categoria`/`C1_status`, `C2_categoria`/`C2_status` e
`C3_categoria`/`C3_status`. Deve corresponder às categorias/status gerais no
arquivo de métricas.

## `variantes.json`

Manifesto e fonte canônica da exportação: janela, versões, hashes dos datasets
e complementos de origem, cobertura, versões e validação da heurística,
políticas de ausência e resultados completos por repositório/variante. A
exportação identifica cada dataset de entrada por SHA-256; o validador exige
que o hash de origem da amostra-ouro conste nesse conjunto.

## Ligação à amostra-ouro

`labels/amostra_ouro_releases.csv` contém a chave composta
(`repositorio`, `release_id`) de 300 releases, cinco em cada um dos 60
repositórios sorteados. Todos os 60 devem pertencer ao dataset final. O
manifesto do sorteio deve registrar 60 repositórios, 300 releases e o hash do
dataset que serviu de origem.

## Execução

Instale as dependências de desenvolvimento e validação (`.[dev,validation]`).
Depois da exportação completa:

```powershell
python -m lab03.dataset_validation `
  --metrics validation/dataset-v1/variantes_metricas.csv `
  --classifications validation/dataset-v1/rq07_classificacoes.csv `
  --variants validation/dataset-v1/variantes.json `
  --gold-sample labels/amostra_ouro_releases.csv `
  --gold-manifest labels/amostra_ouro_sorteio.json `
  --output-manifest validation/dataset-v1/manifesto-validacao-v1.json
```

O validador verifica chaves, cobertura, duplicatas, unidades, denominadores,
intervalos, fórmulas de frequência/CFR, consistência CSV/JSON, contagens da
amostra-ouro, valores zero/ausentes/censurados e hashes. Um manifesto existente
nunca é sobrescrito; use um nome novo para cada congelamento.
