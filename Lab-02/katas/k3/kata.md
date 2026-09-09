# Kata K3 — Cálculo de Troco com Estoque

> Dono: Davi — Issue "Escolha e validação dos 6 katas" (Milestone Lab02S01). Preencher antes da execução (Milestone Lab02S02).

## Enunciado
Crie uma função que receba o valor do troco a ser dado e um dicionário representando o estoque do caixa (ex: `{50: 1, 20: 2, 10: 5}`). A função deve retornar um dicionário com as cédulas a serem devolvidas, usando a menor quantidade de notas possível. Se não houver estoque suficiente para o troco exato, retorne `None`.

## Critérios de aceitação
*   Retornar o troco exato quando há notas suficientes de alto valor.
*   Retornar o troco exato usando notas menores quando as maiores acabam.
*   Retornar `None` quando é impossível formar o valor exato com o estoque atual.

## Dificuldade estimada
Média (Algoritmo guloso com restrição de estado).