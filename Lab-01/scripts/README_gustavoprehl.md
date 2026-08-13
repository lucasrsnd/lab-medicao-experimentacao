# gustavoprehl - extração e validação (RQ01 + RQ02)

Responsável: `gustavoprehl`
Issues: RQ01 (idade do repositório) e RQ02 (PRs aceitas) · `sprint:S01`

## Como rodar

```
cd Lab-01
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .          # instala config/src em modo editavel
copy .env.example .env    # depois editar e colar o token
python scripts\rq01_idade.py
python scripts\rq02_prs_aceitas.py
```

---

## RQ01 — idade do repositório

**Métrica:** idade do repositório = hoje - `createdAt` (campo GraphQL), em anos.

### Validação

- [x] Amostra rodada: 10 repositórios
- [x] Nenhum `createdAt` nulo na amostra
- [x] Idades calculadas fazem sentido (conferido `codecrafters-io/build-your-own-x` e `sindresorhus/awesome` manualmente na página do GitHub, batem)
- [x] Observações / inconsistências encontradas: nenhuma. `openclaw/openclaw` deu idade 0.71 anos (criado em 2025-11-24), o que é coerente, repositório recente com alto número de estrelas.

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

### Trecho de query pronto para integração

Campo relevante dentro do `search(...) { nodes { ... on Repository { } } }` (ver `src/queries`):

```graphql
createdAt
```

Cálculo de idade fica em `extract_rq01_idade_anos()`, em `src/metrics`.

---

## RQ02 — PRs aceitas

**Métrica:** total de pull requests aceitas (merged) por repositório.

### Validação

- [x] Amostra rodada: 10 repositórios
- [x] `prs_aceitas` presente e não-negativo em todos
- [x] Valores fazem sentido: projetos com equipe grande/muito ativa (`freeCodeCamp` 29.056, `openclaw` 23.604) têm ordens de grandeza a mais de PRs aceitas que listas curadas (`awesome-python` 738, `system-design-primer` 210), coerente com a natureza de cada tipo de projeto.
- [x] Observações / inconsistências encontradas: nenhuma.

| repositório | estrelas | PRs aceitas |
|---|---|---|
| codecrafters-io/build-your-own-x | 538265 | 157 |
| sindresorhus/awesome | 494209 | 700 |
| public-apis/public-apis | 455282 | 2106 |
| freeCodeCamp/freeCodeCamp | 453732 | 29056 |
| EbookFoundation/free-programming-books | 394078 | 7416 |
| openclaw/openclaw | 385757 | 23604 |
| nilbuild/developer-roadmap | 364061 | 4387 |
| donnemartin/system-design-primer | 362899 | 210 |
| jwasham/coding-interview-university | 358310 | 415 |
| vinta/awesome-python | 313203 | 738 |

### Trecho de query pronto para integração

Campo relevante dentro do `search(...) { nodes { ... on Repository { } } }` (ver `src/queries`):

```graphql
pullRequests(states: MERGED) {
  totalCount
}
```

Extração feita em `extract_rq02_prs_aceitas()`, em `src/metrics`.
