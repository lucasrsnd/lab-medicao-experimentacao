# RQ01–02 — Frequência e lead time

Base congelada: 300 repositórios. Estatísticas calculadas entre valores por repositório; ausentes não são imputados.

| Métrica | n válido | ausentes | mediana | Q1 | Q3 | IQR |
|---|---:|---:|---:|---:|---:|---:|
| Frequência (releases/semana) | 300 | 0 | 0.268 | 0.134 | 0.555 | 0.421 |
| Lead time (a), por release (horas) | 289 | 11 | 250.820 | 70.317 | 756.463 | 686.145 |
| Lead time (b), por commit (horas) | 289 | 11 | 169.439 | 53.942 | 545.988 | 492.047 |

## Interpretação

A frequência é calculada por repositório como releases na janela divididas pela duração observada em semanas. As variantes de lead time também são resumidas entre repositórios: (a) primeiro resume releases dentro de cada repositório; (b) primeiro resume commits dentro de cada repositório. A variante (a) dá peso a cada release e pode aumentar quando uma release inclui um commit antigo; a (b) agrega os commits e reduz o peso relativo desse commit quando há muitos commits recentes.

Diferença entre as medianas (a − b): 81.381 horas. Isso descreve distribuições agregadas por repositório e não significa que cada repositório tenha a mesma diferença.

Outliers: preservados; nenhum corte ou winsorização aplicado. O gráfico usa escala symlog para preservar zeros e caudas longas; todos os pontos são desenhados.
