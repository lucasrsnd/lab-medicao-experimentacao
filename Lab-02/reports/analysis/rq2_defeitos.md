# RQ2 — Defeitos (testes falhando)

RQ2: O uso de assistente de IA reduz a quantidade de defeitos (testes que falham) no código produzido?

## Cenário: Todos os trials

### Taxa de sucesso (% testes passando)

| Tratamento | N | Mediana (%) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 100.00 | 0.00 | 100.00 | 100.00 |
| sem_ia | 9 | 100.00 | 0.00 | 0.00 | 100.00 |

Outliers (regra IQR): 1 ponto(s) — DaviSantos23/k2/sem_ia

Wilcoxon pareado por integrante (N=3 pares): 
estatística = 0.000, p-valor = 1.0000

### Nº de testes falhando

| Tratamento | N | Mediana (testes) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 0.00 | 0.00 | 0.00 | 0.00 |
| sem_ia | 9 | 0.00 | 0.00 | 0.00 | 2.00 |

Outliers (regra IQR): 1 ponto(s) — DaviSantos23/k2/sem_ia

Wilcoxon pareado por integrante (N=3 pares): 
estatística = 0.000, p-valor = 1.0000

> N=3 (um par por integrante) é uma amostra muito pequena para poder estatístico — interpretar o p-valor com cautela na discussão.

## Cenário: Excluindo outliers de instrumentação

### Taxa de sucesso (% testes passando)

| Tratamento | N | Mediana (%) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 100.00 | 0.00 | 100.00 | 100.00 |
| sem_ia | 8 | 100.00 | 0.00 | 100.00 | 100.00 |

Wilcoxon pareado por integrante (N=3 pares): 
estatística = 0.000, p-valor = 1.0000

### Nº de testes falhando

| Tratamento | N | Mediana (testes) | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 0.00 | 0.00 | 0.00 | 0.00 |
| sem_ia | 8 | 0.00 | 0.00 | 0.00 | 0.00 |

Wilcoxon pareado por integrante (N=3 pares): 
estatística = 0.000, p-valor = 1.0000

> N=3 (um par por integrante) é uma amostra muito pequena para poder estatístico — interpretar o p-valor com cautela na discussão.
