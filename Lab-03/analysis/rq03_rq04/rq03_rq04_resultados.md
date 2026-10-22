# RQ03–04 — CFR e recuperação

Base congelada: 300 repositórios. n válido é o número de repositórios com valor observado; ausentes não são convertidos em zero.

| Métrica | n válido | ausentes | mediana | Q1 | Q3 | IQR |
|---|---:|---:|---:|---:|---:|---:|
| CFR (a) — falha de CI | 300 | 0 | 0.054 | 0.020 | 0.142 | 0.122 |
| CFR (b) — release seguida de corretiva | 289 | 11 | 0.292 | 0.125 | 0.522 | 0.397 |
| Recuperação (horas) | 268 | 32 | 4.894 | 0.844 | 21.483 | 20.639 |

## Censura

| Processo | repositórios com contagens | com eventos | sem eventos | ausentes | eventos observados | censurados | total | proporção agrupada | mediana das proporções por repositório | Q1–Q3 | IQR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Releases CFR (b) | 300 | 291 | 9 | 0 | 8267 | 251 | 8518 | 0.029 | 0.000 | 0.000–0.024 | 0.024 |
| Episódios de recuperação | 300 | 270 | 30 | 0 | 4044 | 75 | 4119 | 0.018 | 0.000 | 0.000–0.000 | 0.000 |

## Interpretação e validação

CFR (a) mede a proporção de execuções válidas de CI que falharam; CFR (b) marca releases predecessoras de uma release corretiva dentro de sete dias. São proxies operacionais distintos e sua divergência não demonstra falha nem sucesso em produção. Para CFR (b), a heurística deve ser interpretada à luz de rótulos humanos do mesmo dataset; a concordância entre avaliadores sozinha não substitui a avaliação da heurística.

Estado da validação vinculada: **source_matches**. origem compatível; F1 de avaliador único, sem consenso, em analysis/validacao_cfr_b. F1 da heurística: —; consenso: ausente. Hashes SHA-256 (amostra-ouro/fonte congelada): `bbc652390d9f` / `bbc652390d9f`.

Nos repositórios com ambos os CFR observados (n=289), a mediana da diferença CFR (b) − CFR (a) é 0.200 (IQR 0.409). A diferença é descritiva, não uma comparação de falhas em produção.

Recuperação reporta a mediana entre episódios recuperados por repositório; episódios censurados permanecem no denominador das proporções e não são imputados como tempos de recuperação.
