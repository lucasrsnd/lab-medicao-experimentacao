# RQ03–04 — CFR e recuperação

Base congelada: 183 repositórios. n válido é o número de repositórios com valor observado; ausentes não são convertidos em zero.

| Métrica | n válido | ausentes | mediana | Q1 | Q3 | IQR |
|---|---:|---:|---:|---:|---:|---:|
| CFR (a) — falha de CI | 183 | 0 | 0.047 | 0.013 | 0.128 | 0.115 |
| CFR (b) — release seguida de corretiva | 172 | 11 | 0.275 | 0.109 | 0.500 | 0.391 |
| Recuperação (horas) | 158 | 25 | 3.490 | 0.861 | 17.772 | 16.911 |

## Censura

| Processo | repositórios com contagens | com eventos | sem eventos | ausentes | eventos observados | censurados | total | proporção agrupada | mediana das proporções por repositório | Q1–Q3 | IQR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Releases CFR (b) | 183 | 174 | 9 | 0 | 4613 | 149 | 4762 | 0.031 | 0.000 | 0.000–0.021 | 0.021 |
| Episódios de recuperação | 183 | 158 | 25 | 0 | 2649 | 46 | 2695 | 0.017 | 0.000 | 0.000–0.000 | 0.000 |

## Interpretação e validação

CFR (a) mede a proporção de execuções válidas de CI que falharam; CFR (b) marca releases predecessoras de uma release corretiva dentro de sete dias. São proxies operacionais distintos e sua divergência não demonstra falha nem sucesso em produção. Para CFR (b), a heurística deve ser interpretada à luz de rótulos humanos do mesmo dataset; a concordância entre avaliadores sozinha não substitui a avaliação da heurística.

Estado da validação vinculada: **not_linked_to_frozen_dataset**. hash de origem da amostra-ouro difere do dataset congelado. F1 da heurística: —; consenso: ausente. Hashes SHA-256 (amostra-ouro/fonte congelada): `87656c1c9637` / `3e66a07889dc`.

Nos repositórios com ambos os CFR observados (n=172), a mediana da diferença CFR (b) − CFR (a) é 0.182 (IQR 0.401). A diferença é descritiva, não uma comparação de falhas em produção.

Recuperação reporta a mediana entre episódios recuperados por repositório; episódios censurados permanecem no denominador das proporções e não são imputados como tempos de recuperação.
