# Lab05 — Fontes e conta do impacto

Issue: S01-06 (#186). Responsável: @lucasrsnd. Revisor: @DaviSantos23.

> **Status:** modelo. As fontes dependem do software escolhido (#181). Toda fonte tem link e data de acesso.

## 1. Números públicos de uso **[pendente: #181]**

| Número | Valor | Fonte (link) | Acesso em | Observação (o que mede de fato) |
|---|---|---|---|---|
| Usuários / clientes | | | | |
| Downloads (PyPI, npm, Docker Hub) | | | | downloads ≠ instalações em produção |
| Ranking / popularidade (DB-Engines, Stack Overflow Survey) | | | | |
| Acessos / requisições / transações por dia ou mês | | | | |
| Empresas ou órgãos que usam | | | | |

Onde procurar: site oficial e páginas de clientes, painéis do gov.br e dados abertos, pypistats.org, npm trends, Docker Hub, DB-Engines, Stack Overflow Developer Survey e W3Techs (tecnologias web).

## 2. Conta do impacto **[pendente: resultado da S02]**

Modelo: **impacto = efeito medido × volume de uso × fator de conversão**.

| Termo | Valor | De onde vem |
|---|---|---|
| Efeito medido (unidade original, com IC 95%) | | `analysis/` (S02) |
| Volume de uso (por dia ou mês) | | seção 1 |
| Fator de conversão (ex.: ms → horas, KB → GB, CPU-s → custo) | | |
| **Impacto estimado (faixa, usando o IC)** | | |

Exemplo de redação: "A versão X respondeu em mediana 18% mais rápido (IC 95%: 12–24%). Com N consultas por dia [fonte], isso equivale a Y–Z horas de CPU por dia."

O impacto é apresentado como **faixa** (limites do IC), não como um número só.

## 3. O que **não** é possível afirmar

Checklist para a seção de limitações (validade externa):

- [ ] O ambiente do grupo (hardware, rede, carga, dados) é diferente do ambiente de produção das empresas.
- [ ] As cargas/consultas/tarefas medidas podem não representar o uso real.
- [ ] Os números públicos de uso medem outra coisa (downloads, visitas) e não o uso exato que foi medido.
- [ ] O efeito pode não ser linear em escala (cache, concorrência, limites de hardware).
- [ ] Período de medição curto ou horário específico (estudos de fora do sistema).
- [ ] Amostra de participantes não representativa (estudos com pessoas).
