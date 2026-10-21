# RQ05 — Frequência de deploy × CFR (Spearman)

Repositórios na tabela-base: 300. α = 0.05; p ajustado por Holm sobre os 2 testes.

| Variante | n pareado | excluídos (ausentes) | ρ | p | p (Holm) | força | CFR = 0 |
|---|---:|---:|---:|---:|---:|---|---:|
| CFR (a) — runs de CI com falha | 300 | 0 | 0.182 | 0.0016 | 0.0016 | fraca | 24 |
| CFR (b) — release seguida de corretiva em 7 dias | 289 | 11 | 0.567 | 5.40e-26 | 1.08e-25 | forte | 52 |

| Variável (n pareado) | mediana | Q1 | Q3 | IQR |
|---|---:|---:|---:|---:|
| Frequência (rel./semana) — cfr_a | 0.268 | 0.134 | 0.555 | 0.421 |
| CFR (a) — runs de CI com falha | 0.054 | 0.020 | 0.142 | 0.122 |
| Frequência (rel./semana) — cfr_b | 0.287 | 0.153 | 0.574 | 0.421 |
| CFR (b) — release seguida de corretiva em 7 dias | 0.292 | 0.125 | 0.522 | 0.397 |

Interpretação: ρ mede associação monotônica entre postos, não causalidade.
Empates em CFR = 0 usam postos médios. Ver `rq05_dispersao.png`.
