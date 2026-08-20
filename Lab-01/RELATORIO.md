# Relatório de Análise: Características de Repositórios Populares no GitHub

**Link do repositório/GitHub Projects:** `https://github.com/lucasrsnd/lab-medicao-experimentacao`

## 1. Introdução
Sistemas de código aberto (open-source) tornaram-se a espinha dorsal do desenvolvimento de software moderno. O sucesso e a sustentabilidade desses projetos dependem de uma comunidade ativa, maturidade do código e boas práticas de manutenção.

Neste laboratório, investigamos as principais características dos 1.000 repositórios mais populares do GitHub (medidos pelo número de estrelas). O objetivo é extrair e analisar métricas de repositório, atividades de contribuição e gestão de *issues* para entender o que define um projeto de sucesso e como diferentes ecossistemas (linguagens de programação) se comportam nesse cenário.

### 1.1 Hipóteses Informais
Antes da coleta e análise aprofundada dos dados, estabelecemos as seguintes hipóteses baseadas no senso comum do desenvolvimento de software:

* **RQ01 (Idade):** Acreditamos que sistemas muito populares sejam maduros e antigos, tendo em média mais de 5 anos de criação, tempo necessário para construir uma grande base de usuários e estrelas.
* **RQ02 (Contribuição Externa):** Espera-se que esses projetos recebam um volume massivo de contribuições externas, com a mediana de *Pull Requests* aceitas na casa dos milhares.
* **RQ03 (Releases):** A hipótese é de que projetos populares adotem práticas de integração/entrega contínua, lançando *releases* com alta frequência (várias dezenas por ano).
* **RQ04 (Atualizações):** Espera-se que a atividade seja diária ou semanal. O tempo até a última atualização (último *push*) deve ser, em sua esmagadora maioria, inferior a 7 dias.
* **RQ05 (Linguagem Primária):** Hipotetizamos que as linguagens mais comuns nesses repositórios acompanhem os relatórios de mercado (como o GitHub Octoverse), sendo dominados por JavaScript, Python, TypeScript e Go.
* **RQ06 (Gestão de Issues):** Projetos saudáveis e populares devem possuir um alto engajamento da comunidade e dos mantenedores, refletindo em um percentual de *issues* fechadas superior a 80%.
* **RQ07 (Correlação por Linguagem):** Acreditamos que repositórios escritos nas linguagens mais populares (Top 3) receberão proporcionalmente mais PRs, mais *releases* e atualizações mais frequentes, devido ao maior tamanho de suas comunidades de desenvolvedores.

## 2. Metodologia de Coleta
