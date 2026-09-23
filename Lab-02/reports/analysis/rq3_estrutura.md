# RQ3 — Estrutura do código (complexidade e duplicação)

RQ3: O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido?

## Cenário: Todos os trials

### Complexidade ciclomática média por função (Radon cc)

| Tratamento | N | Mediana (CC) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 5.00 | 2.00 | 3.00 | 9.00 |
| sem_ia | 9 | 4.00 | 5.00 | 3.00 | 11.00 |

- Wilcoxon pareado por integrante (N=3 pares): estatística = 0.000, p-valor = 1.0000
- Wilcoxon pareado por kata (N=6 pares): estatística = 5.000, p-valor = 1.0000

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 4.50 | 11.00 |
| k2 | 5.00 | 3.00 |
| k3 | 7.00 | 4.00 |
| k4 | 9.00 | 9.00 |
| k5 | 3.50 | 4.00 |
| k6 | 4.00 | 4.00 |

### Duplicação de código (jscpd)

| Tratamento | N | Mediana (%) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 0.00 | 0.00 | 0.00 | 0.00 |
| sem_ia | 9 | 0.00 | 0.00 | 0.00 | 0.00 |

- Wilcoxon pareado por integrante (N=3 pares): estatística = 0.000, p-valor = 1.0000
- Wilcoxon pareado por kata (N=6 pares): estatística = 0.000, p-valor = 1.0000

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 0.00 | 0.00 |
| k2 | 0.00 | 0.00 |
| k3 | 0.00 | 0.00 |
| k4 | 0.00 | 0.00 |
| k5 | 0.00 | 0.00 |
| k6 | 0.00 | 0.00 |

### SLOC — métrica de controle

| Tratamento | N | Mediana (linhas) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 14.00 | 5.00 | 9.00 | 19.00 |
| sem_ia | 9 | 11.00 | 4.00 | 6.00 | 29.00 |

Outliers (regra IQR): 1 ponto(s) — lucasrsnd/k1/sem_ia

- Wilcoxon pareado por integrante (N=3 pares): estatística = 0.000, p-valor = 0.5000
- Wilcoxon pareado por kata (N=6 pares): estatística = 5.000, p-valor = 0.5625

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 17.00 | 29.00 |
| k2 | 10.00 | 7.00 |
| k3 | 16.00 | 11.00 |
| k4 | 15.00 | 14.50 |
| k5 | 9.00 | 9.00 |
| k6 | 11.00 | 10.50 |

### Complexidade normalizada por LOC (CC por 10 SLOC)

| Tratamento | N | Mediana (CC/10 SLOC) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 4.29 | 1.11 | 2.63 | 6.00 |
| sem_ia | 9 | 4.00 | 1.25 | 3.64 | 6.92 |

Outliers (regra IQR): 1 ponto(s) — DaviSantos23/k4/sem_ia

- Wilcoxon pareado por integrante (N=3 pares): estatística = 1.000, p-valor = 1.0000
- Wilcoxon pareado por kata (N=6 pares): estatística = 9.000, p-valor = 0.8438

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 2.65 | 3.79 |
| k2 | 5.00 | 4.38 |
| k3 | 4.37 | 3.64 |
| k4 | 6.00 | 6.27 |
| k5 | 3.89 | 4.44 |
| k6 | 3.64 | 3.82 |

### Índice de Manutenibilidade (Radon mi, opcional)

| Tratamento | N | Mediana (MI) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 66.45 | 13.66 | 57.05 | 100.00 |
| sem_ia | 9 | 75.16 | 35.14 | 52.91 | 100.00 |

Outliers (regra IQR): 1 ponto(s) — lucasrsnd/k6/com_ia

- Wilcoxon pareado por integrante (N=3 pares): estatística = 2.000, p-valor = 0.7500
- Wilcoxon pareado por kata (N=6 pares): estatística = 4.000, p-valor = 0.4375

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 68.79 | 52.91 |
| k2 | 63.85 | 73.88 |
| k3 | 58.72 | 64.86 |
| k4 | 58.20 | 72.73 |
| k5 | 75.29 | 100.00 |
| k6 | 100.00 | 100.00 |

> N=3 (por integrante) e N=6 (por kata) são amostras muito pequenas para poder estatístico — interpretar o p-valor com cautela na discussão.

## Cenário: Excluindo outliers de instrumentação

### Complexidade ciclomática média por função (Radon cc)

| Tratamento | N | Mediana (CC) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 5.00 | 2.00 | 3.00 | 9.00 |
| sem_ia | 8 | 4.00 | 5.00 | 3.00 | 11.00 |

- Wilcoxon pareado por integrante (N=3 pares): estatística = 1.000, p-valor = 1.0000
- Wilcoxon pareado por kata (N=6 pares): estatística = 5.000, p-valor = 1.0000

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 4.50 | 11.00 |
| k2 | 5.00 | 3.00 |
| k3 | 7.00 | 4.00 |
| k4 | 9.00 | 9.00 |
| k5 | 3.50 | 4.00 |
| k6 | 4.00 | 4.00 |

### Duplicação de código (jscpd)

| Tratamento | N | Mediana (%) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 0.00 | 0.00 | 0.00 | 0.00 |
| sem_ia | 8 | 0.00 | 0.00 | 0.00 | 0.00 |

- Wilcoxon pareado por integrante (N=3 pares): estatística = 0.000, p-valor = 1.0000
- Wilcoxon pareado por kata (N=6 pares): estatística = 0.000, p-valor = 1.0000

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 0.00 | 0.00 |
| k2 | 0.00 | 0.00 |
| k3 | 0.00 | 0.00 |
| k4 | 0.00 | 0.00 |
| k5 | 0.00 | 0.00 |
| k6 | 0.00 | 0.00 |

### SLOC — métrica de controle

| Tratamento | N | Mediana (linhas) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 14.00 | 5.00 | 9.00 | 19.00 |
| sem_ia | 8 | 11.00 | 4.00 | 6.00 | 29.00 |

Outliers (regra IQR): 1 ponto(s) — lucasrsnd/k1/sem_ia

- Wilcoxon pareado por integrante (N=3 pares): estatística = 0.000, p-valor = 0.5000
- Wilcoxon pareado por kata (N=6 pares): estatística = 5.000, p-valor = 0.5625

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 17.00 | 29.00 |
| k2 | 10.00 | 6.00 |
| k3 | 16.00 | 11.00 |
| k4 | 15.00 | 14.50 |
| k5 | 9.00 | 9.00 |
| k6 | 11.00 | 10.50 |

### Complexidade normalizada por LOC (CC por 10 SLOC)

| Tratamento | N | Mediana (CC/10 SLOC) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 4.29 | 1.11 | 2.63 | 6.00 |
| sem_ia | 8 | 4.22 | 1.40 | 3.64 | 6.92 |

- Wilcoxon pareado por integrante (N=3 pares): estatística = 1.000, p-valor = 1.0000
- Wilcoxon pareado por kata (N=6 pares): estatística = 4.000, p-valor = 0.4375

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 2.65 | 3.79 |
| k2 | 5.00 | 5.00 |
| k3 | 4.37 | 3.64 |
| k4 | 6.00 | 6.27 |
| k5 | 3.89 | 4.44 |
| k6 | 3.64 | 3.82 |

### Índice de Manutenibilidade (Radon mi, opcional)

| Tratamento | N | Mediana (MI) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 66.45 | 13.66 | 57.05 | 100.00 |
| sem_ia | 8 | 78.84 | 36.26 | 52.91 | 100.00 |

Outliers (regra IQR): 1 ponto(s) — lucasrsnd/k6/com_ia

- Wilcoxon pareado por integrante (N=3 pares): estatística = 2.000, p-valor = 0.7500
- Wilcoxon pareado por kata (N=6 pares): estatística = 4.000, p-valor = 0.4375

| Kata | Mediana Com IA | Mediana Sem IA |
|---|---|---|
| k1 | 68.79 | 52.91 |
| k2 | 63.85 | 72.60 |
| k3 | 58.72 | 64.86 |
| k4 | 58.20 | 72.73 |
| k5 | 75.29 | 100.00 |
| k6 | 100.00 | 100.00 |

> N=3 (por integrante) e N=6 (por kata) são amostras muito pequenas para poder estatístico — interpretar o p-valor com cautela na discussão.
