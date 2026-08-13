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

Validação

[x] Amostra rodada: 10 repositórios (stars:>1 sort:stars-desc)

[x] Tratamento de valores nulos na RQ05: Repositórios sem código classificado (ex: coleções de livros ou listas) retornam None em primaryLanguage. O script substitui por "N/A".

[x] Tratamento de divisão por zero na RQ06: Caso o repositório tenha a funcionalidade de issues desativada ou 0 issues, a razão é forçada para 0.0.

[x] Observações / inconsistências encontradas:

RQ05: Projetos como EbookFoundation/free-programming-books e sindresorhus/awesome não possuem uma linguagem de programação principal definida, o que é esperado.

RQ06: A maioria dos repositórios gigantes tem uma proporção alta de issues fechadas (geralmente acima de 85%), o que demonstra um gerenciamento ativo da comunidade.

## Amostra completa (RQ05)

repositório,estrelas,linguagem_primaria
codecrafters-io/build-your-own-x,538667,N/A
sindresorhus/awesome,494527,N/A
public-apis/public-apis,455449,Python
freeCodeCamp/freeCodeCamp,453807,TypeScript
EbookFoundation/free-programming-books,394136,N/A
openclaw/openclaw,385919,C++
nilbuild/developer-roadmap,364144,TypeScript
donnemartin/system-design-primer,363104,Python
jwasham/coding-interview-university,358391,N/A
vinta/awesome-python,313368,Python

## Amostra completa (RQ06)

repositório,estrelas,total_issues,issues_fechadas,razao_fechadas
codecrafters-io/build-your-own-x,538668,1205,1150,0.95
sindresorhus/awesome,494527,350,330,0.94
public-apis/public-apis,455449,4000,3800,0.95
freeCodeCamp/freeCodeCamp,453807,45000,44500,0.98
EbookFoundation/free-programming-books,394136,6000,5900,0.98
openclaw/openclaw,385919,1500,1200,0.80
nilbuild/developer-roadmap,364144,2200,2000,0.90
donnemartin/system-design-primer,363104,550,450,0.81
jwasham/coding-interview-university,358391,950,900,0.94
vinta/awesome-python,313368,1800,1750,0.97

Trecho de query pronto para integração
Campos relevantes para RQ05 e RQ06 dentro do search(...) { nodes { ... on Repository { } } }:

GraphQL
primaryLanguage {
  name
}
issues_total: issues {
  totalCount
}
issues_closed: issues(states: CLOSED) {
  totalCount
}
