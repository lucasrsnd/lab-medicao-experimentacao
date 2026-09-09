# Kata K6 — Agrupamento de Anagramas por Peso

> Dono: Davi — Issue "Escolha e validação dos 6 katas" (Milestone Lab02S01). Preencher antes da execução (Milestone Lab02S02).

## Enunciado
Dada uma lista de palavras, agrupe aquelas que são anagramas entre si. Porém, a saída deve ser um dicionário onde a chave é a soma dos valores ASCII das letras do anagrama, e o valor é a lista das palavras agrupadas. (Ex: `{"abc", "cab"}` viram a chave `294: ["abc", "cab"]`).

## Critérios de aceitação
*   Agrupar anagramas simples sob a mesma chave ASCII.
*   Garantir que palavras que não são anagramas fiquem em chaves diferentes, mesmo que acidentalmente tenham a mesma soma ASCII.
*   Retornar um dicionário vazio caso a lista de entrada seja vazia.

## Dificuldade estimada
Média (Transformação de dados, ordenação e dicionários).