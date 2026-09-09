# Kata K4 — Validador de Política de Senhas

> Dono: Davi — Issue "Escolha e validação dos 6 katas" (Milestone Lab02S01). Preencher antes da execução (Milestone Lab02S02).

## Enunciado
Crie uma função que valide se uma senha é forte. Ela deve ter no mínimo 8 caracteres, conter pelo menos dois caracteres maiúsculos (que NÃO podem estar adjacentes/juntos) e não pode conter o mesmo caractere repetido 3 vezes em sequência (ex: `aaa` é inválido). Retorne um booleano.

## Critérios de aceitação
*   Validar uma senha que atende a todos os critérios perfeitamente.
*   Rejeitar senhas com menos de 8 caracteres.
*   Rejeitar senhas onde duas letras maiúsculas aparecem juntas.
*   Rejeitar senhas com uma tripla repetição de qualquer caractere.

## Dificuldade estimada
Média (Validações sequenciais e regras de negócio específicas).