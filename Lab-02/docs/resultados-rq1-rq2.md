# Resultados — RQ1 (Tempo) e RQ2 (Defeitos)

> Dono: Gustavo — Issues [S03] "RQ1 — Tempo", "RQ2 — Defeitos" e "Resultados
> por RQ" (Milestone `Lab02-RelatorioFinal`). RQ3 é do Lucas, seção separada.
>
> Fonte dos números: `reports/analysis/rq1_tempo.{md,json}` e
> `reports/analysis/rq2_defeitos.{md,json}`, gerados por
> `src/analysis/rq1_tempo.py` e `src/analysis/rq2_defeitos.py` a partir de
> `data/raw/trials_tempo.csv` (18 trials — 6 katas × 3 integrantes).
>
> **Este texto é o rascunho pronto pra colar na seção "Resultados por RQ" do
> relatório final** — ainda falta o grupo decidir o item da "Nota
> metodológica" abaixo antes de considerar definitivo.

## RQ1 — O uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação?

Considerando os 18 trials coletados, a mediana do tempo até "time-to-green"
foi de **3.17 min** nos trials Com IA (N=9) contra **11.37 min** nos trials
Sem IA (N=9) — uma redução considerável na mediana bruta. Houve 1 trial
censurado (time-box de 35 min atingido sem sucesso), no tratamento Sem IA.

Como o desenho não pareia trial-a-trial (cada kata é resolvido por
integrantes diferentes em tratamentos diferentes — ver `katas/README.md`), o
teste de Wilcoxon foi aplicado pareando **por integrante**: mediana dos 3
trials Com IA de cada pessoa vs. mediana dos 3 Sem IA da mesma pessoa (N=3
pares). Resultado: **estatística = 0.0, p = 0.25** — o maior nível de
significância possível com N=3 no teste exato (não atinge o limiar
convencional de 0.05), mas **os três integrantes individualmente foram mais
rápidos Com IA que Sem IA**, uma direção consistente entre todos os pares
apesar do N pequeno não permitir conclusão estatística forte.

| Integrante | Mediana Com IA (min) | Mediana Sem IA (min) |
|---|---|---|
| Davi | 1.67 | 19.57 |
| Gustavo | 6.68 | 10.55 |
| Lucas | 3.65 | 11.37 |

## RQ2 — O uso de assistente de IA reduz a quantidade de defeitos (testes que falham) no código produzido?

A taxa de sucesso mediana foi de **100%** nos dois tratamentos — praticamente
todos os trials fecharam com todos os testes de aceitação passando ao final
do time-box, independentemente do uso de IA. O Wilcoxon pareado por
integrante (N=3) resultou em **p = 1.0** (nenhuma diferença detectável).
Diferente da RQ1, aqui os dados não sugerem nenhum efeito do assistente de IA
sobre a taxa de defeitos nesta amostra — resultado negativo, mas relevante
para a discussão (produtividade vs. qualidade funcional não caminharam
juntas nos dados coletados).

## Nota metodológica — pendente de alinhamento com o grupo

Um trial (Davi, K2 Sem IA) foi registrado como censurado (35min, 0/2 testes)
por um bug de infraestrutura (colisão de import do pytest, corrigida no
commit `9a79389`) — rodando o mesmo código isoladamente após a correção, ele
passa 3/3. Os números acima usam **todos os 18 trials, incluindo esse
ponto**; a análise também foi rodada excluindo-o (ver
`reports/analysis/rq1_tempo.json`/`rq2_defeitos.json`, chave
`excluindo_outliers_instrumentacao`), com resultado qualitativamente igual
(mediana Sem IA cai de 11.37 para 10.96min, ainda maior que Com IA; p-valores
inalterados). **O grupo precisa decidir e registrar no relatório qual
cenário é o oficial** (incluir com nota de limitação, ou excluir/re-rodar o
trial) antes da entrega.

## Limitações a registrar na Discussão

- **N=3 pares** no Wilcoxon (um por integrante) é uma amostra muito pequena
  — poder estatístico baixo, resultados devem ser lidos como indicativos, não
  conclusivos.
- Outlier em RQ1 (Com IA): Gustavo/K1, 8.31min, dentro da faixa "Com IA" mas
  destoante dos outros dois trials do próprio Gustavo nesse tratamento — não
  removido da análise (critério de outlier aplicado é só a regra IQR
  automática, documentada em `src/analysis/stats_utils.py`).
