"""Tabela-base por repositório para as análises da S03 (RQ01–RQ06).

    python -m lab03.analysis.base --dataset data/amostra_completa.json.gz --output analysis/base_repositorios.csv

Achata o dataset da coleta `--full` em uma linha por repositório, com os
metadados usados como fatores (estrelas, linguagem, contribuidores, idade) e as
métricas DORA já calculadas pelo pipeline em suas variantes: lead time (a) por
release e (b) por commit, CFR (a) por runs de CI e (b) por release corretiva.

As análises leem só este CSV, o que as torna reexecutáveis sem o JSON bruto.
Célula vazia é ausência; `0` é valor observado. Nada é imputado.
"""

import argparse
import csv
import gzip
import json
import sys
from pathlib import Path

# coluna -> (seção do relatório, campo)
METRIC_SOURCES = {
    "deployment_frequency_per_week": ("deployment_frequency", "releases_per_week"),
    "releases_in_window": ("deployment_frequency", "releases_in_window"),
    "deployment_frequency_weeks": ("deployment_frequency", "window_weeks"),
    "lead_time_a_hours": ("lead_time", "by_release_hours"),
    "lead_time_b_hours": ("lead_time", "by_commit_hours"),
    "lead_time_a_releases": ("lead_time", "releases_used"),
    "lead_time_b_commits": ("lead_time", "commits_used"),
    "cfr_a": ("ci_failure_rate", "rate"),
    "cfr_a_runs": ("ci_failure_rate", "runs_evaluated"),
    "cfr_b": ("delivery_failure_rate", "rate"),
    "cfr_b_evaluated": ("delivery_failure_rate", "evaluated"),
    "cfr_b_censored": ("delivery_failure_rate", "censored"),
    "recovery_hours": ("recovery", "median_hours"),
    "recovery_episodes": ("recovery", "episodes_recovered"),
    "recovery_episodes_censored": ("recovery", "censored_episodes"),
}
FIELDS = (
    "repositorio", "estrelas", "linguagem", "contribuidores", "idade_dias",
    *METRIC_SOURCES, "categoria_geral_c1",
)
NUMERIC = tuple(field for field in FIELDS if field not in ("repositorio", "linguagem",
                                                           "categoria_geral_c1"))


def load_dataset(path: Path) -> dict:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def repository_row(item: dict) -> dict:
    metadata, report = item["metadata"], item.get("report") or {}
    row = {
        "repositorio": metadata["full_name"],
        "estrelas": metadata.get("stars"),
        "linguagem": metadata.get("primary_language"),
        "contribuidores": metadata.get("contributor_count"),
        "idade_dias": metadata.get("age_days_at_collection"),
    }
    for column, (section, field) in METRIC_SOURCES.items():
        row[column] = (report.get(section) or {}).get(field)
    overall = (report.get("dora_classification") or {}).get("overall") or {}
    row["categoria_geral_c1"] = overall.get("category")
    return row


def build_rows(dataset: dict) -> list[dict]:
    rows = [repository_row(item) for item in dataset["repositories"]]
    names = [row["repositorio"] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("Dataset com repositórios duplicados.")
    return sorted(rows, key=lambda row: row["repositorio"])


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            # None vira célula vazia: ausência, nunca zero.
            writer.writerow({key: "" if row[key] is None else row[key] for key in FIELDS})
    temporary.replace(path)


def read_csv(path: Path) -> list[dict]:
    """Lê o CSV-base convertendo colunas numéricas (vazio -> None)."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for field in NUMERIC:
            row[field] = float(row[field]) if row.get(field, "") != "" else None
        row["linguagem"] = row.get("linguagem") or None
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, default=Path("data/amostra_completa.json.gz"))
    parser.add_argument("--output", type=Path, default=Path("analysis/base_repositorios.csv"))
    args = parser.parse_args(argv)
    try:
        rows = build_rows(load_dataset(args.dataset))
    except (OSError, KeyError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    write_csv(args.output, rows)
    print(f"{len(rows)} repositórios gravados em {args.output}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
