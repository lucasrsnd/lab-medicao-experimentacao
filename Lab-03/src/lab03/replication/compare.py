"""Compara os resultados originais do grupo autor com os da replicação (FINAL-02).

    python -m lab03.replication.compare --original autor.csv --replicated replicado.csv --mapping config/replicacao-mapeamento.exemplo.json --output-dir replication/comparacao

O esquema do CSV do outro grupo não é conhecido de antemão: o mapeamento JSON
diz, para cada lado (`original`, `replicated`), a coluna-chave, a coluna de cada
métrica (`metrics`, nome lógico -> coluna) e de cada categoria DORA
(`categories`). Os nomes lógicos precisam coincidir nos dois lados.

Regras, aplicadas a cada repositório × métrica:

- a chave é normalizada (minúsculas, sem `https://github.com/`, `.git` ou `/`
  final) antes do alinhamento; repositórios presentes só de um lado são
  contados, não comparados;
- `delta_rel = (replicado − original) / |original|` e `delta_abs = replicado −
  original`; se original = 0, `delta_rel` é indefinido (`original_zero`) e vale
  o absoluto, exceto quando ambos são 0 (`ambos_zero`, diferença nula);
- célula vazia, `NA`, `NaN` ou `null` é ausência (`ausente_original`,
  `ausente_replicado`), nunca zero; vírgula decimal é aceita;
- a execução parcial aparece na cobertura: `n` comparável por métrica e
  repositórios em comum sobre o tamanho da subamostra (`--sample-size`, 30).

Categorias: % de repositórios com a mesma categoria entre os que têm as duas,
e a matriz de mudanças `original -> replicado`.

Saídas: `comparacao.json`, `comparacao.md`, `comparacao_repositorios.csv` e
`comparacao_tabela.tex` (tabela para o artigo).
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from lab03.analysis.stats import fmt, median_iqr

MISSING = frozenset({"", "na", "n/a", "nan", "null", "none", "-"})
SIDES = ("original", "replicated")
DEFAULT_TOLERANCE = 0.05
DEFAULT_SAMPLE_SIZE = 30


def normalize_key(value: str) -> str:
    key = value.strip().lower()
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if key.startswith(prefix):
            key = key[len(prefix):]
    key = key.rstrip("/")
    return key[:-4] if key.endswith(".git") else key


def parse_number(value) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in MISSING:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    number = float(text)
    return None if number != number else number  # NaN numérico também é ausência


def parse_category(value) -> str | None:
    text = (value or "").strip()
    return None if text.lower() in MISSING else text.capitalize()


def validate_mapping(mapping: dict) -> None:
    for side in SIDES:
        if side not in mapping or "key" not in mapping[side]:
            raise ValueError(f"Mapeamento sem '{side}.key'.")
    for section in ("metrics", "categories"):
        names = [set(mapping[side].get(section, {})) for side in SIDES]
        if names[0] != names[1]:
            raise ValueError(f"'{section}' difere entre original e replicado: "
                             f"{sorted(names[0] ^ names[1])}")
    if not mapping["original"].get("metrics") and not mapping["original"].get("categories"):
        raise ValueError("Mapeamento sem métricas nem categorias.")


def load_side(path: Path, spec: dict) -> dict[str, dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        wanted = {spec["key"], *spec.get("metrics", {}).values(), *spec.get("categories", {}).values()}
        if missing := sorted(wanted - columns):
            raise ValueError(f"{path}: colunas ausentes {missing}")
        rows: dict[str, dict] = {}
        for line, raw in enumerate(reader, start=2):
            key = normalize_key(raw[spec["key"]] or "")
            if not key:
                raise ValueError(f"{path}:{line}: chave vazia")
            if key in rows:
                raise ValueError(f"{path}:{line}: repositório duplicado {key}")
            try:
                metrics = {name: parse_number(raw[column])
                           for name, column in spec.get("metrics", {}).items()}
            except ValueError as error:
                raise ValueError(f"{path}:{line}: valor não numérico ({error})") from None
            rows[key] = {
                "metrics": metrics,
                "categories": {name: parse_category(raw[column])
                               for name, column in spec.get("categories", {}).items()},
            }
    return rows


def compare_value(original: float | None, replicated: float | None) -> dict:
    if original is None:
        status = "ausente_original"
    elif replicated is None:
        status = "ausente_replicado"
    elif original == 0:
        status = "ambos_zero" if replicated == 0 else "original_zero"
    else:
        status = "comparavel"
    both = original is not None and replicated is not None
    delta_abs = replicated - original if both else None
    delta_rel = (0.0 if status == "ambos_zero"
                 else delta_abs / abs(original) if status == "comparavel" else None)
    return {"original": original, "replicated": replicated, "status": status,
            "delta_abs": delta_abs, "delta_rel": delta_rel}


def compare(original: dict, replicated: dict, *, tolerance: float = DEFAULT_TOLERANCE,
            sample_size: int = DEFAULT_SAMPLE_SIZE) -> dict:
    common = sorted(set(original) & set(replicated))
    first = next(iter(original.values()), {"metrics": {}, "categories": {}})
    metric_names, category_names = list(first["metrics"]), list(first["categories"])
    per_repository = []
    for key in common:
        entry = {"repositorio": key, "metrics": {}, "categories": {}}
        for name in metric_names:
            entry["metrics"][name] = compare_value(original[key]["metrics"][name],
                                                   replicated[key]["metrics"][name])
        for name in category_names:
            before, after = original[key]["categories"][name], replicated[key]["categories"][name]
            entry["categories"][name] = {"original": before, "replicated": after,
                                         "same": None if before is None or after is None
                                         else before == after}
        per_repository.append(entry)

    metrics = {}
    for name in metric_names:
        values = [entry["metrics"][name] for entry in per_repository]
        statuses = {status: sum(v["status"] == status for v in values)
                    for status in ("comparavel", "ambos_zero", "original_zero",
                                   "ausente_original", "ausente_replicado")}
        relative = [v["delta_rel"] for v in values if v["delta_rel"] is not None]
        absolute = [v["delta_abs"] for v in values if v["delta_abs"] is not None]
        metrics[name] = {
            "n_comparable": len(relative), "n_with_both": len(absolute), "statuses": statuses,
            "delta_rel": median_iqr(relative),
            "abs_delta_rel_median": median_iqr([abs(v) for v in relative])["median"],
            "within_tolerance": (sum(abs(v) <= tolerance for v in relative) / len(relative)
                                 if relative else None),
            "delta_abs": median_iqr(absolute),
        }
    categories = {}
    for name in category_names:
        pairs = [entry["categories"][name] for entry in per_repository
                 if entry["categories"][name]["same"] is not None]
        transitions: dict[str, int] = {}
        for pair in pairs:
            label = f"{pair['original']} -> {pair['replicated']}"
            transitions[label] = transitions.get(label, 0) + 1
        categories[name] = {
            "n": len(pairs), "same": sum(p["same"] for p in pairs),
            "same_proportion": sum(p["same"] for p in pairs) / len(pairs) if pairs else None,
            "transitions": dict(sorted(transitions.items())),
        }
    return {
        "tolerance": tolerance, "sample_size": sample_size,
        "coverage": {
            "original": len(original), "replicated": len(replicated), "common": len(common),
            "only_original": sorted(set(original) - set(replicated)),
            "only_replicated": sorted(set(replicated) - set(original)),
            "common_over_sample": len(common) / sample_size if sample_size else None,
            "partial": len(common) < sample_size,
        },
        "metrics": metrics, "categories": categories, "repositories": per_repository,
    }


def _pct(value):
    return "—" if value is None else f"{100 * value:.1f}%"


def markdown(result: dict) -> str:
    coverage = result["coverage"]
    lines = [
        "# Comparação original × replicado", "",
        f"Repositórios: original {coverage['original']}, replicado {coverage['replicated']}, "
        f"em comum {coverage['common']} de {result['sample_size']} "
        f"({_pct(coverage['common_over_sample'])}){' — execução parcial' if coverage['partial'] else ''}.",
        f"Só no original: {', '.join(coverage['only_original']) or 'nenhum'}. "
        f"Só no replicado: {', '.join(coverage['only_replicated']) or 'nenhum'}.", "",
        f"| Métrica | n comparável | Δ rel. mediana [Q1–Q3] | mediana \\|Δ rel.\\| | "
        f"\\|Δ rel.\\| ≤ {_pct(result['tolerance'])} | Δ abs. mediana | original = 0 | ausentes (orig./repl.) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, m in result["metrics"].items():
        s = m["statuses"]
        lines.append(
            f"| {name} | {m['n_comparable']} | {_pct(m['delta_rel']['median'])} "
            f"[{_pct(m['delta_rel']['q1'])}–{_pct(m['delta_rel']['q3'])}] | "
            f"{_pct(m['abs_delta_rel_median'])} | {_pct(m['within_tolerance'])} | "
            f"{fmt(m['delta_abs']['median'])} | {s['original_zero']} | "
            f"{s['ausente_original']}/{s['ausente_replicado']} |")
    if result["categories"]:
        lines += ["", "| Categoria | n | mesma categoria | mudanças |", "|---|---:|---:|---|"]
        for name, c in result["categories"].items():
            changes = ", ".join(f"{t}: {n}" for t, n in c["transitions"].items()
                                if t.split(" -> ")[0] != t.split(" -> ")[1]) or "nenhuma"
            lines.append(f"| {name} | {c['n']} | {c['same']} ({_pct(c['same_proportion'])}) | {changes} |")
    lines += ["", "Δ rel. = (replicado − original) / |original|. Original = 0 com replicado ≠ 0 "
              "não tem Δ relativo (ver Δ abs.); ambos 0 contam como Δ = 0."]
    return "\n".join(lines) + "\n"


def latex(result: dict) -> str:
    def pct(value):
        return "--" if value is None else f"{100 * value:.1f}\\%".replace(".", "{,}")

    lines = [
        "% Gerado por lab03.replication.compare; não editar à mão.",
        "\\begin{table}[ht]", "\\centering",
        f"\\caption{{Replicação: diferenças por métrica ({result['coverage']['common']} de "
        f"{result['sample_size']} repositórios em comum).}}",
        "\\label{tab:replicacao}", "\\small", "\\begin{tabular}{lrrrr}", "\\hline",
        f"Métrica & $n$ & $\\Delta_{{rel}}$ mediana & $|\\Delta_{{rel}}| \\le {pct(result['tolerance'])}$ "
        "& Mesma categoria \\\\", "\\hline",
    ]
    for name, m in result["metrics"].items():
        category = result["categories"].get(name)
        same = pct(category["same_proportion"]) if category else "--"
        lines.append(f"{name.replace('_', '\\_')} & {m['n_comparable']} & "
                     f"{pct(m['delta_rel']['median'])} & {pct(m['within_tolerance'])} & {same} \\\\")
    for name, c in result["categories"].items():
        if name not in result["metrics"]:
            lines.append(f"{name.replace('_', '\\_')} (categoria) & {c['n']} & -- & -- & "
                         f"{pct(c['same_proportion'])} \\\\")
    lines += ["\\hline", "\\end{tabular}", "\\end{table}"]
    return "\n".join(lines) + "\n"


def write_repositories(path: Path, result: dict) -> None:
    fields = ("repositorio", "tipo", "nome", "original", "replicado", "status", "delta_abs",
              "delta_rel", "mesma_categoria")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in result["repositories"]:
            for name, v in entry["metrics"].items():
                writer.writerow({"repositorio": entry["repositorio"], "tipo": "metrica", "nome": name,
                                 "original": v["original"], "replicado": v["replicated"],
                                 "status": v["status"], "delta_abs": v["delta_abs"],
                                 "delta_rel": v["delta_rel"], "mesma_categoria": None})
            for name, c in entry["categories"].items():
                writer.writerow({"repositorio": entry["repositorio"], "tipo": "categoria", "nome": name,
                                 "original": c["original"], "replicado": c["replicated"],
                                 "status": None, "delta_abs": None, "delta_rel": None,
                                 "mesma_categoria": c["same"]})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--replicated", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                        help="|Δ relativo| considerado concordante (padrão 0,05)")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    args = parser.parse_args(argv)
    try:
        mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
        validate_mapping(mapping)
        result = compare(load_side(args.original, mapping["original"]),
                         load_side(args.replicated, mapping["replicated"]),
                         tolerance=args.tolerance, sample_size=args.sample_size)
    except (OSError, KeyError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "comparacao.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "comparacao.md").write_text(markdown(result), encoding="utf-8")
    (args.output_dir / "comparacao_tabela.tex").write_text(latex(result), encoding="utf-8")
    write_repositories(args.output_dir / "comparacao_repositorios.csv", result)
    coverage = result["coverage"]
    print(f"{coverage['common']} repositórios em comum ({coverage['original']} original, "
          f"{coverage['replicated']} replicado).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
