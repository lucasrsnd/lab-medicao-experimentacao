"""Coleta de métricas estáticas por trial (Radon cc/raw/mi + jscpd + LOC).

Dono: Lucas, Issue [S01] "Script de coleta de métricas estáticas".

Uso (CLI, a partir de `Lab-02/`):
    python -m src.metrics.static_metrics \\
        --kata k1 --participante lucasrsnd --tratamento sem_ia \\
        --path katas/k1/sem_ia/lucasrsnd

Roda, sobre os arquivos-fonte do trial (ignora `test_*.py`/`conftest.py`,
scaffold de teste de aceitação do Davi, não código produzido no trial):

- Radon `raw`, para LOC/LLOC/SLOC, métrica de controle **obrigatória** sempre
  que se reporta complexidade/duplicação (código gerado por IA pode ser mais
  verboso, conforme o enunciado da RQ3).
- Radon `cc`, para complexidade ciclomática (McCabe) média e total por
  função/método (RQ3, métrica primária de estrutura).
- Radon `mi`, para o Índice de Manutenibilidade (RQ3, aprofundamento
  opcional).
- `jscpd` (via `npx`, Node, ver nota em requirements.txt), para o percentual
  de linhas duplicadas. Radon não cobre duplicação, daí a ferramenta
  separada (RQ3).

Cada chamada acrescenta uma linha a `data/raw/trials_metricas.csv`, uma por
trial (kata, integrante, tratamento), no mesmo padrão de
`src.timing.trial_timer` para `trials_tempo.csv`. As duas tabelas se juntam
por (kata, integrante, tratamento) na análise da S03.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze as radon_raw_analyze

LAB02_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = LAB02_ROOT / "data" / "raw" / "trials_metricas.csv"

JSCPD_MIN_LINES = 3
JSCPD_MIN_TOKENS = 20

CSV_FIELDS = [
    "kata",
    "integrante",
    "tratamento",
    "arquivos_analisados",
    "loc",
    "lloc",
    "sloc",
    "num_blocos",
    "complexidade_media",
    "complexidade_total",
    "mi",
    "linhas_totais_jscpd",
    "linhas_duplicadas",
    "duplicacao_pct",
    "clones",
    "erro_parse",
]


@dataclass
class RawMetrics:
    loc: int
    lloc: int
    sloc: int


@dataclass
class ComplexityMetrics:
    media: float
    total: int
    num_blocos: int


@dataclass
class DuplicationMetrics:
    linhas_totais: int
    linhas_duplicadas: int
    duplicacao_pct: float
    clones: int


@dataclass
class TrialMetrics:
    kata: str
    integrante: str
    tratamento: str
    arquivos_analisados: int
    loc: int
    lloc: int
    sloc: int
    num_blocos: int
    complexidade_media: float
    complexidade_total: int
    mi: float
    linhas_totais_jscpd: int
    linhas_duplicadas: int
    duplicacao_pct: float
    clones: int
    erro_parse: bool


def find_source_files(path: Path) -> list[Path]:
    """Lista os arquivos-fonte do trial em `path`.

    Ignora `test_*.py`/`conftest.py` (scaffold de teste de aceitação, não
    código produzido no trial) e pastas de ambiente (`.venv`,
    `__pycache__`) caso `path` seja um diretório com mais coisa dentro.
    """
    if path.is_file():
        return [path]
    if not path.is_dir():
        sys.exit(f"Caminho do trial não encontrado: {path}")

    arquivos = sorted(
        f
        for f in path.rglob("*.py")
        if not f.name.startswith("test_")
        and f.name != "conftest.py"
        and ".venv" not in f.parts
        and "__pycache__" not in f.parts
    )
    if not arquivos:
        sys.exit(
            f"Nenhum arquivo .py de solução encontrado em {path} "
            "(arquivos test_*.py são ignorados de propósito)."
        )
    return arquivos


def analyze_raw_and_complexity(
    arquivos: list[Path],
) -> tuple[RawMetrics, ComplexityMetrics, float, bool]:
    """Agrega Radon `raw`, `cc` e `mi` sobre `arquivos`.

    MI é calculada por arquivo (Radon exige um módulo por chamada) e
    reportada como média simples, suficiente para os katas (1-poucos
    arquivos por trial). Um arquivo com erro de sintaxe (trial que terminou
    com código quebrado no time-box) é contado em `erro_parse` e excluído da
    agregação, em vez de derrubar a coleta inteira: o trial continua sendo
    registrado, mesmo espírito de "censurado, nunca descartado" do timer.
    """
    loc = lloc = sloc = 0
    complexidades: list[int] = []
    mis: list[float] = []
    houve_erro_parse = False

    for arquivo in arquivos:
        codigo = arquivo.read_text(encoding="utf-8-sig")
        try:
            bruto = radon_raw_analyze(codigo)
            blocos = cc_visit(codigo)
            mi = mi_visit(codigo, True)
        except SyntaxError as erro:
            houve_erro_parse = True
            print(f"[aviso] {arquivo} não compilou (SyntaxError: {erro}), excluído da agregação.")
            continue

        loc += bruto.loc
        lloc += bruto.lloc
        sloc += bruto.sloc
        complexidades.extend(bloco.complexity for bloco in blocos)
        mis.append(mi)

    raw = RawMetrics(loc=loc, lloc=lloc, sloc=sloc)
    complexidade = ComplexityMetrics(
        media=round(sum(complexidades) / len(complexidades), 2) if complexidades else 0.0,
        total=sum(complexidades),
        num_blocos=len(complexidades),
    )
    mi_medio = round(sum(mis) / len(mis), 2) if mis else 0.0
    return raw, complexidade, mi_medio, houve_erro_parse


def run_jscpd(
    path: Path,
    *,
    min_lines: int = JSCPD_MIN_LINES,
    min_tokens: int = JSCPD_MIN_TOKENS,
) -> DuplicationMetrics:
    """Roda `jscpd` (via `npx`) sobre `path` e lê o relatório JSON gerado.

    Usa `--ignore` para excluir `test_*.py` do escaneamento, mesmo motivo de
    `find_source_files`, mas o jscpd escaneia um diretório, não uma lista de
    arquivos, daí o glob em vez de reaproveitar `arquivos`.
    """
    alvo = path if path.is_dir() else path.parent
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "jscpd-report"
        comando = [
            "npx", "--yes", "jscpd", str(alvo),
            "--reporters", "json",
            "--output", str(saida),
            "--min-lines", str(min_lines),
            "--min-tokens", str(min_tokens),
            "--ignore", "**/test_*.py,**/conftest.py",
            "--silent",
        ]
        proc = subprocess.run(
            comando, capture_output=True, text=True, shell=(sys.platform == "win32")
        )
        relatorio = saida / "jscpd-report.json"
        if not relatorio.exists():
            sys.exit(
                "jscpd não gerou relatório. Confira se Node/npm estão instalados e "
                "se há internet liberada para `npx` (ou `npm install -g jscpd` para "
                "rodar offline depois de instalado uma vez).\n"
                f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        dados = json.loads(relatorio.read_text(encoding="utf-8"))

    total = dados.get("statistics", {}).get("total", {})
    return DuplicationMetrics(
        linhas_totais=total.get("lines", 0),
        linhas_duplicadas=total.get("duplicatedLines", 0),
        duplicacao_pct=round(total.get("percentage", 0.0), 2),
        clones=total.get("clones", 0),
    )


def collect_static_metrics(
    *,
    kata: str,
    integrante: str,
    tratamento: str,
    path: Path,
    jscpd_fn: Callable[[Path], DuplicationMetrics] = run_jscpd,
) -> TrialMetrics:
    """`jscpd_fn` é injetável para testar sem depender de `npx`/Node (ver
    `tests/test_static_metrics.py`)."""
    arquivos = find_source_files(path)
    raw, complexidade, mi, erro_parse = analyze_raw_and_complexity(arquivos)
    duplicacao = jscpd_fn(path)

    return TrialMetrics(
        kata=kata,
        integrante=integrante,
        tratamento=tratamento,
        arquivos_analisados=len(arquivos),
        loc=raw.loc,
        lloc=raw.lloc,
        sloc=raw.sloc,
        num_blocos=complexidade.num_blocos,
        complexidade_media=complexidade.media,
        complexidade_total=complexidade.total,
        mi=mi,
        linhas_totais_jscpd=duplicacao.linhas_totais,
        linhas_duplicadas=duplicacao.linhas_duplicadas,
        duplicacao_pct=duplicacao.duplicacao_pct,
        clones=duplicacao.clones,
        erro_parse=erro_parse,
    )


def append_result(result: TrialMetrics, csv_path: Path = DEFAULT_CSV_PATH) -> None:
    """Adiciona `result` a `csv_path`, criando o arquivo com cabeçalho se
    ainda não existir."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(asdict(result))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--kata", required=True, help='ex.: "k1"')
    parser.add_argument("--participante", required=True, help='ex.: "lucasrsnd"')
    parser.add_argument("--tratamento", required=True, choices=["com_ia", "sem_ia"])
    parser.add_argument(
        "--path", required=True, type=Path, help="arquivo ou pasta com a solução do trial"
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    print(
        f"Coletando métricas estáticas: kata={args.kata} integrante={args.participante} "
        f"tratamento={args.tratamento} path={args.path}"
    )

    resultado = collect_static_metrics(
        kata=args.kata,
        integrante=args.participante,
        tratamento=args.tratamento,
        path=args.path,
    )
    append_result(resultado, csv_path=args.csv)

    aviso_erro = " [ATENÇÃO: erro_parse=True, ver avisos acima]" if resultado.erro_parse else ""
    print(
        f"LOC(sloc)={resultado.sloc} complexidade_media={resultado.complexidade_media} "
        f"mi={resultado.mi} duplicacao={resultado.duplicacao_pct}% -> {args.csv}{aviso_erro}"
    )


if __name__ == "__main__":
    main()
