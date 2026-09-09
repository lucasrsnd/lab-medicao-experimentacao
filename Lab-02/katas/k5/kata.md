# Kata K5 — Achatamento de Dicionário JSON

> Dono: Davi — Issue "Escolha e validação dos 6 katas" (Milestone Lab02S01). Preencher antes da execução (Milestone Lab02S02).

## Enunciado
Escreva uma função que receba um dicionário aninhado (JSON) e retorne um dicionário de um único nível, concatenando as chaves com um *underline* (`_`). Exemplo: `{"user": {"id": 1, "name": "Bob"}}` deve virar `{"user_id": 1, "user_name": "Bob"}`.

## Critérios de aceitação
*   Achatar corretamente um dicionário com apenas um nível de profundidade (não deve alterar as chaves originais).
*   Achatar um dicionário com 2 ou mais níveis de profundidade concatenando corretamente.
*   Tratar dicionários vazios retornando outro dicionário vazio.

## Dificuldade estimada
Média (Recursão e navegação em dicionários).