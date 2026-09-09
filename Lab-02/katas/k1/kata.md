# Kata K1 — Parser de Log Customizado

> Dono: Davi — Issue "Escolha e validação dos 6 katas" (Milestone Lab02S01). Preencher antes da execução (Milestone Lab02S02).

## Enunciado
Dada uma string representando uma linha de log de servidor no formato `[YYYY-MM-DD HH:MM:SS] LEVEL IP - Mensagem`, crie uma função que faça o parse e retorne um dicionário com as chaves `timestamp`, `nivel`, `ip` e `mensagem`. Se o IP não estiver presente, a chave `ip` deve receber `None`.

## Critérios de aceitação
*   Fazer o parse correto de uma linha completa válida.
*   Tratar corretamente uma linha que não possui o IP informado (ex: `... LEVEL - Mensagem`).
*   Retornar um dicionário vazio caso a string de entrada seja vazia ou mal formatada.

## Dificuldade estimada
Média (Manipulação de strings e dicionários, sem algoritmos complexos).