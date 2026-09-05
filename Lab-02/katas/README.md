# Katas do experimento

> Dono: Davi — Issues "Escolha e validação dos 6 katas" e "Scaffold dos testes
> de aceitação" da Milestone `Lab02S01` no GitHub Projects.

## Estrutura por kata

```
katas/kXX/
├── kata.md        # enunciado do kata + critérios de aceitação
├── com_ia/        # trial(s) resolvido(s) com assistente de IA habilitado
│   └── <integrante>/
└── sem_ia/        # trial(s) resolvido(s) sem assistente de IA
    └── <integrante>/
```

Cada trial individual (Milestone `Lab02S02`) vive em
`katas/kXX/{com_ia,sem_ia}/<integrante>/`, com o código produzido no time-box e
os testes de aceitação (pytest) que definem "time-to-green" para aquele kata.

## Tratamento por integrante e kata

Tabela de contrabalanceamento sugerida (Milestone `Lab02S02`, 18 trials = 6 katas × 3 integrantes):

| Kata | Gustavo | Lucas | Davi |
|---|---|---|---|
| K1 | Com IA | Sem IA | Com IA |
| K2 | Com IA | Sem IA | Sem IA |
| K3 | Com IA | Sem IA | Com IA |
| K4 | Sem IA | Com IA | Sem IA |
| K5 | Sem IA | Com IA | Com IA |
| K6 | Sem IA | Com IA | Sem IA |

- Gustavo e Lucas ficam em **blocos invertidos** (K1–K3 vs. K4–K6) — controla
  efeito de aprendizado ao longo da sessão sem confundir kata×tratamento.
- Davi **intercala** kata a kata — cada kata acaba testado com e sem IA por
  pelo menos duas pessoas diferentes.
- Dentro de cada bloco, alternar também **a ordem** dos trials entre os três
  (quem começa com IA, quem começa sem) para não confundir ordem com tratamento.

## Katas

| Kata | Tema | Status |
|---|---|---|
| k1 | _a definir (Issue "Escolha e validação dos 6 katas")_ | ⬜ |
| k2 | _a definir (Issue "Escolha e validação dos 6 katas")_ | ⬜ |
| k3 | _a definir (Issue "Escolha e validação dos 6 katas")_ | ⬜ |
| k4 | _a definir (Issue "Escolha e validação dos 6 katas")_ | ⬜ |
| k5 | _a definir (Issue "Escolha e validação dos 6 katas")_ | ⬜ |
| k6 | _a definir (Issue "Escolha e validação dos 6 katas")_ | ⬜ |
