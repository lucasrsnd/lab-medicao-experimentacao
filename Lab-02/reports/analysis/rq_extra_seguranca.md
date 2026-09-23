# RQ extra (exploratória) — Vulnerabilidades de segurança (Bandit)

O uso de assistente de IA altera a quantidade de vulnerabilidades de segurança introduzidas no código produzido? Contribuição extra do grupo, não uma das RQ1-RQ3 fixas do enunciado.

**Resultado**: 0 vulnerabilidade(s) encontrada(s) em 18 trials (Com IA e Sem IA).

| Tratamento | N | Mediana | IQR | Mín | Máx |
|---|---|---|---|---|---|
| com_ia | 9 | 0.00 | 0.00 | 0.00 | 0.00 |
| sem_ia | 9 | 0.00 | 0.00 | 0.00 | 0.00 |

Wilcoxon pareado por integrante (N=3): estatística = 0.000, p-valor = 1.0000.

**Interpretação**: com 0 vulnerabilidades nos dois tratamentos, o teste não tem o que detectar (todas as diferenças pareadas são zero) — resultado nulo, não ausência de diferença estatisticamente comprovada. Ver `docs/resultados-seguranca.md` para a discussão completa de por que isso é esperado nesta amostra.