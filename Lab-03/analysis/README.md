# Análises da S03

Cada análise é um script reexecutável a partir de `base_repositorios.csv`,
que por sua vez é derivado do dataset congelado da coleta completa.

```powershell
python -m pip install -e ".[dev,analysis]"
python -m lab03.analysis.reproduce # tudo abaixo, mais analysis/MANIFESTO.json (--check compara com ele)
python -m lab03.analysis.base      # data/amostra_completa.json.gz -> analysis/base_repositorios.csv
python -m lab03.analysis.rq01_rq02 # analysis/rq01_rq02/
python -m lab03.analysis.rq03_rq04 # analysis/rq03_rq04/
python -m lab03.analysis.c1_reference # analysis/c1_reference/
python -m lab03.analysis.rq05      # analysis/rq05/
python -m lab03.analysis.rq06      # analysis/rq06/
python -m lab03.analysis.cfr_b_validation  # dataset + labels/ -> analysis/validacao_cfr_b/
```

## `base_repositorios.csv`

Uma linha por repositório (chave `repositorio`). Célula vazia é ausência; `0`
é valor observado.

| Coluna | Unidade | Origem no relatório |
|---|---|---|
| `estrelas`, `linguagem`, `contribuidores`, `idade_dias` | contagem / texto / dias | `metadata` |
| `deployment_frequency_per_week`, `releases_in_window`, `deployment_frequency_weeks` | releases/semana, contagem, semanas | `deployment_frequency` |
| `lead_time_a_hours`, `lead_time_b_hours`, `lead_time_a_releases`, `lead_time_b_commits` | horas, releases, commits | `lead_time` |
| `cfr_a`, `cfr_a_runs` | proporção [0,1], runs | `ci_failure_rate` |
| `cfr_b`, `cfr_b_evaluated`, `cfr_b_censored` | proporção [0,1], releases | `delivery_failure_rate` (heurística v2) |
| `recovery_hours`, `recovery_episodes`, `recovery_episodes_censored` | horas, episódios recuperados e censurados | `recovery` |
| `categoria_geral_c1` | Elite/High/Medium/Low ou vazio | `dora_classification.overall` |

O CFR (b) vem do relatório de cada repositório (releases publicadas, C1), e não
da linha C2 de `variantes_metricas.csv`, que depende do complemento de
pré-releases ainda não coletado.

## RQ01–04 e classificação C1

`rq01_rq02` reproduz frequência e lead time (a/b), com mediana, IQR, n válido,
ausentes e gráfico que preserva todos os outliers. `rq03_rq04` compara CFR (a/b)
e recuperação, inclui n válido e proporções agrupadas e por repositório para as
censuras. A seção identifica CFR (a) como proxy de falha de CI e CFR (b) como
proxy de release corretiva; nenhum deles é tratado como observação de falha em
produção. A validação humana só é considerada evidência para esta base quando
o hash de origem da amostra-ouro coincide com o dataset congelado.
Esse estado (`not_linked_to_frozen_dataset`) diz respeito à validação do
protocolo, com consenso sobre a `reamostragem-v2`, que não foi feita. A
validação parcial, com um avaliador sobre a 1ª rodada, está em
`validacao_cfr_b/` e é descrita abaixo.

`c1_reference` aplica o classificador já testado às quatro métricas C1, exporta
categoria e status por repositório, distribuição de categorias e contagem de
não classificáveis. Também verifica que a classificação geral reproduz a
categoria previamente armazenada na base.

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

## RQ06 — subgrupos (`rq06/`)

Fatores pré-registrados no protocolo: linguagem principal, quartis de estrelas
e quartis de contribuidores. Métricas de referência C1: frequência, lead time
(a), CFR (a) e recuperação. São 3 × 4 = 12 testes Kruskal-Wallis (todos os fatores
têm 3+ grupos) com ε² = H/(n−1), corrigidos juntos por Holm. Para fatores com
dois grupos, o script usa Mann-Whitney e Cliff δ. Cada teste usa só os
repositórios com a métrica observada, por isso n varia: 183 em frequência e
CFR, 172 em lead time e 158 em recuperação.

Decisões:

- Linguagens com menos de 10 repositórios são agrupadas em "Outras" (40
  repositórios, 13 linguagens). Isso evita grupos com n de 1 a 9, em que
  Kruskal-Wallis fica instável. O preço é um grupo heterogêneo, e isso conta
  como ameaça à validade.
- Os quartis vêm dos cortes amostrais, com empate no corte indo para o quartil
  inferior. Os cortes e tamanhos (45 ou 46 por grupo) estão em `rq06_resultados.md`.
- Tipo de projeto **não** é fator. Não foi escolhido no protocolo, e o rótulo
  só existe para os 60 repositórios da amostra-ouro, então não é extrapolado.
- Empates (por exemplo CFR = 0) usam a correção de empates do `scipy.stats.kruskal`.

Resultado: nenhum dos 12 testes é significativo após Holm. O mais próximo é
contribuidores × lead time (a), com H = 13,03, p = 0,005 e p (Holm) = 0,055,
ε² = 0,076 (pequeno): o lead time mediano cresce de 131 h (Q1) para 443 h (Q3)
e 289 h (Q4). Os demais efeitos são desprezíveis ou pequenos (ε² ≤ 0,061).
Nesta amostra de repositórios populares, linguagem, popularidade e tamanho da
comunidade explicam pouco da variação das métricas DORA. A ausência de
significância não prova ausência de efeito, porque os grupos têm de 13 a 46
repositórios.

## Validação do CFR (b) — avaliador único (`validacao_cfr_b/`)

Desvio do protocolo, por decisão do grupo: a `labels/reamostragem-v2/` não foi
rotulada, e na 1ª rodada (`labels/amostra_ouro_*`) só o avaliador B rotulou.
Os rótulos de A são rascunhos de IA (todas as linhas trazem `[rascunho IA]`).
Por isso não existe consenso. A referência é B, e A entra só como referência
auxiliar declarada (LLM), nunca como segundo avaliador.

A 1ª rodada saiu da mesma coleta do snapshot (13/10/2026, mesma janela), mas
sorteada sobre mais repositórios. Só entram releases cujo repositório está no
snapshot e cujo `release_id` e veredito conferem: 178 de 283 releases, em 37
dos 58 repositórios com releases sorteadas. As 105 restantes são de 21
repositórios fora dos 183.

Resultado (heurística v2 × B, `resultados.md`): precisão 0,234 (IC 95% de
Wilson 0,165–0,321), recall 0,929 (0,774–0,980), F1 0,374. Entre as 111
releases marcadas como corretivas pela heurística, B confirmou 26. Das 28
corretivas segundo B, a heurística perdeu 2. O F1 fica abaixo do limiar de
0,70 do protocolo, e o viés é de **superestimação** do CFR (b). Auxiliar: κ de
Cohen B × LLM = 0,506. Os intervalos ignoram o agrupamento de releases por
repositório e por isso são otimistas.
