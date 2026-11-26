# Lab05 — Escolha do software

Issue: S01-01 (#181). Responsável: @DaviSantos23. Revisor: @gustavoprehl.

> **Decisão:** WordPress. Em 25/11/2026, o solicitante confirmou que nenhum outro grupo selecionou este software.

## Shortlist

| Candidato | Caminho de estudo possível | Evidência inicial de operação/impacto |
|---|---|---|
| **WordPress — selecionado** | Experimento controlado em uma instalação de teste: comparar a latência HTTP da mesma página com cache de página completa desligado e ligado. Códigos HTTP serão registrados para validar a coleta, não como desfecho inferencial. O dado público de adoção contextualiza o impacto; não será tratado como volume de requisições. | A versão estável mais recente consultada é 7.1.5, publicada em 18/11/2026. O showcase oficial lista 163 sites, incluindo NASA e The White House. A W3Techs estima uso em 38,4% de todos os sites e 57,3% daqueles cujo CMS é conhecido. |
| PostgreSQL | Experimento controlado com a mesma consulta e conjunto de dados, comparando execução com e sem índice. | A política oficial lista a versão 19.0, lançada em 19/11/2026. No ranking DB-Engines de novembro de 2026, aparece em 4º lugar geral, com pontuação 689,69. |
| Drupal | Experimento controlado de cache em uma instalação de teste, medindo a resposta da mesma página com configurações equivalentes. | A página oficial de releases identifica Drupal 10.6.18 como versão de correção pronta para produção. A W3Techs estima uso em 0,6% de todos os sites e lista exemplos como MIT e Europa.eu. |

O caminho de pesquisa de cada alternativa usa o software instalado e executado em um ambiente de teste; nenhum repositório público do GitHub é tratado como objeto de pesquisa.

## Evidências dos critérios para WordPress

| Critério | Evidência | Avaliação |
|---|---|---|
| **Real** | A documentação oficial descreve WordPress como software de publicação que suporta desde sites e blogs até portais e sites empresariais. A página oficial de funcionalidades afirma que ele alimenta mais de 43% da web; essa afirmação é mantida como contexto da própria organização, não como estimativa atual independente. | Produto de software existente, documentado e instalável; atende ao critério. |
| **Em operação** | WordPress 7.1.5 foi publicado em 18/11/2026. O showcase oficial lista 163 sites e apresenta, entre outros, NASA, The White House, Disney e Ubisoft. | Há versões mantidas e exemplos institucionais públicos de uso. Os exemplos do showcase são evidência de operação, não uma medida de tráfego. |
| **Alto impacto** | A W3Techs informa uso em 38,4% de todos os sites e em 57,3% dos sites cujo CMS é conhecido; a página marca os dados como atualizados em 26/11/2026. | A prevalência é um sinal quantitativo forte de alcance. A métrica não informa visitas, requisições ou instalações ativas e não permite extrapolar diretamente o efeito do experimento para horas economizadas em produção. |

## Justificativa da escolha

WordPress oferece uma intervenção mensurável para as três sprints: o estado do cache de página completa pode ser alternado em uma instalação de teste sem acessar sites de produção. A mesma página e o mesmo conteúdo podem ser medidos repetidamente, permitindo comparar a latência com o desenho pareado do [plano de análise](./plano-analise.md). A adoção pública torna o tema relevante, enquanto a execução local limita o risco e permite controle experimental. A exclusividade foi confirmada pelo solicitante; o [protocolo de coleta](./protocolo-coleta.md) da issue #183 ainda deve fixar implementação do cache, ambiente e carga.

## Fontes

Fontes consultadas em **26/11/2026 (UTC)**:

1. [WordPress — Features](https://wordpress.org/about/features/) — descrição oficial do produto e afirmação de alcance.
2. [WordPress 7.1.5 Release](https://wordpress.org/news/2026/11/wordpress-7-1-5-release/) — versão estável e data de publicação.
3. [WordPress Showcase](https://wordpress.org/showcase/) — exemplos institucionais e quantidade de sites exibidos.
4. [W3Techs — WordPress usage statistics](https://w3techs.com/technologies/details/cm-wordpress) — estimativa de uso e metodologia do levantamento.
5. [PostgreSQL — Versioning Policy](https://www.postgresql.org/support/versioning/) — versão e data de lançamento.
6. [DB-Engines — PostgreSQL](https://db-engines.com/en/system/PostgreSQL) — posição e pontuação no ranking de novembro de 2026.
7. [Drupal — Releases](https://www.drupal.org/project/drupal/releases) — release pronto para produção.
8. [W3Techs — Drupal usage statistics](https://w3techs.com/technologies/details/cm-drupal) — estimativa de uso e exemplos de sites.
