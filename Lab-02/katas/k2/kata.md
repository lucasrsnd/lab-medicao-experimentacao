# Kata K2 — Sistema de Reservas (Conflito de Intervalos)

> Dono: Davi — Issue "Escolha e validação dos 6 katas" (Milestone Lab02S01). Preencher antes da execução (Milestone Lab02S02).

## Enunciado
Dada uma lista de tuplas representando horários de início e fim de reuniões (ex: `[(10, 12), (11, 13), (14, 15)]`), crie uma função que retorne `True` se houver algum conflito de horário (sobreposição) entre qualquer par de reuniões, e `False` caso todas possam ocorrer no mesmo espaço.

## Critérios de aceitação
*   Retornar `False` para uma lista de horários sem sobreposição.
*   Retornar `True` para uma lista onde um horário termina depois do início do próximo.
*   Retornar `False` para reuniões adjacentes (ex: `(10, 12)` e `(12, 14)` não conflitam).
*   Lidar com listas vazias ou com apenas uma reunião.

## Dificuldade estimada
Média (Ordenação e comparação de tuplas).