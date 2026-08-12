# lucasrsnd — extração e validação (RQ03 + RQ04)

Responsável: `lucasrsnd`
Issues:
- RQ03 — extração e validação (total de releases) · `sprint:S01`
- RQ04 — extração e validação (tempo até última atualização) · `sprint:S01`

## Métricas

- **RQ03**: total de releases do repositório (`releases.totalCount`, campo GraphQL).
- **RQ04**: tempo até a última atualização = hoje − `pushedAt` (data do último push), em dias.

## Como rodar

```
cd Lab-01
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .          # instala config/src em modo editavel
copy .env.example .env    # depois editar e colar o token
python scripts\rq03_releases.py
python scripts\rq04_atualizacao.py
```

## Validação

- [x] Amostra rodada: 10 repositórios (`stars:>1 sort:stars-desc`)
- [x] Nenhum `releases.totalCount` ou `pushedAt` nulo na amostra
- [x] Valores de releases e de dias desde atualização fazem sentido
- [x] Observações / inconsistências encontradas:
  - **RQ03**: a maioria dos repositórios da amostra tem **0 releases**, mesmo com centenas de milhares de estrelas. Isso é coerente — vários são listas/coleções (`sindresorhus/awesome`, `EbookFoundation/free-programming-books`, `public-apis/public-apis`) que nunca usam a feature "Releases" do GitHub, só recebem commits diretos. Só `openclaw/openclaw` (233) e `nilbuild/developer-roadmap` (1) fogem disso.
  - **RQ04**: a maior parte foi atualizada há poucos dias (0 a 6 dias), exceto `jwasham/coding-interview-university` (347 dias) e `donnemartin/system-design-primer` (144 dias) — ambos são listas de referência mais estáticas, não projetos de código com desenvolvimento ativo constante.

### Amostra completa (RQ03)

| repositório | estrelas | total de releases |
|---|---|---|
| codecrafters-io/build-your-own-x | 538667 | 0 |
| sindresorhus/awesome | 494527 | 0 |
| public-apis/public-apis | 455449 | 0 |
| freeCodeCamp/freeCodeCamp | 453807 | 0 |
| EbookFoundation/free-programming-books | 394136 | 0 |
| openclaw/openclaw | 385919 | 233 |
| nilbuild/developer-roadmap | 364144 | 1 |
| donnemartin/system-design-primer | 363104 | 0 |
| jwasham/coding-interview-university | 358391 | 0 |
| vinta/awesome-python | 313368 | 0 |

### Amostra completa (RQ04)

| repositório | estrelas | último push | dias desde atualização |
|---|---|---|---|
| codecrafters-io/build-your-own-x | 538668 | 2026-07-14T19:25:58Z | 27 |
| sindresorhus/awesome | 494527 | 2026-06-30T18:21:16Z | 41 |
| public-apis/public-apis | 455449 | 2026-08-08T20:32:59Z | 2 |
| freeCodeCamp/freeCodeCamp | 453807 | 2026-08-11T11:51:50Z | 0 |
| EbookFoundation/free-programming-books | 394136 | 2026-08-11T12:11:06Z | 0 |
| openclaw/openclaw | 385919 | 2026-08-11T13:53:54Z | 0 |
| nilbuild/developer-roadmap | 364144 | 2026-08-07T12:43:15Z | 4 |
| donnemartin/system-design-primer | 363104 | 2026-03-20T01:52:19Z | 144 |
| jwasham/coding-interview-university | 358391 | 2025-08-28T14:42:47Z | 347 |
| vinta/awesome-python | 313368 | 2026-08-05T06:11:04Z | 6 |

## Trecho de query pronto para integração

Campos relevantes para RQ03 e RQ04 dentro do `search(...) { nodes { ... on Repository { } } }` (ver `src/queries`):

```graphql
releases {
  totalCount
}
pushedAt
```

Cálculo de "dias desde atualização" fica em `extract_rq04_dias_desde_atualizacao()`, em
`src/metrics`. RQ03 não precisa de cálculo adicional, `total_releases` já vem pronto
de `releases.totalCount` (ver `extract_rq03_total_releases()`).
