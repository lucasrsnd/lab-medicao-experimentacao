# Análises da S03

Cada análise é um script reexecutável a partir de `base_repositorios.csv`,
que por sua vez é derivado do dataset congelado da coleta completa.

```powershell
python -m pip install -e ".[dev,analysis]"
python -m lab03.analysis.base      # data/amostra_completa.json.gz -> analysis/base_repositorios.csv
python -m lab03.analysis.rq05      # analysis/rq05/
```

## `base_repositorios.csv`

Uma linha por repositório (chave `repositorio`). Célula vazia é ausência; `0`
é valor observado.

| Coluna | Unidade | Origem no relatório |
|---|---|---|
| `estrelas`, `linguagem`, `contribuidores`, `idade_dias` | contagem / texto / dias | `metadata` |
| `deployment_frequency_per_week`, `releases_in_window` | releases/semana, contagem | `deployment_frequency` |
| `lead_time_a_hours`, `lead_time_b_hours` | horas | `lead_time.by_release_hours`, `by_commit_hours` |
| `cfr_a`, `cfr_a_runs` | proporção [0,1], runs | `ci_failure_rate` |
| `cfr_b`, `cfr_b_evaluated`, `cfr_b_censored` | proporção [0,1], releases | `delivery_failure_rate` (heurística v2) |
| `recovery_hours`, `recovery_episodes` | horas, episódios recuperados | `recovery` |
| `categoria_geral_c1` | Elite/High/Medium/Low ou vazio | `dora_classification.overall` |

O CFR (b) vem do relatório de cada repositório (releases publicadas, C1), e não
da linha C2 de `variantes_metricas.csv`, que depende do complemento de
pré-releases ainda não coletado.

## RQ05 — frequência × CFR (`rq05/`)

Spearman entre `deployment_frequency_per_week` e cada CFR, separadamente, com
n pareado (repositórios sem a métrica são excluídos, não imputados). Os dois
p-valores recebem ajuste de Holm. Variável constante ou n < 3 deixam ρ
indefinido, com o motivo registrado. A dispersão usa eixo X `symlog`: a
frequência varia em mais de duas ordens de grandeza e tem zeros, que um log
puro descartaria.

Resultado na amostra de 183 repositórios (`rq05_resultados.md`):

- **CFR (a), CI:** ρ = 0,151, p (Holm) = 0,041, n = 183. Associação positiva
  **fraca**: repositórios que publicam mais releases têm, em postos, uma
  proporção levemente maior de runs com falha.
- **CFR (b), release corretiva:** ρ = 0,547, p (Holm) < 0,001, n = 172 (11 sem
  release avaliável). Associação positiva **forte**.

Discussão. Nenhuma das variantes apoia a leitura do DORA de que velocidade e
estabilidade andam juntas (o que exigiria ρ negativo). A força da associação
com o CFR (b) deve ser lida com cautela, pois é em parte **construída pela
própria definição**: quem publica várias releases por semana tem mais chance de
ter uma release *patch* nos 7 dias seguintes, que a heurística marca como
corretiva. Já o CFR (a) mede falha de pipeline, independente do ritmo de
releases, e por isso a associação quase desaparece. Em ambos os casos é uma
associação entre postos: não há base para afirmar que publicar mais *causa*
mais falhas. Projetos maiores ou mais ativos podem ter as duas coisas, por
exemplo. Os 33 repositórios com CFR (b) = 0 e os 20 com CFR (a) = 0 entram com
postos médios (empates).
