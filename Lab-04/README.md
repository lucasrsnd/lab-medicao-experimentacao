# Lab 04 — Pearson × Spearman por simulação

Par **P5**: tamanho do módulo (LOC) × número de defeitos. Plano, arquitetura e
contratos entre módulos em [`docs/plano-lab04.md`](docs/plano-lab04.md).

- GitHub Projects: <https://github.com/users/lucasrsnd/projects/2>
- Dashboard: *link adicionado após o deploy (ver "Deploy" abaixo)*

## Instalação

No diretório `Lab-04`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Testes

```powershell
python -m pytest
```

## Dashboard

No diretório `Lab-04`, com o ambiente ativado:

```powershell
streamlit run streamlit_app.py
```

O dashboard só lê os artefatos versionados em `data/real/`, `outputs/` e
`docs/dashboard/`. Os textos de cada seção ficam em `docs/dashboard/NN-*.md`, e
cada autor edita só o seu. Seções cujos artefatos ainda não existem mostram um
aviso em vez de quebrar a página.

| Seção | Conteúdo | Situação |
|---|---|---|
| 1. Cenário | pergunta, H₀/H₁, origem dos dados | S01 |
| 2. Os dados | G1 — real × simulado | S01 |
| 3. Como os testes funcionam | G2 — t sob H₀, região de rejeição, p-valor do exemplo | S01 |
| 4. Erro tipo I | G3 | S02 |
| 5. Poder | G4 | S02 |
| 6. Dados reais | tabela dos dois testes | entrega final |
| 7. Conclusão | expectativa × resultado, recomendação | entrega final |

## Deploy (Streamlit Community Cloud)

O deploy sai da `main`: cada merge na `main` atualiza o app publicado. Por isso,
rode `python -m pytest` antes de fazer o merge.

| Arquivo | Papel no Cloud |
|---|---|
| `streamlit_app.py` | arquivo de entrada; põe `src/` no `sys.path`, porque o Cloud não instala o pacote |
| `requirements.txt` | dependências com versões fixas; tem precedência sobre o `pyproject.toml` da mesma pasta |
| `.streamlit/config.toml` | tema; vale por estar ao lado do arquivo de entrada |

O Cloud executa a partir da **raiz do repositório**. Para reproduzir isso
localmente, na raiz e com um ambiente instalado só pelo `requirements.txt`:

```powershell
streamlit run Lab-04/streamlit_app.py
```

### Publicar (uma vez)

1. Fazer o merge na `main` do PR com estes arquivos.
2. Em <https://share.streamlit.io>, entrar com o GitHub e escolher **Create app** → deploy a partir do GitHub.
3. Preencher:
   - **Repository:** `lucasrsnd/lab-medicao-experimentacao`
   - **Branch:** `main`
   - **Main file path:** `Lab-04/streamlit_app.py`
   - **App URL:** um subdomínio curto, ex.: `lab04-pearson-spearman`
   - **Advanced settings → Python:** 3.13, a versão em que o projeto foi testado
4. Depois de publicado, preencher `DASHBOARD_URL` em `src/lab04/config.py` e o link no topo deste README. O botão "Dashboard" do topo passa a funcionar.

### Ao preparar a Sprint 2 e a apresentação

- **Versionar `outputs/simulacoes.csv`.** O dashboard só lê arquivos; ele não roda as 10.000 repetições ao abrir.
- **Nova dependência:** adicionar no `pyproject.toml` e no `requirements.txt`, com versão fixa. O `tests/test_deploy.py` falha se os dois divergirem.
- **Textos novos** (`docs/dashboard/04-*.md`, `05-*.md`) usam os blocos `## O que observar` e `## Conclusão`.
- **Simulador do bônus:** poucas repetições e `st.cache_data`, porque os recursos do Cloud são limitados.
- **Antes da apresentação:** abrir o link alguns minutos antes. Apps sem acesso recente podem hibernar; se aparecer a tela para acordar o app, basta clicar. Se o Cloud falhar, use o plano B, o comando local acima.

## Contratos compartilhados

| Módulo | Conteúdo |
|---|---|
| `lab04.config` | semente (`SEED = 42`), α, repetições, tamanhos de efeito e caminhos de `data/` e `outputs/` |
| `lab04.contracts` | `MarginalParams`, `Scenario`, `TestResult` e colunas dos arquivos trocados entre módulos |
| `lab04.style` | cor e rótulo de cada teste e `apply_layout` (título, eixos e legenda) |

O comando único de reprodução será adicionado na integração final (FINAL-01).
