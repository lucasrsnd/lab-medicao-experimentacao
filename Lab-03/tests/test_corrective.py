"""Heurística corretiva e CFR (b) com os exemplos numéricos da RQ03."""
from datetime import datetime, timedelta, timezone

import pytest

from lab03.domain import Commit, Release, ReleaseChanges, Window
from lab03.metrics import calculate_delivery_failure_rate, classify_release
from lab03.metrics.corrective import has_fix_keyword, is_patch_only_bump, parse_semver

START = datetime(2025, 1, 1, tzinfo=timezone.utc)
WINDOW = Window(START, datetime(2026, 1, 1, tzinfo=timezone.utc))
_ids = iter(range(1, 10_000))


def release(tag, when):
    return Release(next(_ids), tag, "sha-" + tag, when, False, "", f"https://x/{tag}")


def change(tag, when, previous=None, messages=(), exclusion=None):
    commits = tuple(Commit(f"c{next(_ids)}", when, m) for m in messages)
    return ReleaseChanges(release(tag, when), previous, commits, exclusion)


def day(month, d):
    return datetime(2025, month, d, tzinfo=timezone.utc)


def test_semver_extrai_versao_com_ou_sem_prefixo():
    assert parse_semver("v2.3.1") == (2, 3, 1)
    assert parse_semver("release-1.0.12") == (1, 0, 12)
    assert parse_semver("nightly") is None


@pytest.mark.parametrize("before,after,expected", [
    ("2.3.0", "2.3.1", True),
    ("v2.3.0", "v2.3.4", True),
    ("2.3.1", "2.4.0", False),
    ("2.3.1", "3.3.2", False),
    ("2.3.1", "2.3.1", False),
    ("2.3.1", "2.3.0", False),
    ("latest", "2.3.1", False),
    (None, "2.3.1", False),
])
def test_patch_only_bump(before, after, expected):
    assert is_patch_only_bump(before, after) is expected


def test_palavras_chave_na_primeira_linha():
    assert has_fix_keyword(["fix: crash ao abrir arquivo"])
    assert has_fix_keyword(["Revert \"add feature\""])
    assert has_fix_keyword(["HOTFIX login"])
    assert has_fix_keyword(["Fixes #12"])
    assert not has_fix_keyword(["feat: prefix handling", "docs: suffix"])
    assert not has_fix_keyword(["feat: nova opção\n\nfix mencionado só no corpo"])


def test_classifica_patch_do_exemplo_do_enunciado():
    previous = release("v2.3.0", day(5, 10))
    verdict = classify_release(
        change("v2.3.1", day(5, 12), previous, ["fix: crash ao abrir arquivo"])
    )
    assert verdict.corrective
    assert verdict.reasons == ("patch_only_semver", "commit_keyword")


def test_minor_sem_palavra_chave_nao_e_corretiva():
    previous = release("v2.4.0", day(6, 1))
    verdict = classify_release(change("v2.5.0", day(6, 20), previous, ["feat: x"]))
    assert not verdict.corrective and verdict.reasons == ()


def test_sem_commits_so_a_versao_pode_disparar():
    previous = release("1.0.0", day(3, 1))
    verdict = classify_release(
        change("1.0.1", day(3, 2), previous, exclusion="compare_not_found")
    )
    assert verdict.corrective and not verdict.commits_available


def test_primeira_release_sem_antecessora_nao_e_corretiva():
    assert not classify_release(change("v1.0.1", day(2, 1), None,
                                       exclusion="no_previous_release")).corrective


def _chain(*specs):
    """specs: (tag, data, [mensagens]); a antecessora é a spec anterior."""
    result, previous = [], None
    for tag, when, messages in specs:
        item = change(tag, when, previous, messages)
        result.append(item)
        previous = item.release
    return result


def test_cfr_b_exemplo_do_enunciado():
    changes = _chain(
        ("v2.3.0", day(5, 10), ["feat: a"]),
        ("v2.3.1", day(5, 12), ["fix: crash ao abrir arquivo"]),
        ("v2.4.0", day(6, 1), ["feat: b"]),
        ("v2.5.0", day(6, 20), ["feat: c"]),
    )
    result = calculate_delivery_failure_rate(changes, WINDOW)
    assert result.failed_tags == ("v2.3.0",)
    # v2.3.0, v2.3.1, v2.4.0, v2.5.0 avaliáveis; só v2.3.0 falhou.
    assert (result.failed, result.evaluated, result.censored) == (1, 4, 0)
    assert result.rate == pytest.approx(0.25)
    assert result.corrective_total == 1


def test_corretiva_depois_de_mais_de_7_dias_nao_conta():
    changes = _chain(
        ("v1.0.0", day(5, 1), ["feat: a"]),
        ("v1.0.1", day(5, 9), ["fix: b"]),
    )
    assert calculate_delivery_failure_rate(changes, WINDOW).failed == 0


def test_limite_de_7_dias_e_inclusivo():
    changes = _chain(
        ("v1.0.0", day(5, 1), ["feat: a"]),
        ("v1.0.1", day(5, 8), ["fix: b"]),
    )
    assert calculate_delivery_failure_rate(changes, WINDOW).failed_tags == ("v1.0.0",)


def test_alguma_corretiva_dentro_de_7_dias_basta_mesmo_nao_sendo_a_proxima():
    changes = _chain(
        ("v1.0.0", day(5, 1), ["feat: a"]),
        ("v1.1.0", day(5, 2), ["feat: b"]),
        ("v1.1.1", day(5, 4), ["fix: c"]),
    )
    result = calculate_delivery_failure_rate(changes, WINDOW)
    assert result.failed_tags == ("v1.0.0", "v1.1.0")


def test_releases_nos_ultimos_7_dias_sao_censuradas():
    late = datetime(2025, 12, 28, tzinfo=timezone.utc)
    changes = _chain(
        ("v3.0.0", day(11, 1), ["feat: a"]),
        ("v3.1.0", late, ["feat: b"]),
        ("v3.1.1", late + timedelta(days=1), ["fix: c"]),
    )
    result = calculate_delivery_failure_rate(changes, WINDOW)
    assert (result.evaluated, result.censored, result.failed) == (1, 2, 0)


def test_instante_exato_de_7_dias_antes_do_fim_e_avaliavel():
    boundary = WINDOW.end - timedelta(days=7)
    result = calculate_delivery_failure_rate(
        _chain(("v1.0.0", boundary, ["feat: a"])), WINDOW)
    assert (result.evaluated, result.censored) == (1, 0)


def test_uma_unica_release_nao_falha():
    result = calculate_delivery_failure_rate(
        _chain(("v1.0.0", day(5, 1), ["fix: a"])), WINDOW)
    assert (result.failed, result.evaluated, result.rate) == (0, 1, 0.0)


def test_sem_releases_avaliaveis_rate_e_none_nao_zero():
    assert calculate_delivery_failure_rate([], WINDOW).rate is None
    only_late = _chain(("v1.0.0", WINDOW.end - timedelta(days=1), ["feat: a"]))
    result = calculate_delivery_failure_rate(only_late, WINDOW)
    assert result.rate is None and result.censored == 1


def test_ordena_por_data_de_publicacao():
    changes = _chain(
        ("v1.0.0", day(5, 1), ["feat: a"]),
        ("v1.0.1", day(5, 3), ["fix: b"]),
    )
    result = calculate_delivery_failure_rate(list(reversed(changes)), WINDOW)
    assert result.failed_tags == ("v1.0.0",)


def test_v1_marca_com_uma_palavra_chave_e_v2_exige_maioria_de_commits():
    previous = release("v2.4.0", day(6, 1))
    mixed = change("v2.5.0", day(6, 20), previous,
                   ["feat: a", "feat: b", "feat: c", "fix: d"])
    assert classify_release(mixed, "v1").corrective
    assert not classify_release(mixed, "v2").corrective
    mostly_fixes = change("v2.5.0", day(6, 20), previous, ["fix: a", "fix: b", "feat: c"])
    assert classify_release(mostly_fixes, "v2").reasons == ("commit_keyword",)


def test_versao_desconhecida_falha():
    with pytest.raises(ValueError):
        classify_release(change("v1.0.0", day(5, 1)), "v9")


def test_resultado_registra_a_versao_usada():
    changes = _chain(("v1.0.0", day(5, 1), ["fix: a"]), ("v1.0.1", day(5, 2), ["fix: b"]))
    assert calculate_delivery_failure_rate(changes, WINDOW, version="v1").heuristic_version == "v1"
    assert calculate_delivery_failure_rate(changes, WINDOW).heuristic_version == "v2"
