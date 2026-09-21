# RQ1 — Tempo (time-to-green)

RQ1: O uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação?

## Cenário: Todos os trials

### Mediana/IQR por tratamento (minutos)

| Tratamento | N | Mediana | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 3.17 | 1.92 | 1.40 | 8.31 |
| sem_ia | 9 | 11.37 | 13.24 | 9.06 | 35.00 |

### Censura (time-box atingido sem sucesso)

| Tratamento | Trials | Censurados |
|---|---|---|
| com_ia | 9 | 0 |
| sem_ia | 9 | 1 |

### Outliers (regra IQR, por tratamento)

- gustavoprehl / k1 / com_ia: 8.31min

### Wilcoxon pareado por integrante (N=3 pares)

| Integrante | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| DaviSantos23 | 1.67 | 19.57 |
| gustavoprehl | 6.68 | 10.55 |
| lucasrsnd | 3.65 | 11.37 |

**Estatística** = 0.000, **p-valor** = 0.2500

> N=3 (um par por integrante) é uma amostra muito pequena para poder estatístico — interpretar o p-valor com cautela na discussão.

## Cenário: Excluindo outliers de instrumentação

### Mediana/IQR por tratamento (minutos)

| Tratamento | N | Mediana | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 3.17 | 1.92 | 1.40 | 8.31 |
| sem_ia | 8 | 10.96 | 10.62 | 9.06 | 25.12 |

### Censura (time-box atingido sem sucesso)

| Tratamento | Trials | Censurados |
|---|---|---|
| com_ia | 9 | 0 |
| sem_ia | 8 | 0 |

### Outliers (regra IQR, por tratamento)

- gustavoprehl / k1 / com_ia: 8.31min

### Wilcoxon pareado por integrante (N=3 pares)

| Integrante | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| DaviSantos23 | 1.67 | 14.50 |
| gustavoprehl | 6.68 | 10.55 |
| lucasrsnd | 3.65 | 11.37 |

**Estatística** = 0.000, **p-valor** = 0.2500

> N=3 (um par por integrante) é uma amostra muito pequena para poder estatístico — interpretar o p-valor com cautela na discussão.
