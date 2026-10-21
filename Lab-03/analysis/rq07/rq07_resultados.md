# RQ07 — Sensibilidade da classificação às variantes

Base: 300 repositórios. Só entram repositórios com categoria geral nas duas variantes; os demais são excluídos, sem imputação.

| Par | n comparado | excluídos | mudaram | % mudaram | subiram | desceram | κ ponderado (linear) |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1xC2 | 259 | 41 | 115 | 44.4 | 36 | 79 | 0.311 |
| C1xC3 | 260 | 40 | 74 | 28.5 | 59 | 15 | 0.625 |
| C2xC3 | 261 | 39 | 107 | 41.0 | 99 | 8 | 0.428 |

## C1xC2

Linhas: categoria em C1. Colunas: categoria em C2.

| | Low | Medium | High | Elite |
|---|---:|---:|---:|---:|
| Low | 10 | 13 | 1 | 0 |
| Medium | 10 | 99 | 21 | 0 |
| High | 4 | 48 | 35 | 1 |
| Elite | 0 | 4 | 13 | 0 |

Exclusões: C1_sem_categoria = 2, C2_sem_categoria = 1, ambas_sem_categoria = 38.

## C1xC3

Linhas: categoria em C1. Colunas: categoria em C3.

| | Low | Medium | High | Elite |
|---|---:|---:|---:|---:|
| Low | 13 | 10 | 1 | 0 |
| Medium | 4 | 84 | 41 | 1 |
| High | 1 | 6 | 76 | 6 |
| Elite | 0 | 0 | 4 | 13 |

Exclusões: C1_sem_categoria = 4, C3_sem_categoria = 0, ambas_sem_categoria = 36.

## C2xC3

Linhas: categoria em C2. Colunas: categoria em C3.

| | Low | Medium | High | Elite |
|---|---:|---:|---:|---:|
| Low | 13 | 7 | 5 | 0 |
| Medium | 5 | 92 | 68 | 0 |
| High | 0 | 3 | 48 | 19 |
| Elite | 0 | 0 | 0 | 1 |

Exclusões: C2_sem_categoria = 3, C3_sem_categoria = 0, ambas_sem_categoria = 36.

Leitura: a C2 usa o CFR (b), cuja validação de avaliador único ficou abaixo do limiar do protocolo (F1 < 0,70). Mudanças que envolvem a C2 podem refletir o erro da heurística, e não só a definição de entrega. Os resultados descrevem esta amostra e não implicam causalidade.
