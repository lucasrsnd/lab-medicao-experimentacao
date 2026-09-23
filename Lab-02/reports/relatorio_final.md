# Relatório de Experimento: Impacto de Assistentes de IA no Desenvolvimento de Software

**Disciplina:** Medição e Experimentação em Engenharia de Software (PUC Minas)  
**Equipa:** Davi Érico, Gustavo Prehl, Lucas Rosendo  

---

## 1. Introdução

A adoção de assistentes de Inteligência Artificial (IA) generativa transformou o panorama do desenvolvimento de software, prometendo ganhos significativos de produtividade. No entanto, é fundamental quantificar empiricamente se a velocidade de entrega compromete a qualidade estrutural e a manutenibilidade do código produzido. 

Este experimento visa avaliar o impacto do uso de IA na resolução de problemas algorítmicos (*Katas*), medindo tanto o tempo de desenvolvimento até à aprovação nos testes automáticos (*time-to-green*) quanto as métricas estáticas do código fonte gerado.

### 1.1 Hipóteses
Para guiar a análise estatística, definimos as seguintes hipóteses:
* **H1 (Tempo de Desenvolvimento):** O tratamento `com_ia` reduz significativamente o *time-to-green* em comparação com o tratamento `sem_ia`.
* **H2 (Qualidade Estrutural - Complexidade):** Não existe diferença estatisticamente significativa na Complexidade Ciclomática (McCabe) entre o código produzido com e sem o auxílio da IA.
* **H3 (Qualidade Estrutural - Duplicação):** O código gerado no tratamento `com_ia` apresenta uma taxa de duplicação igual ou inferior ao código produzido no tratamento `sem_ia`.

---

## 2. Metodologia

Para garantir a validade interna e a reprodutibilidade dos resultados, o laboratório foi estruturado sob um rigoroso protocolo de medição e isolamento de variáveis.

### 2.1 Desenho Experimental (Crossover Within-Subject)
O experimento utilizou um design *crossover within-subject*, onde os três participantes (Davi, Gustavo, Lucas) foram expostos a ambos os tratamentos (`com_ia` e `sem_ia`). Foram definidos 6 desafios de programação (Katas K1 a K6). A distribuição dos katas garantiu que cada participante resolvesse metade dos problemas com IA e a outra metade de forma estritamente manual, alternando a ordem para mitigar o viés de aprendizagem.

### 2.2 Os Katas (Desafios)
Os katas consistiram em problemas clássicos de lógica e estruturas de dados, com testes unitários (Pytest) previamente redigidos e imutáveis durante a execução (Sprint 02). Exemplos de desafios incluíram: extração de dados de *logs* (K1), cálculo de troco com controlo de stock (K3), validação robusta de palavras-passe (K4) e achatamento de dicionários aninhados por recursividade (K5).

### 2.3 Assistente de IA e Versão
No tratamento `com_ia`, os participantes utilizaram o assistente **[INSERIR NOME DA IA AQUI - ex: GitHub Copilot / Gemini 1.5 Pro]** integrado ao ambiente de desenvolvimento. O *prompting* foi livre, mas focado na geração da lógica necessária para satisfazer os critérios de aceitação. No tratamento `sem_ia`, qualquer ferramenta de preenchimento inteligente de código foi estritamente desativada.

### 2.4 Ambiente de Execução e Coleta de Dados
A automação da coleta de métricas foi o pilar da reprodutibilidade:
* **Tempo Real (Time-to-Green):** Desenvolveu-se um *script* customizado em Python (`trial_timer.py`) rodando em *background* via *polling* a cada 10 segundos. O relógio parava automaticamente assim que todos os testes passassem, ou era aplicado um limite de censura de 35 minutos (*time-box*).
* **Métricas Estáticas:** A análise de código foi extraída através das bibliotecas **Radon** (Complexidade Ciclomática, *Maintainability Index* e SLOC) e **jscpd** (taxa de duplicação de *tokens*). Os ficheiros de teste (`test_*.py`) foram isolados e ignorados pelo analisador para não corromper os resultados do código-fonte submetido.