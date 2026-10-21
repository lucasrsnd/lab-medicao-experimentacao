"""Validação parcial do CFR (b) com um avaliador humano (amostra-ouro, 1ª rodada).

    python -m lab03.analysis.cfr_b_validation --dataset data/amostra_completa.json.gz --output-dir analysis/validacao_cfr_b

Desvio do protocolo (decisão do grupo): a rodada `labels/reamostragem-v2/` não
foi rotulada e o avaliador C não rotulou a 1ª rodada. Sem dois avaliadores
humanos não há consenso; por isso os rótulos do avaliador B (humano) servem de
referência e o resultado é uma validação de avaliador único, não um F1 contra
consenso.

A 1ª rodada (`labels/amostra_ouro_*`) foi sorteada da coleta de 2026-10-13, a
mesma do snapshot analisado, mas sobre um conjunto maior de repositórios. Só
entram as releases cujo repositório está no snapshot e cujo `release_id` e
veredito da heurística conferem; as demais são contadas como excluídas.

Os rótulos do avaliador A são rascunhos gerados por IA (marcados
`[rascunho IA]`). Entram apenas como referência auxiliar declarada (LLM):
concordância B × LLM e LLM × heurística, nunca como segundo avaliador.

Saídas: `resultados.json`, `resultados.md` e `releases.csv`.
"""

import argparse
import csv
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

from lab03.analysis.stats import fmt as _fmt
from lab03.manual_validation import evaluate_heuristic, heuristic_predictions

AI_DRAFT_MARK = "[rascunho IA]"
Z_95 = 1.959963984540054


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_dataset(path: Path) -> dict:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(successes: int, total: int) -> list[float] | None:
    """Intervalo de Wilson a 95% para uma proporção; None se total = 0."""
    if total == 0:
        return None
    p = successes / total
    denominator = 1 + Z_95 ** 2 / total
    center = (p + Z_95 ** 2 / (2 * total)) / denominator
    half = Z_95 * math.sqrt(p * (1 - p) / total + Z_95 ** 2 / (4 * total ** 2)) / denominator
    return [max(0.0, center - half), min(1.0, center + half)]


def cohen_kappa(first: list[str], second: list[str]) -> float | None:
    n = len(first)
    if n == 0:
        return None
    observed = sum(a == b for a, b in zip(first, second)) / n
    categories = set(first) | set(second)
    expected = sum((first.count(c) / n) * (second.count(c) / n) for c in categories)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def _labels_by_tag(rows: list[dict]) -> dict:
    return {(r["repositorio"].strip(), r["tag"].strip()): r for r in rows}


def match_sample(dataset: dict, sample_rows: list[dict]) -> tuple[list[dict], dict]:
    """Separa as releases-ouro presentes no snapshot das excluídas (com motivo)."""
    reports = {i["metadata"]["full_name"]: i["report"] for i in dataset["repositories"]}
    matched, excluded = [], {}
    for row in sample_rows:
        name, tag, release_id = row["repositorio"].strip(), row["tag"].strip(), row["release_id"].strip()
        report = reports.get(name)
        result = report.get("delivery_failure_rate") if report else None
        ids = {r["tag"]: str(r["id"]) for r in report["catalog"]["releases"]} if report else {}
        verdicts = {v["tag"] for v in result["verdicts"]} if result else set()
        reason = ("repositorio_fora_do_snapshot" if report is None
                  else "sem_cfr_b" if result is None
                  else "release_id_diferente" if ids.get(tag) != release_id
                  else "sem_veredito" if tag not in verdicts else None)
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
        else:
            matched.append(row)
    return matched, excluded


def analyze(dataset: dict, sample_rows: list[dict], rater_b: list[dict], rater_a: list[dict]) -> dict:
    matched, excluded = match_sample(dataset, sample_rows)
    version, predictions = heuristic_predictions(dataset, matched)
    b_labels, a_labels = _labels_by_tag(rater_b), _labels_by_tag(rater_a)
    keys = [(r["repositorio"].strip(), r["tag"].strip()) for r in matched]
    missing = [k for k in keys if k not in b_labels or k not in a_labels]
    if missing:
        raise ValueError(f"Releases-ouro sem rótulo de A ou B: {missing[:5]}")
    a_ai_drafts = sum(AI_DRAFT_MARK in a_labels[k].get("observacoes", "") for k in keys)

    releases = []
    for row, key, prediction in zip(matched, keys, predictions):
        releases.append({
            "repositorio": key[0], "tag": key[1], "release_id": prediction["release_id"],
            "rotulo_b": b_labels[key]["e_corretiva"].strip(),
            "rotulo_a_llm": a_labels[key]["e_corretiva"].strip(),
            "e_corretiva_heuristica": prediction["e_corretiva_heuristica"],
        })

    def evaluate(field: str) -> dict:
        reference = [{"repositorio": r["repositorio"], "release_id": r["release_id"],
                      "consenso_e_corretiva": r[field]} for r in releases]
        result = evaluate_heuristic(reference, predictions, heuristic_version=version)
        (tn, fp), (fn, tp) = result["confusion_matrix"]["values"]
        result["confusion_matrix"]["rows_are_consensus"] = False
        result["confusion_matrix"]["rows_are_reference"] = field
        result["precision_ci95"] = wilson(tp, tp + fp)
        result["recall_ci95"] = wilson(tp, tp + fn)
        result["accuracy"] = (tp + tn) / (tp + tn + fp + fn) if releases else None
        result.pop("evaluation_complete_for_300_releases")
        return result

    b, a = [r["rotulo_b"] for r in releases], [r["rotulo_a_llm"] for r in releases]
    return {
        "schema_version": 1,
        "heuristic_version": version,
        "protocol_deviation": (
            "Avaliador humano único (B); sem consenso. Rótulos de A são rascunhos de IA "
            "e entram só como referência auxiliar declarada."
        ),
        "sample": {
            "gold_releases": len(sample_rows),
            "gold_repositories": len({r["repositorio"] for r in sample_rows}),
            "evaluated_releases": len(releases),
            "evaluated_repositories": len({r["repositorio"] for r in releases}),
            "excluded": excluded,
            "positives_b": b.count("sim"),
            "a_rows_marked_ai_draft": a_ai_drafts,
        },
        "heuristic_vs_b": evaluate("rotulo_b"),
        "auxiliary_llm": {
            "kappa_b_vs_llm": cohen_kappa(b, a),
            "agreement_b_vs_llm": sum(x == y for x, y in zip(b, a)) / len(b) if b else None,
            "heuristic_vs_llm": evaluate("rotulo_a_llm"),
        },
        "limitations": [
            "Um único avaliador humano: sem medida de confiabilidade entre avaliadores.",
            "Releases sorteadas de uma população maior que o snapshot; só os repositórios "
            "presentes no snapshot são avaliados.",
            "Releases do mesmo repositório não são independentes; os intervalos de Wilson "
            "ignoram esse agrupamento e tendem a ser estreitos demais.",
        ],
        "_releases": releases,
    }


def markdown(analysis: dict) -> str:
    s, h = analysis["sample"], analysis["heuristic_vs_b"]
    (tn, fp), (fn, tp) = h["confusion_matrix"]["values"]
    aux = analysis["auxiliary_llm"]

    def ci(value):
        return "—" if value is None else f"[{value[0]:.3f}; {value[1]:.3f}]"

    excluded = ", ".join(f"{k}: {v}" for k, v in s["excluded"].items()) or "nenhuma"
    lines = [
        "# Validação parcial do CFR (b) — avaliador único", "",
        f"**Desvio do protocolo:** {analysis['protocol_deviation']}", "",
        f"Heurística {analysis['heuristic_version']}. Releases avaliadas: "
        f"{s['evaluated_releases']} de {s['gold_releases']} "
        f"({s['evaluated_repositories']} de {s['gold_repositories']} repositórios). "
        f"Excluídas: {excluded}. Corretivas segundo B: {s['positives_b']}.", "",
        "| Referência B \\ Heurística | não | sim |", "|---|---:|---:|",
        f"| não | {tn} | {fp} |", f"| sim | {fn} | {tp} |", "",
        "| Métrica | valor | IC 95% (Wilson) |", "|---|---:|---|",
        f"| Precisão | {_fmt(h['precision'])} | {ci(h['precision_ci95'])} |",
        f"| Recall | {_fmt(h['recall'])} | {ci(h['recall_ci95'])} |",
        f"| F1 | {_fmt(h['f1'])} | — |",
        f"| Acurácia | {_fmt(h['accuracy'])} | — |", "",
        "## Referência auxiliar (LLM, não é avaliador)", "",
        f"{s['a_rows_marked_ai_draft']} rótulos de A marcados `[rascunho IA]`. "
        f"κ de Cohen B × LLM = {_fmt(aux['kappa_b_vs_llm'])} "
        f"(concordância {_fmt(aux['agreement_b_vs_llm'])}). "
        f"Heurística × LLM: precisão {_fmt(aux['heuristic_vs_llm']['precision'])}, "
        f"recall {_fmt(aux['heuristic_vs_llm']['recall'])}, "
        f"F1 {_fmt(aux['heuristic_vs_llm']['f1'])}.", "",
        "## Limitações", "",
        *[f"- {item}" for item in analysis["limitations"]],
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, default=Path("data/amostra_completa.json.gz"))
    parser.add_argument("--sample", type=Path, default=Path("labels/amostra_ouro_releases.csv"))
    parser.add_argument("--rater-b", type=Path, default=Path("labels/rotulos_B_releases.csv"))
    parser.add_argument("--rater-a-llm", type=Path, default=Path("labels/rotulos_A_releases.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/validacao_cfr_b"))
    args = parser.parse_args(argv)
    inputs = {"dataset": args.dataset, "sample": args.sample,
              "rater_b": args.rater_b, "rater_a_llm": args.rater_a_llm}
    try:
        analysis = analyze(_load_dataset(args.dataset), _read_csv(args.sample),
                           _read_csv(args.rater_b), _read_csv(args.rater_a_llm))
        analysis["input_sha256"] = {name: _sha256(path) for name, path in inputs.items()}
    except (OSError, KeyError, ValueError, RuntimeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    releases = analysis.pop("_releases")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "resultados.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "resultados.md").write_text(markdown(analysis), encoding="utf-8")
    with (args.output_dir / "releases.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(releases[0]) if releases else ["repositorio"])
        writer.writeheader()
        writer.writerows(releases)
    h = analysis["heuristic_vs_b"]
    print(f"n={h['evaluated_releases']} precisao={_fmt(h['precision'])} "
          f"recall={_fmt(h['recall'])} f1={_fmt(h['f1'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
