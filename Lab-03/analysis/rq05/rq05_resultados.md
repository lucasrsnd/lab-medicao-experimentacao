# RQ05 — Frequência de deploy × CFR (Spearman)

Repositórios na tabela-base: 183. α = 0.05; p ajustado por Holm sobre os 2 testes.

| Variante | n pareado | excluídos (ausentes) | ρ | p | p (Holm) | força | CFR = 0 |
|---|---:|---:|---:|---:|---:|---|---:|
| CFR (a) — runs de CI com falha | 183 | 0 | 0.151 | 0.0414 | 0.0414 | fraca | 20 |
| CFR (b) — release seguida de corretiva em 7 dias | 172 | 11 | 0.547 | 8.77e-15 | 1.75e-14 | forte | 33 |

| Variável (n pareado) | mediana | Q1 | Q3 | IQR |
|---|---:|---:|---:|---:|
| Frequência (rel./semana) — cfr_a | 0.249 | 0.134 | 0.555 | 0.421 |
| CFR (a) — runs de CI com falha | 0.047 | 0.013 | 0.128 | 0.115 |
| Frequência (rel./semana) — cfr_b | 0.277 | 0.153 | 0.579 | 0.426 |
| CFR (b) — release seguida de corretiva em 7 dias | 0.275 | 0.109 | 0.500 | 0.391 |

Interpretação: ρ mede associação monotônica entre postos, não causalidade.
Empates em CFR = 0 usam postos médios. Ver `rq05_dispersao.png`.
