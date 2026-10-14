# Protocolo de validação manual (amostra-ouro) — Lab03S02

Seção 6 do enunciado. Este documento fixa o sorteio e o protocolo cego **antes**
de qualquer rótulo ser preenchido.

## 1. Coleta completa

```powershell
$env:GITHUB_TOKEN = "..."   # nunca commitar
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
python -m lab03.gold_sample --dataset data/amostra_completa.json --out labels
```

- 60 repositórios: `random.Random(42).sample` sobre os nomes ordenados
  (equivalente reproduzível a `df.sample(n=60, random_state=42)`; a ordem do
  arquivo não influencia).
- 5 releases por repositório: `random.Random(f"42:{repo}")`, entre as releases
  da janela que têm lista de commits (a primeira release histórica não tem
  comparação e não é rotulável).
- `labels/amostra_ouro_sorteio.json` registra semente, hash SHA-256 do dataset e
  janela. `labels/amostra_ouro_releases.csv` é a lista sorteada (sem rótulos).
- O comando recusa sobrescrever arquivos existentes (`--force` refaz o sorteio e
  **apaga o trabalho de rotulagem**; só usar antes de alguém começar).

## 3. Regras do protocolo cego

1. Cada avaliador (A, B, C) preenche **só** a sua planilha em `labels/`:
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
| `tipo_projeto` | `biblioteca/framework`, `aplicacao/servico`, `ferramenta CLI`, `outro` | O que o repositório principalmente entrega, lendo README e estrutura. |
| `releases_sao_entregas` | `sim`, `nao`, `incerto` | As releases chegam a usuários como entregas reais (binários, pacote publicado, versão implantável), ou são só marcos/tags sem entrega? |
| `observacoes` | texto livre | Dúvidas e motivo de `incerto`. |

Planilha de releases (uma linha por release sorteada; abrir `url_release` e
`url_comparacao`, ler release notes e a lista de commits):

| Coluna | Valores | Critério |
|---|---|---|
| `e_corretiva` | `sim`, `nao` | `sim` se o objetivo **principal** da release é corrigir um defeito recente (hotfix, revert, correção de regressão). Release que mistura novas funcionalidades e algumas correções, como é comum, é `nao`. |
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
