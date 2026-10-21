# Validação parcial do CFR (b) — avaliador único

**Desvio do protocolo:** Avaliador humano único (B); sem consenso. Rótulos de A são rascunhos de IA e entram só como referência auxiliar declarada.

Heurística v2. Releases avaliadas: 283 de 283 (58 de 58 repositórios). Excluídas: nenhuma. Corretivas segundo B: 46.

| Referência B \ Heurística | não | sim |
|---|---:|---:|
| não | 109 | 128 |
| sim | 6 | 40 |

| Métrica | valor | IC 95% (Wilson) |
|---|---:|---|
| Precisão | 0.238 | [0.180; 0.308] |
| Recall | 0.870 | [0.743; 0.939] |
| F1 | 0.374 | — |
| Acurácia | 0.527 | — |

## Referência auxiliar (LLM, não é avaliador)

283 rótulos de A marcados `[rascunho IA]`. κ de Cohen B × LLM = 0.590 (concordância 0.883). Heurística × LLM: precisão 0.298, recall 0.980, F1 0.457.

## Limitações

- Um único avaliador humano: sem medida de confiabilidade entre avaliadores.
- Releases sorteadas de uma população maior que o snapshot; só os repositórios presentes no snapshot são avaliados.
- Releases do mesmo repositório não são independentes; os intervalos de Wilson ignoram esse agrupamento e tendem a ser estreitos demais.
