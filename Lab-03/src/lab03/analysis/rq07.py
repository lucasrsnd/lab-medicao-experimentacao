"""RQ07: sensibilidade da classificação DORA às variantes C1, C2 e C3.

    python -m lab03.analysis.rq07 --classificacoes validation/dataset-v1/rq07_classificacoes.csv

Para cada par de variantes, calcula o percentual de repositórios que mudam de
categoria geral, a matriz de transição e o kappa de Cohen ponderado linear.
Só entram repositórios classificados nas duas variantes; os demais ficam fora,
com o motivo registrado, e nunca são imputados.
"""

import argparse
import csv
import hashlib
import itertools
import json
import sys
from pathlib import Path

from lab03.analysis.stats import fmt

CATEGORIES = ("Low", "Medium", "High", "Elite")  # ordem crescente
VARIANTS = ("C1", "C2", "C3")


def weighted_kappa(matrix: list[list[int]]) -> float | None:
    """Kappa de Cohen com pesos lineares w = 1 - |i - j| / (k - 1)."""
    k = len(matrix)
    total = sum(map(sum, matrix))
    if total == 0:
        return None
    rows = [sum(row) / total for row in matrix]
    columns = [sum(matrix[i][j] for i in range(k)) / total for j in range(k)]
    weight = [[1 - abs(i - j) / (k - 1) for j in range(k)] for i in range(k)]
    observed = sum(weight[i][j] * matrix[i][j] / total for i in range(k) for j in range(k))
    expected = sum(weight[i][j] * rows[i] * columns[j] for i in range(k) for j in range(k))
    return None if expected == 1 else (observed - expected) / (1 - expected)


def read_classifications(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    needed = {f"{v}_{s}" for v in VARIANTS for s in ("categoria", "status")}
    missing = needed - set(rows[0] if rows else needed)
    if missing:
        raise ValueError(f"Colunas ausentes em {path}: {sorted(missing)}")
    return rows


def _usable(row: dict, variant: str) -> bool:
    return row[f"{variant}_status"] == "classified" and row[f"{variant}_categoria"] in CATEGORIES


def compare_pair(rows: list[dict], first: str, second: str) -> dict:
    matrix = [[0] * len(CATEGORIES) for _ in CATEGORIES]
    exclusions = {f"{first}_sem_categoria": 0, f"{second}_sem_categoria": 0, "ambas_sem_categoria": 0}
    up = down = 0
    for row in rows:
        ok_first, ok_second = _usable(row, first), _usable(row, second)
        if not ok_first and not ok_second:
            exclusions["ambas_sem_categoria"] += 1
        elif not ok_first:
            exclusions[f"{first}_sem_categoria"] += 1
        elif not ok_second:
            exclusions[f"{second}_sem_categoria"] += 1
        else:
            i = CATEGORIES.index(row[f"{first}_categoria"])
            j = CATEGORIES.index(row[f"{second}_categoria"])
            matrix[i][j] += 1
            up += j > i
            down += j < i
    n = sum(map(sum, matrix))
    changed = up + down
    kappa = weighted_kappa(matrix)
    return {
        "pair": f"{first}x{second}",
        "n_compared": n,
        "n_excluded": len(rows) - n,
        "exclusions": exclusions,
        "changed": changed,
        "changed_pct": changed / n * 100 if n else None,
        "moved_up": up,
        "moved_down": down,
        "weighted_kappa_linear": kappa,
        "kappa_undefined_reason": None if kappa is not None else (
            "sem repositórios comparáveis" if n == 0 else "concordância esperada igual a 1"
        ),
        "matrix": {
            "rows": f"categoria em {first}",
            "columns": f"categoria em {second}",
            "categories": list(CATEGORIES),
            "counts": matrix,
        },
    }


def analyze(rows: list[dict]) -> dict:
    return {
        "repositories": len(rows),
        "weights": "linear, categorias ordenadas Low < Medium < High < Elite",
        "pairs": [compare_pair(rows, a, b) for a, b in itertools.combinations(VARIANTS, 2)],
    }


def markdown(result: dict) -> str:
    lines = [
        "# RQ07 — Sensibilidade da classificação às variantes",
        "",
        f"Base: {result['repositories']} repositórios. Só entram repositórios com categoria geral "
        "nas duas variantes; os demais são excluídos, sem imputação.",
        "",
        "| Par | n comparado | excluídos | mudaram | % mudaram | subiram | desceram | κ ponderado (linear) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair in result["pairs"]:
        lines.append(
            f"| {pair['pair']} | {pair['n_compared']} | {pair['n_excluded']} | {pair['changed']} "
            f"| {fmt(pair['changed_pct'], 1)} | {pair['moved_up']} | {pair['moved_down']} "
            f"| {fmt(pair['weighted_kappa_linear'])} |"
        )
    for pair in result["pairs"]:
        first, second = pair["pair"].split("x")
        matrix = pair["matrix"]
        lines += ["", f"## {pair['pair']}", "",
                  f"Linhas: categoria em {first}. Colunas: categoria em {second}.", "",
                  "| | " + " | ".join(CATEGORIES) + " |", "|---|" + "---:|" * len(CATEGORIES)]
        for name, counts in zip(CATEGORIES, matrix["counts"]):
            lines.append(f"| {name} | " + " | ".join(map(str, counts)) + " |")
        reasons = ", ".join(f"{key} = {value}" for key, value in pair["exclusions"].items())
        lines += ["", f"Exclusões: {reasons}."]
        if pair["kappa_undefined_reason"]:
            lines.append(f"κ indefinido: {pair['kappa_undefined_reason']}.")
    lines += [
        "",
        "Leitura: a C2 usa o CFR (b), cuja validação de avaliador único ficou abaixo do limiar "
        "do protocolo (F1 < 0,70). Mudanças que envolvem a C2 podem refletir o erro da heurística, "
        "e não só a definição de entrega. Os resultados descrevem esta amostra e não implicam "
        "causalidade.",
        "",
    ]
    return "\n".join(lines)


def write_matrices(path: Path, result: dict) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["par", "de", "para", "repositorios"])
        for pair in result["pairs"]:
            for name, counts in zip(CATEGORIES, pair["matrix"]["counts"]):
                for target, count in zip(CATEGORIES, counts):
                    writer.writerow([pair["pair"], name, target, count])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--classificacoes", type=Path,
                        default=Path("validation/dataset-v1/rq07_classificacoes.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/rq07"))
    args = parser.parse_args(argv)
    try:
        rows = read_classifications(args.classificacoes)
        # CRLF vira LF: o CSV versionado muda de fim de linha com o autocrlf do Git.
        digest = hashlib.sha256(args.classificacoes.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    result = analyze(rows)
    result["input_csv_sha256"] = digest
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "rq07_resultados.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "rq07_resultados.md").write_text(markdown(result), encoding="utf-8")
    write_matrices(args.output_dir / "rq07_matrizes.csv", result)
    for pair in result["pairs"]:
        print(f"{pair['pair']}: n={pair['n_compared']} mudaram={fmt(pair['changed_pct'], 1)}% "
              f"kappa={fmt(pair['weighted_kappa_linear'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
