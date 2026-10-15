# Protocolo de validação manual (amostra-ouro) — Lab03S02

Seção 6 do enunciado. Este documento fixa o sorteio e o protocolo cego **antes**
de qualquer rótulo ser preenchido.

## 1. Coleta completa

```powershell
$env:GITHUB_TOKEN = "SEU_TOKEN_LOCAL"   # substitua localmente; nunca commitar
python -m lab03 --config config/estudo.json --full --output data/amostra_completa.json
```

- Alvo: `population.final_sample_minimum` (300) repositórios elegíveis.
- Exige `collection_allowed: true` e a janela oficial em `config/estudo.json`
  (pré-condições do [protocolo](protocolo.md)). Sem isso a CLI recusa antes de
  qualquer requisição.
- Cache em `data/cache.sqlite3` (padrão; use `--cache` para outro caminho, como
  `data/cache_estudo.sqlite3`): se a coleta cair (rate limit, rede, `Ctrl+C`),
  rode o mesmo comando para retomar.
- Cada repositório traz `delivery_failure_rate` (CFR b), com o veredito da
  heurística por release e a versão da heurística.

## 2. Sorteio

```powershell
python -m lab03.gold_sample --dataset data/amostra_completa.json --out labels/reamostragem-v2
```

- 60 repositórios, sorteados com `random.Random(42).sample` sobre os nomes
  ordenados que têm ao menos cinco releases comparáveis. A ordem do arquivo
  não influencia. Repositórios sem cinco releases rotuláveis são excluídos do
  sorteio para manter exatamente 300 releases.
- 5 releases por repositório: `random.Random(f"42:{repo}")`, entre as releases
  da janela que têm lista de commits (a primeira release histórica não tem
  comparação e não é rotulável).
- `labels/reamostragem-v2/amostra_ouro_sorteio.json` registra semente, hash
  SHA-256 do dataset e janela, além das contagens de repositórios elegíveis e
  excluídos. `labels/reamostragem-v2/amostra_ouro_releases.csv` é a lista
  sorteada (sem rótulos).
- O comando recusa sobrescrever arquivos existentes (`--force` refaz o sorteio e
  **apaga o trabalho de rotulagem**; só usar antes de alguém começar).

## 3. Regras do protocolo cego

1. Cada avaliador (A, B, C) preenche **só** a sua planilha em
   `labels/reamostragem-v2/`:
   `rotulos_<X>_repositorios.csv` e `rotulos_<X>_releases.csv`.
2. Não consultar os outros avaliadores nem os rótulos deles, não abrir os
   arquivos dos outros enquanto não houver consenso.
3. Não ver a saída da heurística: não abrir `data/amostra_completa.json`
   (campos `delivery_failure_rate`, `verdicts`), não rodar a heurística sobre a
   amostra-ouro e não olhar métricas DORA dos repositórios sorteados. As
   planilhas não contêm nada disso.
4. Commitar o arquivo de rótulos só quando ele estiver completo, referenciando
   a Issue do avaliador no commit.

## 4. Como preencher

Planilha de repositórios (uma linha por repositório):

| Coluna | Valores | Critério |
|---|---|---|
| `tipo_projeto` | `biblioteca/framework`, `aplicacao/servico`, `ferramenta CLI`, `outro`, `incerto` | O que o repositório principalmente entrega, lendo README e estrutura; registrar motivo de `incerto` em `observacoes`. |
| `releases_sao_entregas` | `sim`, `nao`, `incerto` | As releases chegam a usuários como entregas reais (binários, pacote publicado, versão implantável), ou são só marcos/tags sem entrega? |
| `observacoes` | texto livre | Dúvidas e motivo de `incerto`. |

Planilha de releases (uma linha por release sorteada; abrir `url_release` e
`url_comparacao`, ler release notes e a lista de commits):

| Coluna | Valores | Critério |
|---|---|---|
| `e_corretiva` | `sim`, `nao`, `incerto` | `sim` se o objetivo **principal** da release é corrigir um defeito recente (hotfix, revert, correção de regressão). Release que mistura novas funcionalidades e algumas correções, como é comum, é `nao`; registrar motivo de `incerto` em `observacoes`. |
| `observacoes` | texto livre | Ex.: "release só de dependências". |

`url_comparacao` vazia significa que não há release anterior comparável (não
deveria ocorrer no sorteio).

O sorteio atual tem 60 repositórios e 283 releases, e não 300. Os
repositórios com menos de 5 releases rotuláveis entram com as que têm.
`microsoft/terminal` e `modelcontextprotocol/servers` não têm nenhuma release
rotulável e são avaliados só na planilha de repositórios.

### Validação do formato

Antes de commitar, cada avaliador valida **a própria** planilha:

```powershell
python -m lab03.label_validation --rater B --complete-ids --allow-blank   # durante a rotulagem: progresso
python -m lab03.label_validation --rater B                                 # ao final: exige tudo preenchido
```

O validador lê só o sorteio e as planilhas do avaliador informado. Não abre
rótulos dos outros nem a saída da heurística. Ele confere:

- a cobertura exata do sorteio, sem linhas repetidas;
- o vocabulário das três dimensões (`tipo_projeto`, `releases_sao_entregas` e
  `e_corretiva`);
- a justificativa em `observacoes` quando o valor for `outro` ou `incerto`.

`--complete-ids` preenche `release_id` a partir do sorteio, sem alterar
rótulos. Os rótulos só são publicados depois que os três avaliadores
encerrarem a avaliação independente.

## 5. Consenso e métricas (Issues do Davi)

Cálculo do kappa de Fleiss, consenso (maioria simples; casos 1-1-1 decididos em
reunião e registrados) e avaliação da heurística (precisão/recall/F1, refinar se
F1 < 0,70) usam estes arquivos como entrada. A heurística atual é
`HEURISTIC_VERSION = "v2"` em `src/lab03/metrics/corrective.py`.

### Calcular concordância e preparar consenso

Somente depois de A, B e C finalizarem as planilhas, execute no diretório
`Lab-03`:

```powershell
python -m lab03.manual_validation agreement `
  --sample-manifest labels/reamostragem-v2/amostra_ouro_sorteio.json `
  --sample-repositories labels/reamostragem-v2/rotulos_A_repositorios.csv `
  --sample-releases labels/reamostragem-v2/amostra_ouro_releases.csv `
  --a-repositories labels/reamostragem-v2/rotulos_A_repositorios.csv `
  --a-releases labels/reamostragem-v2/rotulos_A_releases.csv `
  --b-repositories labels/reamostragem-v2/rotulos_B_repositorios.csv `
  --b-releases labels/reamostragem-v2/rotulos_B_releases.csv `
  --c-repositories labels/reamostragem-v2/rotulos_C_repositorios.csv `
  --c-releases labels/reamostragem-v2/rotulos_C_releases.csv `
  --output-dir labels/consenso-v1
```

O script exige 60 repositórios e 300 releases idênticos entre os avaliadores.
Ele chama `aggregate_raters` e `fleiss_kappa` do statsmodels, reporta categorias,
itens completos, ausências por avaliador, kappa indefinido e concordância baixa.
Itens incompletos são reportados e não entram no cálculo. Os CSVs de consenso
são rascunhos; as colunas de consenso ficam vazias para deliberação dos três,
sem desempate automático. Mantenha as planilhas individuais inalteradas.

### Avaliar a versão congelada da heurística

Após decidir e registrar os rótulos de consenso, exporte as previsões da versão
que gerou o dataset e avalie-as:

```powershell
python -m lab03.manual_validation predictions `
  --dataset data/amostra_completa.json `
  --sample-releases labels/reamostragem-v2/amostra_ouro_releases.csv `
  --output labels/consenso-v1/previsoes-v2.csv

python -m lab03.manual_validation evaluate `
  --consensus labels/consenso-v1/consenso-releases.csv `
  --predictions labels/consenso-v1/previsoes-v2.csv `
  --heuristic-version v2 `
  --output labels/consenso-v1/avaliacao-v2.json
```

O JSON contém matriz de confusão (linhas=consenso, colunas=heurística),
precisão, recall, F1, contagens excluídas e hashes das entradas. Ele também
contém `heuristic_version` e `f1` no topo e pode ser fornecido à exportação das
variantes por `--heuristic-evaluation`. Para cada refinamento, gere um novo
arquivo de avaliação; não altere rótulos para elevar F1 e registre o viés de
ajuste à mesma amostra. Se F1 < 0,70, o relatório marca refinamento necessário.

O sorteio anterior em `labels/amostra_ouro_sorteio.json` registra 283 releases,
não as 300 exigidas. Preserve esse artefato e suas planilhas. A nova amostra
deve ficar em `labels/reamostragem-v2/`; todos os três avaliadores precisam
rotulá-la de forma independente antes do cálculo de concordância e do consenso.
