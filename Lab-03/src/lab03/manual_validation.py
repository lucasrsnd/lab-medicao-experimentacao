"""Fleiss agreement, consensus drafts and gold-sample heuristic evaluation."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

RATERS = ("A", "B", "C")
REPOSITORY_LABELS = {
    "tipo_projeto": (
        "biblioteca/framework",
        "aplicacao/servico",
        "ferramenta CLI",
        "outro",
        "incerto",
    ),
    "releases_sao_entregas": ("sim", "nao", "incerto"),
}
RELEASE_LABELS = {"e_corretiva": ("sim", "nao", "incerto")}
F1_THRESHOLD = 0.70


def _read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_label_file(path, key_fields, label_fields, allowed):
    result = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = set(key_fields) | set(label_fields)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: faltam colunas obrigatórias {sorted(required)}.")
        for line, row in enumerate(reader, start=2):
            key = tuple((row[field] or "").strip() for field in key_fields)
            if any(not value for value in key):
                raise ValueError(f"{path}:{line}: chave vazia.")
            if key in result:
                raise ValueError(f"{path}:{line}: chave duplicada {key}.")
            labels = {field: (row[field] or "").strip() for field in label_fields}
            for field, label in labels.items():
                if label and label not in allowed[field]:
                    raise ValueError(f"{path}:{line}: rótulo inválido {field}={label!r}.")
            result[key] = labels
    return result


def _read_sample(manifest_path, repositories_path, releases_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    repository_rows = _read_csv(repositories_path)
    release_rows = _read_csv(releases_path)
    if manifest.get("repositories") != 60 or manifest.get("releases") != 300:
        raise ValueError("Manifesto da amostra deve registrar 60 repositórios e 300 releases.")
    if not repository_rows or not {"repositorio"}.issubset(repository_rows[0]):
        raise ValueError("CSV da amostra deve conter a coluna repositorio.")
    if not release_rows or not {"repositorio", "release_id"}.issubset(release_rows[0]):
        raise ValueError("CSV de releases da amostra deve conter repositorio e release_id.")
    repository_keys = [((row["repositorio"] or "").strip(),) for row in repository_rows]
    release_keys = [
        ((row["repositorio"] or "").strip(), (row["release_id"] or "").strip())
        for row in release_rows
    ]
    if len(repository_keys) != 60 or len(set(repository_keys)) != 60:
        raise ValueError("A amostra precisa conter 60 repositórios únicos.")
    if len(release_keys) != 300 or len(set(release_keys)) != 300:
        raise ValueError("A amostra precisa conter 300 releases únicas.")
    if {name for name, in repository_keys} != {name for name, _ in release_keys}:
        raise ValueError("A lista de releases não corresponde aos 60 repositórios sorteados.")
    releases_per_repository = {
        name: sum(sample_name == name for sample_name, _ in release_keys)
        for name, in repository_keys
    }
    if set(releases_per_repository.values()) != {5}:
        raise ValueError("A amostra precisa conter exatamente cinco releases por repositório.")
    return repository_keys, release_keys


def _fleiss_dimension(keys, ratings_by_rater, field, categories):
    complete_rows = []
    missing_by_rater = {rater: 0 for rater in RATERS}
    category_counts = {rater: {label: 0 for label in categories} for rater in RATERS}
    incomplete_items = 0
    for key in keys:
        values = []
        for rater in RATERS:
            label = ratings_by_rater[rater].get(key, {}).get(field, "")
            if label:
                category_counts[rater][label] += 1
            else:
                missing_by_rater[rater] += 1
            values.append(label)
        if all(values):
            complete_rows.append(values)
        else:
            incomplete_items += 1

    kappa = None
    undefined_reason = None
    if not complete_rows:
        undefined_reason = "no_complete_items"
    else:
        try:
            from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa
        except ImportError as error:
            raise RuntimeError(
                "Instale statsmodels: python -m pip install -e '.[dev,validation]'"
            ) from error
        observed_categories = sorted({label for row in complete_rows for label in row})
        category_index = {label: index for index, label in enumerate(observed_categories)}
        table, _ = aggregate_raters([
            [category_index[label] for label in row]
            for row in complete_rows
        ])
        value = float(fleiss_kappa(table, method="fleiss"))
        if math.isfinite(value):
            kappa = value
        else:
            undefined_reason = "fleiss_kappa_undefined_for_observed_marginals"

    interpretation = None
    if kappa is not None:
        if kappa < 0:
            interpretation = "poor"
        elif kappa <= 0.20:
            interpretation = "slight"
        elif kappa <= 0.40:
            interpretation = "fair"
        elif kappa <= 0.60:
            interpretation = "moderate"
        elif kappa <= 0.80:
            interpretation = "substantial"
        else:
            interpretation = "almost_perfect"
    return {
        "expected_items": len(keys),
        "items_with_three_labels": len(complete_rows),
        "items_missing_at_least_one_label": incomplete_items,
        "missing_labels_by_rater": missing_by_rater,
        "categories": list(categories),
        "category_counts_by_rater": category_counts,
        "fleiss_kappa": kappa,
        "kappa_defined": kappa is not None,
        "interpretation": interpretation,
        "undefined_reason": undefined_reason,
        "low_agreement": kappa is not None and kappa < 0.21,
    }


def calculate_agreement(manifest_path, repositories_path, releases_path, rater_files):
    repository_keys, release_keys = _read_sample(
        manifest_path, repositories_path, releases_path
    )
    if set(rater_files) != set(RATERS):
        raise ValueError(f"Forneça exatamente os avaliadores {', '.join(RATERS)}.")
    raters = {}
    for rater in RATERS:
        repository_labels = _read_label_file(
            rater_files[rater]["repositories"],
            ("repositorio",),
            tuple(REPOSITORY_LABELS),
            REPOSITORY_LABELS,
        )
        release_labels = _read_label_file(
            rater_files[rater]["releases"],
            ("repositorio", "release_id"),
            tuple(RELEASE_LABELS),
            RELEASE_LABELS,
        )
        if set(repository_labels) - set(repository_keys):
            raise ValueError(f"Avaliador {rater}: repositório fora da amostra.")
        if set(release_labels) - set(release_keys):
            raise ValueError(f"Avaliador {rater}: release fora da amostra.")
        raters[rater] = {
            "repositories": repository_labels,
            "releases": release_labels,
        }

    dimensions = {}
    for field, categories in REPOSITORY_LABELS.items():
        dimensions[field] = _fleiss_dimension(
            repository_keys,
            {rater: raters[rater]["repositories"] for rater in RATERS},
            field,
            categories,
        )
    for field, categories in RELEASE_LABELS.items():
        dimensions[field] = _fleiss_dimension(
            release_keys,
            {rater: raters[rater]["releases"] for rater in RATERS},
            field,
            categories,
        )

    repository_draft = []
    for (repository,) in repository_keys:
        row = {"repositorio": repository}
        for rater in RATERS:
            values = raters[rater]["repositories"].get((repository,), {})
            for field in REPOSITORY_LABELS:
                row[f"{field}_{rater}"] = values.get(field, "")
        row["consenso_tipo_projeto"] = ""
        row["consenso_releases_sao_entregas"] = ""
        row["decision_notes"] = ""
        repository_draft.append(row)

    release_draft = []
    for repository, release_id in release_keys:
        row = {"repositorio": repository, "release_id": release_id}
        for rater in RATERS:
            values = raters[rater]["releases"].get((repository, release_id), {})
            row[f"e_corretiva_{rater}"] = values.get("e_corretiva", "")
        row["consenso_e_corretiva"] = ""
        row["decision_notes"] = ""
        release_draft.append(row)

    return {
        "schema_version": 1,
        "raters": list(RATERS),
        "dimensions": dimensions,
        "repository_consensus_draft": repository_draft,
        "release_consensus_draft": release_draft,
    }


def heuristic_predictions(dataset, sample_release_rows):
    """Project frozen full-run verdicts onto the 300 sampled release IDs."""
    reports = {
        item["metadata"]["full_name"]: item["report"]
        for item in dataset["repositories"]
    }
    version_set = set()
    verdicts_by_repo = {}
    for name, report in reports.items():
        result = report.get("delivery_failure_rate")
        if result is None:
            continue
        version_set.add(result["heuristic_version"])
        verdicts = {verdict["tag"]: verdict for verdict in result["verdicts"]}
        release_ids = {
            release["tag"]: str(release["id"])
            for release in report["catalog"]["releases"]
        }
        verdicts_by_repo[name] = (verdicts, release_ids)
    if len(version_set) != 1:
        raise ValueError("Dataset não tem exatamente uma versão consistente da heurística.")
    version = next(iter(version_set))

    predictions = []
    for sample in sample_release_rows:
        name = sample["repositorio"].strip()
        tag = sample["tag"].strip()
        release_id = str(sample["release_id"]).strip()
        if name not in verdicts_by_repo:
            raise ValueError(f"Sem resultado da heurística para {name}.")
        verdicts, release_ids = verdicts_by_repo[name]
        if tag not in verdicts or release_ids.get(tag) != release_id:
            raise ValueError(f"Release-ouro não corresponde ao resultado: {name} {tag}.")
        predictions.append({
            "repositorio": name,
            "release_id": release_id,
            "e_corretiva_heuristica": "sim" if verdicts[tag]["corrective"] else "nao",
        })
    return version, predictions


def evaluate_heuristic(consensus_rows, prediction_rows, *, heuristic_version):
    """Evaluate the frozen binary heuristic against discussed gold labels."""
    try:
        from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
    except ImportError as error:
        raise RuntimeError(
            "Instale scikit-learn: python -m pip install -e '.[dev,validation]'"
        ) from error
    if not heuristic_version.strip():
        raise ValueError("Informe a versão congelada da heurística.")
    consensus = {}
    for row in consensus_rows:
        key = ((row.get("repositorio") or "").strip(), str(row.get("release_id") or "").strip())
        if not all(key) or key in consensus:
            raise ValueError(f"Chave de consenso vazia ou duplicada: {key}.")
        label = (row.get("consenso_e_corretiva") or "").strip()
        if label and label not in ("sim", "nao", "incerto"):
            raise ValueError(f"Rótulo de consenso inválido: {label!r}")
        consensus[key] = label
    predictions = {}
    for row in prediction_rows:
        key = ((row.get("repositorio") or "").strip(), str(row.get("release_id") or "").strip())
        if not all(key) or key in predictions:
            raise ValueError(f"Chave de previsão vazia ou duplicada: {key}.")
        row_version = (row.get("heuristic_version") or "").strip()
        if row_version and row_version != heuristic_version:
            raise ValueError(
                f"Previsão {key} usa {row_version}, não {heuristic_version}."
            )
        prediction = (row.get("e_corretiva_heuristica") or "").strip()
        if prediction not in ("sim", "nao"):
            raise ValueError(f"Previsão inválida para {key}: {prediction!r}")
        predictions[key] = prediction

    keys = sorted(set(consensus) | set(predictions))
    evaluated = [
        key for key in keys
        if consensus.get(key) in ("sim", "nao") and key in predictions
    ]
    y_true = [consensus[key] for key in evaluated]
    y_pred = [predictions[key] for key in evaluated]
    if evaluated:
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true,
            y_pred,
            labels=["nao", "sim"],
            pos_label="sim",
            average="binary",
            zero_division=0,
        )
        matrix = confusion_matrix(y_true, y_pred, labels=["nao", "sim"]).tolist()
        metrics = {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        }
        refinement_required = float(f1) < F1_THRESHOLD
    else:
        matrix = [[0, 0], [0, 0]]
        metrics = {"precision": None, "recall": None, "f1": None}
        refinement_required = None
    return {
        "schema_version": 1,
        "heuristic_version": heuristic_version,
        "positive_label": "sim",
        "confusion_matrix": {
            "labels": ["nao", "sim"],
            "rows_are_consensus": True,
            "columns_are_heuristic": True,
            "values": matrix,
        },
        "metrics": metrics,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "expected_releases": len(consensus),
        "releases_with_prediction": len(set(consensus) & set(predictions)),
        "evaluated_releases": len(evaluated),
        "excluded_missing_or_uncertain_consensus": sum(
            consensus.get(key) not in ("sim", "nao") for key in keys
        ),
        "excluded_missing_prediction": sum(
            label in ("sim", "nao") and key not in predictions
            for key, label in consensus.items()
        ),
        "predictions_without_consensus": sum(key not in consensus for key in predictions),
        "evaluation_complete_for_300_releases": (
            len(consensus) == 300 and len(evaluated) == 300
        ),
        "refinement_required_if_f1_below_0_70": refinement_required,
        "limitations": [
            "A amostra usada para refinar e avaliar é a mesma; há viés de ajuste.",
            "Rótulos incertos ou ausentes não entram nas métricas binárias e são contados.",
        ],
    }


def _write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Não sobrescrever artefato existente: {path}")
    if not rows:
        raise ValueError(f"Nenhuma linha para gravar em {path}.")
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Não sobrescrever artefato existente: {path}")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    agreement = subparsers.add_parser("agreement", help="calcular Fleiss e criar rascunhos")
    agreement.add_argument("--sample-manifest", type=Path, required=True)
    agreement.add_argument("--sample-repositories", type=Path, required=True)
    agreement.add_argument("--sample-releases", type=Path, required=True)
    for rater in RATERS:
        agreement.add_argument(f"--{rater.lower()}-repositories", type=Path, required=True)
        agreement.add_argument(f"--{rater.lower()}-releases", type=Path, required=True)
    agreement.add_argument("--output-dir", type=Path, required=True)

    predictions = subparsers.add_parser("predictions", help="exportar previsões congeladas para amostra")
    predictions.add_argument("--dataset", type=Path, required=True)
    predictions.add_argument("--sample-releases", type=Path, required=True)
    predictions.add_argument("--output", type=Path, required=True)

    evaluate = subparsers.add_parser("evaluate", help="avaliar heurística contra consenso")
    evaluate.add_argument("--consensus", type=Path, required=True)
    evaluate.add_argument("--predictions", type=Path, required=True)
    evaluate.add_argument("--heuristic-version", required=True)
    evaluate.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "agreement":
            rater_files = {
                rater: {
                    "repositories": getattr(args, f"{rater.lower()}_repositories"),
                    "releases": getattr(args, f"{rater.lower()}_releases"),
                }
                for rater in RATERS
            }
            result = calculate_agreement(
                args.sample_manifest,
                args.sample_repositories,
                args.sample_releases,
                rater_files,
            )
            output_dir = args.output_dir
            output_paths = (
                output_dir / "consenso-repositorios.csv",
                output_dir / "consenso-releases.csv",
                output_dir / "concordancia-fleiss.json",
            )
            existing = [path for path in output_paths if path.exists()]
            if existing:
                raise FileExistsError(f"Não sobrescrever artefato existente: {existing[0]}")
            _write_csv(output_paths[0],
                       result["repository_consensus_draft"])
            _write_csv(output_paths[1],
                       result["release_consensus_draft"])
            result["input_sha256"] = {
                "sample_manifest": _sha256(args.sample_manifest),
                "sample_repositories": _sha256(args.sample_repositories),
                "sample_releases": _sha256(args.sample_releases),
                **{
                    f"{rater}_{kind}": _sha256(path)
                    for rater, files in rater_files.items()
                    for kind, path in files.items()
                },
            }
            _write_json(output_paths[2], {
                "schema_version": result["schema_version"],
                "raters": result["raters"],
                "dimensions": result["dimensions"],
                "input_sha256": result["input_sha256"],
            })
            print(f"Concordância e rascunhos gravados em {output_dir}")
        elif args.command == "predictions":
            dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
            version, rows = heuristic_predictions(
                dataset, _read_csv(args.sample_releases)
            )
            for row in rows:
                row["heuristic_version"] = version
            _write_csv(args.output, rows)
            print(f"{len(rows)} previsões v{version} gravadas em {args.output}")
        else:
            result = evaluate_heuristic(
                _read_csv(args.consensus),
                _read_csv(args.predictions),
                heuristic_version=args.heuristic_version,
            )
            result["input_sha256"] = {
                "consensus": _sha256(args.consensus),
                "predictions": _sha256(args.predictions),
            }
            _write_json(args.output, result)
            print(f"Avaliação gravada em {args.output}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"Validação manual falhou: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
