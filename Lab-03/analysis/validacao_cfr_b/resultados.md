# Validação parcial do CFR (b) — avaliador único

**Desvio do protocolo:** Avaliador humano único (B); sem consenso. Rótulos de A são rascunhos de IA e entram só como referência auxiliar declarada.

Heurística v2. Releases avaliadas: 178 de 283 (37 de 58 repositórios). Excluídas: repositorio_fora_do_snapshot: 105. Corretivas segundo B: 28.

| Referência B \ Heurística | não | sim |
|---|---:|---:|
| não | 65 | 85 |
| sim | 2 | 26 |

| Métrica | valor | IC 95% (Wilson) |
|---|---:|---|
| Precisão | 0.234 | [0.165; 0.321] |
| Recall | 0.929 | [0.774; 0.980] |
| F1 | 0.374 | — |
| Acurácia | 0.511 | — |

## Referência auxiliar (LLM, não é avaliador)

178 rótulos de A marcados `[rascunho IA]`. κ de Cohen B × LLM = 0.506 (concordância 0.860). Heurística × LLM: precisão 0.297, recall 1.000, F1 0.458.

## Limitações

- Um único avaliador humano: sem medida de confiabilidade entre avaliadores.
- Releases sorteadas de uma população maior que o snapshot; só os repositórios presentes no snapshot são avaliados.
- Releases do mesmo repositório não são independentes; os intervalos de Wilson ignoram esse agrupamento e tendem a ser estreitos demais.
