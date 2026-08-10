# RQ01 — extração e validação (idade do repositório)

Responsável: `gustavoprehl`
Issue: RQ01 — extração e validação (idade do repositório) · `sprint:S01`

## Métrica

Idade do repositório = hoje − `createdAt` (campo GraphQL), em anos.

## Como rodar

```
cd Lab-01
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # depois editar e colar o token
cd individual\gustavoprehl
python rq01_idade.py
```

## Validação

- [x] Amostra rodada: 10 repositórios
- [x] Nenhum `createdAt` nulo na amostra
- [x] Idades calculadas fazem sentido (conferido `codecrafters-io/build-your-own-x` e `sindresorhus/awesome` manualmente na página do GitHub — batem)
- [x] Observações / inconsistências encontradas: nenhuma. `openclaw/openclaw` deu idade 0.71 anos (criado em 2025-11-24), o que é coerente — repositório recente com alto número de estrelas.

Amostra completa:

| repositório | estrelas | criado em | idade (anos) |
|---|---|---|---|
| codecrafters-io/build-your-own-x | 538254 | 2018-05-09 | 8.25 |
| sindresorhus/awesome | 494202 | 2014-07-11 | 12.08 |
| public-apis/public-apis | 455280 | 2016-03-20 | 10.39 |
| freeCodeCamp/freeCodeCamp | 453729 | 2014-12-24 | 11.62 |
| EbookFoundation/free-programming-books | 394078 | 2013-10-11 | 12.83 |
| openclaw/openclaw | 385751 | 2025-11-24 | 0.71 |
| nilbuild/developer-roadmap | 364060 | 2017-03-15 | 9.40 |
| donnemartin/system-design-primer | 362892 | 2017-02-26 | 9.45 |
| jwasham/coding-interview-university | 358308 | 2016-06-06 | 10.18 |
| vinta/awesome-python | 313188 | 2014-06-27 | 12.12 |

## Trecho de query pronto para integração (Issue #10)

O campo relevante para RQ01 dentro do `search(...) { nodes { ... on Repository { } } }` é:

```graphql
createdAt
```

Cálculo de idade fica no lado do script (Python), não no GraphQL — ver `calcular_idade_anos()` em `rq01_idade.py`.
