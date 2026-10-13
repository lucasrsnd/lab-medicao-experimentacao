"""Heurística automática de release corretiva (RQ03 b) e CFR de entrega.

Uma release é marcada como corretiva por sinais observáveis, sem julgamento
humano:

- ``patch_only_semver``: a versão muda só no número de *patch* em relação à
  release anterior (``2.3.0 -> 2.3.1``);
- ``commit_keyword``: alguma mensagem de commit entre as duas releases cita
  ``revert``, ``hotfix`` ou ``fix`` (na primeira linha da mensagem).

Versões (cada uma deve ser documentada com o F1 obtido na amostra-ouro):

- ``v1``: marca a release se **qualquer** commit citar a palavra-chave (o
  "e/ou" literal do enunciado). Em teste real (``cli/cli``, 27 releases) marcou
  27/27 como corretivas: "fix" aparece em quase todo lote de commits. Mantida
  só como linha de base.
- ``v2`` (padrão): a palavra-chave só conta quando pelo menos
  ``KEYWORD_COMMIT_SHARE`` (50%) dos commits da release a citam, isto é, quando
  correções são o conteúdo principal da release.
"""

import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Iterable, Sequence

from lab03.domain import ReleaseChanges, Window

HEURISTIC_VERSION = "v2"
KEYWORD_COMMIT_SHARE = 0.5
FOLLOW_UP_DAYS = 7

_SEMVER = re.compile(r"(?<![0-9A-Za-z])[vV]?(\d+)\.(\d+)\.(\d+)(?![0-9])")
_KEYWORD = re.compile(r"\b(?:revert|hotfix|fix(?:e[sd])?)\b", re.IGNORECASE)


def parse_semver(tag: str) -> tuple[int, int, int] | None:
    """Extrai MAJOR.MINOR.PATCH do nome da tag; None se não houver versão."""
    match = _SEMVER.search(tag)
    return tuple(int(part) for part in match.groups()) if match else None


def is_patch_only_bump(previous_tag: str | None, tag: str) -> bool:
    if previous_tag is None:
        return False
    before, after = parse_semver(previous_tag), parse_semver(tag)
    if before is None or after is None:
        return False
    return after[:2] == before[:2] and after[2] > before[2]


def fix_commit_share(messages: Iterable[str]) -> float:
    """Fração de commits cujo assunto cita revert/hotfix/fix."""
    subjects = [m.strip().split("\n", 1)[0] for m in messages]
    if not subjects:
        return 0.0
    return sum(bool(_KEYWORD.search(subject)) for subject in subjects) / len(subjects)


def has_fix_keyword(messages: Iterable[str]) -> bool:
    return fix_commit_share(messages) > 0


@dataclass(frozen=True)
class CorrectiveVerdict:
    tag: str
    corrective: bool
    reasons: tuple[str, ...]
    commits_available: bool


def classify_release(
    change: ReleaseChanges, version: str = HEURISTIC_VERSION,
) -> CorrectiveVerdict:
    """Classifica uma release usando a antecessora e os commits entre as duas.

    Sem commits (compare excluído, release sem antecessora), só o sinal de
    versão pode disparar; `commits_available=False` registra a limitação.
    """
    if version not in ("v1", "v2"):
        raise ValueError(f"Versão de heurística desconhecida: {version}")
    reasons = []
    previous_tag = change.previous.tag if change.previous else None
    if is_patch_only_bump(previous_tag, change.release.tag):
        reasons.append("patch_only_semver")
    commits_available = change.exclusion is None and bool(change.commits)
    if commits_available:
        share = fix_commit_share(c.message for c in change.commits)
        if version == "v1" and share > 0:
            reasons.append("commit_keyword")
        elif version == "v2" and share >= KEYWORD_COMMIT_SHARE:
            reasons.append("commit_keyword")

    return CorrectiveVerdict(
        change.release.tag, bool(reasons), tuple(reasons), commits_available,
    )


@dataclass(frozen=True)
class DeliveryFailureResult:
    """CFR (b). `rate` é None quando nenhuma release pôde ser avaliada."""
    rate: float | None
    failed: int
    evaluated: int
    censored: int
    releases_total: int
    corrective_total: int
    failed_tags: tuple[str, ...] = ()
    verdicts: tuple[CorrectiveVerdict, ...] = field(default=(), repr=False)
    heuristic_version: str = HEURISTIC_VERSION


def calculate_delivery_failure_rate(
    changes: Sequence[ReleaseChanges],
    window: Window,
    *,
    follow_up_days: int = FOLLOW_UP_DAYS,
    version: str = HEURISTIC_VERSION,
) -> DeliveryFailureResult:
    """Release R falha se alguma release corretiva for publicada em (R, R+7d].

    Releases com menos de 7 dias de acompanhamento até o fim da janela são
    censuradas e ficam fora do denominador. `changes` contém só releases
    publicadas (não pré-releases) da janela, como produzido por
    `collect_changes`.
    """
    ordered = sorted(changes, key=lambda c: (c.release.published_at, c.release.id))
    verdicts = [classify_release(change, version) for change in ordered]
    follow_up = timedelta(days=follow_up_days)
    failed_tags = []
    evaluated = censored = 0
    for index, change in enumerate(ordered):
        published = change.release.published_at
        if published + follow_up > window.end:
            censored += 1
            continue
        evaluated += 1
        deadline = published + follow_up
        for later, verdict in zip(ordered[index + 1:], verdicts[index + 1:]):
            if later.release.published_at > deadline:
                break
            if verdict.corrective and later.release.published_at > published:
                failed_tags.append(change.release.tag)
                break
    return DeliveryFailureResult(
        rate=len(failed_tags) / evaluated if evaluated else None,
        failed=len(failed_tags),
        evaluated=evaluated,
        censored=censored,
        releases_total=len(ordered),
        corrective_total=sum(v.corrective for v in verdicts),
        failed_tags=tuple(failed_tags),
        verdicts=tuple(verdicts),
        heuristic_version=version,
    )
