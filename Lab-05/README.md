# Lab05 — Medição de um software real em operação

Estudo empírico sobre um software real, em operação e de alto impacto: escolher o software, medir algo relevante nele com um protocolo reprodutível, testar hipóteses e estimar o impacto do efeito medido.

> **Status (Sprint 01):** o software ainda está em escolha (#181). Coleta e análise já funcionam de ponta a ponta. O piloto de fumaça roda contra um servidor local ([docs/piloto.md](docs/piloto.md)). Quando o software for definido, basta criar um arquivo de alvos e repetir o piloto.

## Estrutura

| Pasta / arquivo | Conteúdo | Issue |
|---|---|---|
| `docs/software.md` | Escolha do software e evidências dos três critérios | #181 |
| `docs/proposta.md` | Pergunta, GQM, hipóteses e as 7 categorias | #182 |
| [`docs/protocolo-coleta.md`](docs/protocolo-coleta.md) | O que, de onde, como e quantas vezes se mede; regras de ética | #183 |
| [`docs/dicionario-dados.md`](docs/dicionario-dados.md) | Colunas, tipos, unidades, escalas e origem de cada dado | #183 |
| [`docs/piloto.md`](docs/piloto.md) | Execução do piloto, validação, ajustes no protocolo e estimativa da S02 | #184 |
| [`docs/plano-analise.md`](docs/plano-analise.md) | Escalas, testes, tamanho do efeito e poder | #185 |
| [`docs/impacto-fontes.md`](docs/impacto-fontes.md) | Fontes públicas de uso e conta do impacto | #186 |
| `scripts/coleta.py` | Coletor parametrizado (alvo, repetições, semente, intervalo) | #184 |
| `scripts/alvos/*.json` | Um arquivo por estudo: tratamentos (URLs) e unidades | #184 |
| `scripts/servidor_local.py` | Servidor local do piloto de fumaça (sem tráfego para terceiros) | #184 |
| `data/piloto/` | Coleta piloto (CSV + log + metadados), versionada | #184 |
| `data/raw/`, `data/processed/` | Coleta completa da S02 e dados derivados | S02 |
| `analysis/` | Pipeline de análise ([README](analysis/README.md)) | #185, #186 |
| `tests/` | Testes do coletor | #184 |

## Como reproduzir

A partir de `Lab-05`, no PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m pytest                                   # testes do coletor
cd analysis; python -m pytest; cd ..               # testes da análise

# Piloto de fumaça (dois terminais)
python scripts/servidor_local.py --porta 8765
python scripts/coleta.py scripts/alvos/piloto_local.json --repeticoes 5 --aquecimento 3 --aquecer-unidades --intervalo 0.2 --saida data/piloto --rede "loopback (127.0.0.1)"

# Análise do piloto
cd analysis
python -m analise.piloto ../data/piloto/<arquivo>.csv --saida resultados/piloto_local --pareado
```

Para estimar a duração de uma coleta sem fazer nenhuma requisição:

```powershell
python scripts/coleta.py scripts/alvos/<estudo>.json --repeticoes 30 --aquecer-unidades --estimar --latencia-ms 400
```

Cada execução grava `<nome>_<UTC>.csv` (formato longo, entrada da análise), `.log.jsonl` (todas as requisições) e `.meta.json` (software, ambiente, parâmetros e validação).
