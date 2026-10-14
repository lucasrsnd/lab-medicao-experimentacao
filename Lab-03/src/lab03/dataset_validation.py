"""Validate frozen Sprint 02 variant exports, keys, units and gold-sample links."""

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from lab03.variants import CSV_FIELDS, METRICS, VARIANTS

CATEGORIES = {"Elite", "High", "Medium", "Low"}
DENOMINATOR_UNITS = {
    "deployment_frequency_per_week": "weeks",
    "lead_time_hours": {
        "C1": "releases",
        "C2": "commits",
        "C3": "commits",
    },
    "change_failure_rate": {
        "C1": "valid_ci_runs",
        "C2": "evaluable_releases",
        "C3": "valid_ci_runs",
    },
    "recovery_time_hours": "recovered_episodes",
}
CLASSIFICATION_FIELDS = (
    "repositorio",
    *(f"{variant}_{suffix}" for variant in VARIANTS for suffix in ("categoria", "status")),
)
GOLD_SAMPLE_FIELDS = {"repositorio", "tag", "release_id", "publicada_em"}


def _read_csv(path, required_columns):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            missing = sorted(required_columns - set(reader.fieldnames or ()))
            raise ValueError(f"{path}: colunas obrigatórias ausentes: {missing}")
        rows = []
        for line, row in enumerate(reader, start=2):
            missing = sorted(column for column in required_columns if row.get(column) is None)
            if missing:
                raise ValueError(f"{path}:{line}: campos truncados no CSV: {missing}")
            rows.append(row)
        return rows


def _number(value, field, *, allow_empty=True):
    text = "" if value is None else str(value).strip()
    if not text and allow_empty:
        return None
    try:
        number = float(text)
    except ValueError as error:
        raise ValueError(f"{field} deve ser numérico ou vazio.") from error
    if not math.isfinite(number):
        raise ValueError(f"{field} deve ser finito.")
    return number


def _same_number(csv_value, json_value, field):
    left = _number(csv_value, field)
    if json_value is None:
        if left is not None:
            raise ValueError(f"{field}: CSV e JSON divergem.")
    elif left is None or not math.isclose(left, float(json_value), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"{field}: CSV e JSON divergem.")


def _validate_metric_row(row, variant):
    repository = (row["repositorio"] or "").strip()
    if not repository or "/" not in repository:
        raise ValueError("repositorio deve usar owner/name.")
    if row["unidade_entrega"] != VARIANTS[variant]["delivery_unit"]:
        raise ValueError(f"{repository} {variant}: unidade_entrega divergente.")
    if row["lead_time_variante"] != VARIANTS[variant]["lead_time"]:
        raise ValueError(f"{repository} {variant}: variante de lead time divergente.")
    if row["cfr_variante"] != VARIANTS[variant]["cfr"]:
        raise ValueError(f"{repository} {variant}: variante de CFR divergente.")
    if row["status_geral"] not in ("classified", "incomplete"):
        raise ValueError(f"{repository} {variant}: status_geral inválido.")
    reported_missing = {
        name for name in row["metricas_ausentes"].split(";") if name
    }
    if row["status_geral"] == "classified":
        if row["categoria_geral"] not in CATEGORIES or row["pontos_gerais"] not in ("1", "2", "3", "4"):
            raise ValueError(f"{repository} {variant}: classificação geral inválida.")
        if reported_missing:
            raise ValueError(f"{repository} {variant}: categoria geral com métricas ausentes.")
    elif row["categoria_geral"] or row["pontos_gerais"]:
        raise ValueError(f"{repository} {variant}: incompleto não pode ter categoria geral.")

    for metric in METRICS:
        value_field = f"{metric}_valor"
        numerator_field = f"{metric}_numerador"
        denominator_field = f"{metric}_denominador"
        unit_field = f"{metric}_unidade_denominador"
        category_field = f"{metric}_categoria"
        reason_field = f"{metric}_motivo_ausencia"
        value = _number(row[value_field], value_field)
        numerator = _number(row[numerator_field], numerator_field)
        denominator = _number(row[denominator_field], denominator_field)
        category = (row[category_field] or "").strip()
        reason = (row[reason_field] or "").strip()
        unit = (row[unit_field] or "").strip()

        if numerator is not None and numerator < 0:
            raise ValueError(f"{repository} {variant}: {numerator_field} negativo.")
        if denominator is not None and denominator < 0:
            raise ValueError(f"{repository} {variant}: {denominator_field} negativo.")
        if numerator is not None and not numerator.is_integer():
            raise ValueError(f"{repository} {variant}: {numerator_field} deve ser inteiro.")
        if metric != "deployment_frequency_per_week":
            if any(
                value is not None and not value.is_integer()
                for value in (numerator, denominator)
            ):
                raise ValueError(f"{repository} {variant}: contagens de {metric} devem ser inteiras.")
        if value is None:
            if category or not reason:
                raise ValueError(
                    f"{repository} {variant}: ausência de {metric} precisa de motivo e sem categoria."
                )
        else:
            if denominator is None or denominator <= 0 or reason:
                raise ValueError(
                    f"{repository} {variant}: observado exige denominador positivo e motivo vazio."
                )
            if category not in CATEGORIES:
                raise ValueError(f"{repository} {variant}: categoria inválida para {metric}.")
            if metric == "change_failure_rate" and not 0 <= value <= 1:
                raise ValueError(f"{repository} {variant}: CFR fora de [0, 1].")
            if metric != "change_failure_rate" and value < 0:
                raise ValueError(f"{repository} {variant}: {metric} não pode ser negativo.")
            if metric in ("deployment_frequency_per_week", "change_failure_rate"):
                if numerator is None or denominator is None or denominator <= 0:
                    raise ValueError(
                        f"{repository} {variant}: {metric} exige numerador e denominador válidos."
                    )
                if metric == "change_failure_rate" and numerator > denominator:
                    raise ValueError(f"{repository} {variant}: falhas excedem o denominador de CFR.")
                if not math.isclose(value, numerator / denominator, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError(f"{repository} {variant}: fórmula de {metric} inconsistente.")
        expected_unit = DENOMINATOR_UNITS.get(metric)
        if expected_unit is None:
            expected_unit = "recovered_episodes"
        if isinstance(expected_unit, dict):
            expected_unit = expected_unit[variant]
        if unit != expected_unit:
            raise ValueError(
                f"{repository} {variant}: unidade de denominador {unit!r}, esperada {expected_unit!r}."
            )

    actual_missing = {
        metric for metric in METRICS if not row[f"{metric}_valor"].strip()
    }
    if reported_missing != actual_missing:
        raise ValueError(
            f"{repository} {variant}: metricas_ausentes não corresponde aos valores vazios."
        )

    censored_cfr = _number(row["cfr_b_releases_censored"], "cfr_b_releases_censored")
    recovery_censored = _number(
        row["recovery_episodes_censored"], "recovery_episodes_censored"
    )
    if censored_cfr is not None and censored_cfr < 0:
        raise ValueError(f"{repository} {variant}: censura de CFR negativa.")
    if recovery_censored is not None and recovery_censored < 0:
        raise ValueError(f"{repository} {variant}: censura de recuperação negativa.")
    if any(value is not None and not value.is_integer() for value in (censored_cfr, recovery_censored)):
        raise ValueError(f"{repository} {variant}: contagens censuradas devem ser inteiras.")
    if variant != "C2" and censored_cfr is not None:
        raise ValueError("Censura de releases só se aplica ao CFR (b) de C2.")
    if row["complemento_disponivel"].strip().lower() not in ("true", "false", ""):
        raise ValueError(f"{repository} {variant}: complemento_disponivel inválido.")
    if variant == "C2" and row["complemento_disponivel"].strip().lower() == "true":
        if censored_cfr is None:
            raise ValueError(f"{repository} C2: contagem de releases censuradas ausente.")


def validate_exports(
    metrics_rows,
    classification_rows,
    variants_payload,
    gold_sample_rows,
    gold_manifest,
    *,
    minimum_repositories=300,
):
    """Check CSV/JSON consistency and explicit zero, missing and censored values."""
    canonical = variants_payload.get("repositories")
    if not isinstance(canonical, dict):
        raise ValueError("variantes.json deve conter o objeto repositories.")
    names = set(canonical)
    if len(names) < minimum_repositories:
        raise ValueError(
            f"Dataset tem {len(names)} repositórios únicos; mínimo {minimum_repositories}."
        )
    if variants_payload.get("coverage", {}).get("status") != "complete":
        raise ValueError("A cobertura da coleta/seleção não está completa.")
    if gold_manifest.get("repositories") != 60 or gold_manifest.get("releases") != 300:
        raise ValueError("Manifesto da amostra-ouro deve registrar 60 repositórios e 300 releases.")
    source_hash = gold_manifest.get("source_dataset_sha256")
    dataset_hashes = {
        item.get("sha256") for item in variants_payload.get("datasets", [])
    }
    if not source_hash or source_hash not in dataset_hashes:
        raise ValueError("A amostra-ouro e o dataset congelado têm hashes de origem diferentes.")
    if len(metrics_rows) != len(names) * len(VARIANTS):
        raise ValueError("variantes_metricas.csv deve ter três linhas por repositório.")
    metric_index = {}
    for row in metrics_rows:
        variant = row["variante"].strip()
        name = row["repositorio"].strip()
        key = (name, variant)
        if variant not in VARIANTS or key in metric_index:
            raise ValueError(f"Chave (repositorio, variante) inválida ou duplicada: {key}.")
        if name not in names:
            raise ValueError(f"{name} não consta em variantes.json.")
        _validate_metric_row(row, variant)
        metric_index[key] = row
        classification = canonical[name][variant]["classification"]
        for metric in METRICS:
            source = classification["metrics"][metric]
            for suffix, json_field in (
                ("valor", "value"),
                ("numerador", "numerator"),
                ("denominador", "denominator"),
            ):
                _same_number(
                    row[f"{metric}_{suffix}"],
                    source[json_field],
                    f"{name} {variant} {metric} {suffix}",
                )
            if row[f"{metric}_categoria"].strip() != (source["category"] or ""):
                raise ValueError(f"{name} {variant}: categoria de {metric} difere do JSON.")
            if row[f"{metric}_motivo_ausencia"].strip() != (source["missing_reason"] or ""):
                raise ValueError(f"{name} {variant}: motivo de {metric} difere do JSON.")
            expected_unit = source["denominator_unit"] or ""
            if row[f"{metric}_unidade_denominador"].strip() != expected_unit:
                raise ValueError(f"{name} {variant}: unidade de {metric} difere do JSON.")
        if row["categoria_geral"].strip() != (
            classification["overall"]["category"] or ""
        ):
            raise ValueError(f"{name} {variant}: categoria geral difere do JSON.")
        if row["status_geral"].strip() != classification["overall"]["status"]:
            raise ValueError(f"{name} {variant}: status geral difere do JSON.")
        if row["pontos_gerais"].strip() != (
            "" if classification["overall"]["points"] is None
            else str(classification["overall"]["points"])
        ):
            raise ValueError(f"{name} {variant}: pontos gerais diferem do JSON.")
        if row["metricas_ausentes"].strip().split(";") != classification["overall"]["missing_metrics"]:
            raise ValueError(f"{name} {variant}: metricas_ausentes diferem do JSON.")
        expected_censored_cfr = canonical[name][variant].get("cfr_b_censored_releases")
        _same_number(
            row["cfr_b_releases_censored"],
            expected_censored_cfr,
            f"{name} {variant} cfr_b_releases_censored",
        )
        _same_number(
            row["recovery_episodes_censored"],
            canonical[name][variant].get("recovery_episodes_censored"),
            f"{name} {variant} recovery_episodes_censored",
        )

    if {name for name, _ in metric_index} != names:
        raise ValueError("CSV não cobre todos os repositórios do arquivo JSON.")
    for name in names:
        if {(name, variant) for variant in VARIANTS} - set(metric_index):
            raise ValueError(f"{name}: falta variante no CSV.")

    class_index = {}
    for row in classification_rows:
        name = row["repositorio"].strip()
        if name in class_index or name not in names:
            raise ValueError(f"Chave de classificação duplicada ou fora do dataset: {name}.")
        class_index[name] = row
        for variant in VARIANTS:
            metrics_row = metric_index[(name, variant)]
            if row[f"{variant}_categoria"].strip() != metrics_row["categoria_geral"].strip():
                raise ValueError(f"{name} {variant}: categoria geral diverge entre CSVs.")
            if row[f"{variant}_status"].strip() != metrics_row["status_geral"].strip():
                raise ValueError(f"{name} {variant}: status diverge entre CSVs.")
    if set(class_index) != names:
        raise ValueError("rq07_classificacoes.csv não cobre os mesmos repositórios.")

    sample_keys = []
    for line, row in enumerate(gold_sample_rows, start=2):
        repository = row["repositorio"].strip()
        release_id = row["release_id"].strip()
        if not repository or not release_id:
            raise ValueError(f"Amostra-ouro linha {line}: chave vazia.")
        key = (repository, release_id)
        if key in sample_keys:
            raise ValueError(f"Amostra-ouro linha {line}: release duplicada {key}.")
        sample_keys.append(key)
    sample_repositories = {repository for repository, _ in sample_keys}
    if len(sample_repositories) != 60 or len(sample_keys) != 300:
        raise ValueError("A amostra-ouro deve conter 60 repositórios e 300 releases únicas.")
    if not sample_repositories.issubset(names):
        raise ValueError("A amostra-ouro referencia repositório ausente no dataset.")
    per_repository = {
        repository: sum(name == repository for name, _ in sample_keys)
        for repository in sample_repositories
    }
    if set(per_repository.values()) != {5}:
        raise ValueError("A amostra-ouro deve conter exatamente cinco releases por repositório.")

    censored_cfr_total = sum(
        _number(metric_index[(name, "C2")]["cfr_b_releases_censored"], "cfr_b_releases_censored") or 0
        for name in names
    )
    censored_recovery_total = sum(
        _number(metric_index[(name, "C1")]["recovery_episodes_censored"], "recovery_episodes_censored") or 0
        for name in names
    )
    return {
        "status": "validated",
        "repository_count": len(names),
        "metric_rows": len(metrics_rows),
        "classification_rows": len(classification_rows),
        "gold_repository_count": len(sample_repositories),
        "gold_release_count": len(sample_keys),
        "cfr_b_censored_releases": censored_cfr_total,
        "recovery_episodes_censored": censored_recovery_total,
        "coverage": variants_payload["coverage"],
    }


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--classifications", type=Path, required=True)
    parser.add_argument("--variants", type=Path, required=True)
    parser.add_argument("--gold-sample", type=Path, required=True)
    parser.add_argument("--gold-manifest", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        metrics_rows = _read_csv(args.metrics, set(CSV_FIELDS))
        classification_rows = _read_csv(args.classifications, set(CLASSIFICATION_FIELDS))
        gold_rows = _read_csv(args.gold_sample, GOLD_SAMPLE_FIELDS)
        variants_payload = json.loads(args.variants.read_text(encoding="utf-8"))
        gold_manifest = json.loads(args.gold_manifest.read_text(encoding="utf-8"))
        result = validate_exports(
            metrics_rows,
            classification_rows,
            variants_payload,
            gold_rows,
            gold_manifest,
        )
        result["schema_version"] = 1
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        result["artifacts"] = {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in (
                ("metrics", args.metrics),
                ("classifications", args.classifications),
                ("variants", args.variants),
                ("gold_sample", args.gold_sample),
                ("gold_manifest", args.gold_manifest),
            )
        }
        if args.output_manifest.exists():
            raise FileExistsError(f"Não sobrescrever manifesto existente: {args.output_manifest}")
        args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output_manifest.with_suffix(args.output_manifest.suffix + ".tmp")
        temporary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(args.output_manifest)
        print(f"Dataset validado e congelado: {result['repository_count']} repositórios.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Validação do dataset falhou: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
