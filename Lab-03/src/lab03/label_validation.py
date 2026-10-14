"""Valida as planilhas de rótulos de um avaliador da amostra-ouro.

    python -m lab03.label_validation --rater B
    python -m lab03.label_validation --rater B --complete-ids
    python -m lab03.label_validation --rater B --allow-blank   # durante a rotulagem

Lê só o sorteio (`amostra_ouro_releases.csv`) e as planilhas do avaliador
informado. Nunca abre rótulos de outros avaliadores nem a saída da heurística,
para não quebrar o protocolo cego. Verifica:

- as linhas cobrem exatamente os repositórios e releases sorteados, sem
  repetição;
- os valores das três dimensões estão no vocabulário do protocolo
  (`tipo_projeto`, `releases_sao_entregas`, `e_corretiva`);
- casos ambíguos (`incerto`, `outro`) têm justificativa em `observacoes`.

`--complete-ids` preenche a coluna `release_id` a partir do sorteio (por
repositório e tag) sem alterar nenhum rótulo.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_TYPES = frozenset({"biblioteca/framework", "aplicacao/servico", "ferramenta CLI", "outro"})
DELIVERIES = frozenset({"sim", "nao", "incerto"})
CORRECTIVE = frozenset({"sim", "nao"})
NEEDS_JUSTIFICATION = {"tipo_projeto": {"outro"}, "releases_sao_entregas": {"incerto"}}


def _read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _check_value(errors, where, field, value, allowed, allow_blank):
    if value == "":
        if not allow_blank:
            errors.append(f"{where}: {field} vazio")
    elif value not in allowed:
        errors.append(f"{where}: {field}={value!r} fora de {sorted(allowed)}")


def validate(labels: Path, rater: str, *, allow_blank: bool = False) -> dict:
    _, draw = _read(labels / "amostra_ouro_releases.csv")
    _, repositories = _read(labels / f"rotulos_{rater}_repositorios.csv")
    _, releases = _read(labels / f"rotulos_{rater}_releases.csv")
    errors: list[str] = []

    # Repositório sem release rotulável é sorteado mesmo assim (só a dimensão
    # de repositório): o total vem do manifesto, não das releases.
    expected_total = json.loads(
        (labels / "amostra_ouro_sorteio.json").read_text(encoding="utf-8")
    )["repositories"]
    seen = [row.get("repositorio", "") for row in repositories]
    missing = sorted({row["repositorio"] for row in draw} - set(seen))
    repeated = sorted({name for name in seen if seen.count(name) > 1})
    if missing or repeated or len(seen) != expected_total:
        errors.append(
            f"repositórios divergem do sorteio: {len(seen)} de {expected_total}, "
            f"faltam {missing}, repetidos {repeated}"
        )
    for row in repositories:
        where = row.get("repositorio", "?")
        _check_value(errors, where, "tipo_projeto", row.get("tipo_projeto", "").strip(),
                     PROJECT_TYPES, allow_blank)
        _check_value(errors, where, "releases_sao_entregas",
                     row.get("releases_sao_entregas", "").strip(), DELIVERIES, allow_blank)
        for field, ambiguous in NEEDS_JUSTIFICATION.items():
            if row.get(field, "").strip() in ambiguous and not row.get("observacoes", "").strip():
                errors.append(f"{where}: {field}={row[field].strip()} exige justificativa em observacoes")

    ids = {(row["repositorio"], row["tag"]): row["release_id"] for row in draw}
    keys = [(row.get("repositorio", ""), row.get("tag", "")) for row in releases]
    if sorted(keys) != sorted(ids):
        missing = sorted(set(ids) - set(keys))
        extra = sorted(set(keys) - set(ids))
        repeated = sorted({key for key in keys if keys.count(key) > 1})
        errors.append(f"releases divergem do sorteio: faltam {missing[:5]}, sobram {extra[:5]}, repetidas {repeated[:5]}")
    for row in releases:
        key = (row.get("repositorio", ""), row.get("tag", ""))
        where = f"{key[0]}@{key[1]}"
        _check_value(errors, where, "e_corretiva", row.get("e_corretiva", "").strip(),
                     CORRECTIVE, allow_blank)
        if row.get("release_id") and key in ids and row["release_id"] != ids[key]:
            errors.append(f"{where}: release_id {row['release_id']} difere do sorteio {ids[key]}")

    def filled(rows, fields):
        return sum(all(row.get(f, "").strip() for f in fields) for row in rows)

    return {
        "rater": rater,
        "errors": errors,
        "repositories": len(repositories),
        "repositories_labeled": filled(repositories, ("tipo_projeto", "releases_sao_entregas")),
        "releases": len(releases),
        "releases_labeled": filled(releases, ("e_corretiva",)),
        "ambiguous_with_notes": sum(
            bool(row.get("observacoes", "").strip()) for row in repositories + releases
        ),
    }


def complete_ids(labels: Path, rater: str) -> int:
    """Acrescenta/preenche `release_id` (após `tag`), mantendo os rótulos."""
    _, draw = _read(labels / "amostra_ouro_releases.csv")
    ids = {(row["repositorio"], row["tag"]): row["release_id"] for row in draw}
    path = labels / f"rotulos_{rater}_releases.csv"
    fields, rows = _read(path)
    if "release_id" not in fields:
        fields.insert(fields.index("tag") + 1, "release_id")
    changed = 0
    for row in rows:
        key = (row["repositorio"], row["tag"])
        if key not in ids:
            raise ValueError(f"Release fora do sorteio: {key}")
        if row.get("release_id") != ids[key]:
            row["release_id"] = ids[key]
            changed += 1
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rater", required=True, choices=("A", "B", "C"))
    parser.add_argument("--labels", type=Path, default=Path("labels"))
    parser.add_argument("--allow-blank", action="store_true",
                        help="aceitar rótulos ainda vazios (acompanhar o progresso)")
    parser.add_argument("--complete-ids", action="store_true",
                        help="preencher release_id a partir do sorteio antes de validar")
    args = parser.parse_args(argv)
    try:
        if args.complete_ids:
            print(f"release_id preenchido em {complete_ids(args.labels, args.rater)} linhas.")
        report = validate(args.labels, args.rater, allow_blank=args.allow_blank)
    except (OSError, KeyError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(f"Avaliador {report['rater']}: repositórios {report['repositories_labeled']}/"
          f"{report['repositories']}, releases {report['releases_labeled']}/{report['releases']}, "
          f"linhas com observação {report['ambiguous_with_notes']}.")
    for error in report["errors"]:
        print(f"- {error}", file=sys.stderr)
    if report["errors"]:
        print(f"{len(report['errors'])} problema(s).", file=sys.stderr)
        return 1
    print("Formato válido." if not args.allow_blank else "Sem erros de formato até aqui.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
