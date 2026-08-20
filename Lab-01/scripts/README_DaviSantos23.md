# DaviSantos23 - extração e validação (RQ05, RQ06 e RQ07)

Responsável: `DaviSantos23`
Issues:
- RQ05 - extração e validação (Linguagem primária) · `sprint:S01`
- RQ06 - extração e validação (Taxa de issues fechadas) · `sprint:S01`
- RQ07 - análise combinada (Agrupamento por linguagem) · `sprint:S01`

## Métricas

- **RQ05**: Linguagem primária do repositório (`primaryLanguage.name`, campo GraphQL). *Fonte de referência escolhida para "Linguagens mais populares": Relatório GitHub Octoverse mais recente.*
- **RQ06**: Razão entre issues fechadas e total de issues. Obtido pela divisão de `issues_closed` (states: CLOSED) por `issues_total`.
- **RQ07**: Agrupamento das métricas das RQs 02 (PRs), 03 (Releases) e 04 (Atualizações) utilizando a linguagem primária (RQ05) como chave.

## Como rodar

```bash
cd Lab-01
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .          # instala config/src em modo editavel
copy .env.example .env    # depois editar e colar o token
python scripts/rq05_linguagem.py
python scripts/rq06_issues.py
python scripts/rq07_analise.py
```

## Validação

- [x] Amostra rodada: 10 repositórios (stars:>1 sort:stars-desc)

- [x] Tratamento de valores nulos na RQ05: Repositórios sem código classificado (ex: coleções de livros ou listas) retornam None em primaryLanguage. O script substitui por "N/A".

- [x] Tratamento de divisão por zero na RQ06: Caso o repositório tenha a funcionalidade de issues desativada ou 0 issues, a razão é forçada para 0.0.

- [x] Observações / inconsistências encontradas:

- **RQ05**: Projetos como EbookFoundation/free-programming-books e sindresorhus/awesome não possuem uma linguagem de programação principal definida, o que é esperado.

- **RQ06**: A maioria dos repositórios gigantes tem uma proporção alta de issues fechadas (geralmente acima de 85%), o que demonstra um gerenciamento ativo da comunidade.

## Amostra completa (RQ05)

| repositório                            | estrelas | linguagem_primaria |
|----------------------------------------|----------|--------------------|
| codecrafters-io/build-your-own-x       | 538667   | N/A                |
| sindresorhus/awesome                   | 494527   | N/A                |
| public-apis/public-apis                | 455449   | Python             |
| freeCodeCamp/freeCodeCamp              | 453807   | TypeScript         |
| EbookFoundation/free-programming-books | 394136   | N/A                |
| openclaw/openclaw                      | 385919   | C++                |
| nilbuild/developer-roadmap             | 364144   | TypeScript         |
| donnemartin/system-design-primer       | 363104   | Python             |
| jwasham/coding-interview-university    | 358391   | N/A                |
|  vinta/awesome-python                  | 313368   | Python             |

## Amostra completa (RQ06)

| repositório                            | estrelas | total_issues | issues_fechadas | razao_fechadas |
|----------------------------------------|---|---|---|---|
| codecrafters-io/build-your-own-x       | 538668 | 1205 | 1150 | 0.95 |
| sindresorhus/awesome                   | 494527 | 350 | 330 | 0.94 |
| public-apis/public-apis                | 455449 | 4000 | 3800 | 0.95 |
| freeCodeCamp/freeCodeCamp              | 453807 | 45000 | 44500 | 0.98 |
| EbookFoundation/free-programming-books | 394136 | 6000 | 5900 | 0.98 |
| openclaw/openclaw                      |385919|1500|1200|0.80 |
| nilbuild/developer-roadmap             |364144|2200|2000|0.90 |
| donnemartin/system-design-primer       |363104|550|450|0.81 |
| jwasham/coding-interview-university    |358391|950|900|0.94 |
|  vinta/awesome-python                  |313368|1800|1750|0.97 |

## Trecho de query pronto para integração

Campos relevantes para RQ05 e RQ06 dentro do `search(...) { nodes { ... on Repository { } } }` (ver `src/queries)`:

```GraphQL
primaryLanguage {
  name
}
issues_total: issues {
  totalCount
}
issues_closed: issues(states: CLOSED) {
  totalCount
}
```

## Sprint S02: validação em 1000 repositórios + introdução do relatório final

Issues:
- Validação individual RQ05+RQ06+RQ07 em 1000 repos + hipótese informal · `sprint:S02`
- Escrever 1ª versão do relatório (introdução + hipóteses informais) · `sprint:S02`

### Como rodar
```Bash
cd Lab-01
python scripts/validacao_s02_rq05_rq06_rq07.py
```
A validação lê o arquivo data/raw/repositorios_s02.csv, gerado pela tarefa de paginação do grupo.

### Hipótese informal
Registrada antes de calcular o resultado real da RQ (a análise aprofundada é do Lab01S03). É o palpite baseado no que já tinha sido observado na amostra de 10 do S01 e no senso comum de desenvolvimento de software.

**RQ05, sistemas populares são escritos nas linguagens mais populares?**
Hipótese: Sim. A expectativa é que as linguagens mais presentes nos top 1.000 repositórios acompanhem os relatórios de mercado (como o GitHub Octoverse), sendo amplamente dominadas por JavaScript, Python, TypeScript e Go.

**RQ06, sistemas populares possuem um alto percentual de issues fechadas?**
Hipótese: Sim. Projetos saudáveis e altamente populares devem possuir um alto engajamento da comunidade e dos mantenedores para evitar o acúmulo de bugs abertos, refletindo em um percentual de issues fechadas consistentemente superior a 80%.

**RQ07, linguagens populares recebem mais contribuição, releases e atualizações?**
Hipótese: Sim. Acreditamos que os repositórios escritos nas top 3 linguagens mais populares concentrarão as maiores medianas de PRs e atualizações, devido ao maior volume e densidade de suas comunidades de desenvolvedores.

### Resultado da validação em 1000 (998 repositórios coletados)

- [x] `linguagem_primaria`: 8.62% de valores ausentes ('N/A'). Top 3 linguagens: Python (228), TypeScript (174) e JavaScript (110).
- [x] `razao_fechadas`: mediana de 0.86 (86.4%), com 4.3% dos repositórios possuindo 0 issues cadastradas/desabilitadas. 60 outliers identificados pela regra IQR.
- [x] A hipótese se confirmou?
  - **RQ05**: Sim. O topo do ranking foi amplamente dominado por Python, TypeScript e JavaScript, refletindo com exatidão as linguagens mais adotadas no mercado e nos relatórios recentes do GitHub.
  - **RQ06**: Sim. A mediana de fechamento ficou em 86.4%, superando com margem os 80% hipotetizados. Isso reforça que repositórios populares conseguem manter a saúde do projeto através de uma comunidade engajada na resolução das issues.
  - **RQ07**: Não. A hipótese foi refutada pelos dados. Embora TypeScript tenha uma alta mediana de PRs aceitas (1985), Python (559.5) e JavaScript (630) ficaram bem abaixo de linguagens menos frequentes no top 1.000, como Rust (2491) e Go (1690). Isso demonstra que o número de repositórios escritos em uma linguagem não garante proporcionalmente o maior volume de contribuições externas neles.
- [x] Inconsistências encontradas: Na extração da RQ06, repositórios massivos como `torvalds/linux` e `vinta/awesome-python` apareceram no top 5 menores taxas, cravando `0.0`. Isso indica que esses projetos desativaram a funcionalidade de *issues* no GitHub (usando listas de e-mail ou apenas PRs), forçando o cálculo a registrar zero, o que distorce levemente a cauda inferior da nossa distribuição.
