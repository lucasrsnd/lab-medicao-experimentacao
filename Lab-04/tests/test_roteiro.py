import re

from lab04.config import DASHBOARD_URL, LAB_ROOT

ROTEIRO = (LAB_ROOT / "docs" / "roteiro-apresentacao.md").read_text(encoding="utf-8")
MEMBERS = {"Gustavo", "Lucas", "Davi"}


def section(title: str) -> str:
    start = ROTEIRO.index(f"## {title}")
    end = ROTEIRO.find("\n## ", start + 1)
    return ROTEIRO[start:end if end != -1 else None]


# | # | Quem | Pergunta | Navegar para | Tempo | Passa para |
ORDER = [
    (int(n), who, to)
    for n, who, to in re.findall(r"^\| (\d+) \| (\w+) \|.*\| (\w+|—) \|$", section("Ordem da apresentação"), re.M)
]


def cards() -> dict[int, str]:
    owners = {}
    for block in re.split(r"^### ", section("Cartão de cada integrante"), flags=re.M)[1:]:
        owner = block.split(" ", 1)[0]
        for n in re.findall(r"^#### P(\d+) · ", block, re.M):
            owners[int(n)] = owner
    return owners


def test_order_covers_15_questions_in_sequence():
    assert [n for n, _, _ in ORDER] == list(range(1, 16))
    assert {who for _, who, _ in ORDER} == MEMBERS


def test_handoff_matches_next_presenter():
    for (_, _, to), (_, next_who, _) in zip(ORDER, ORDER[1:]):
        assert to == next_who
    assert ORDER[-1][2] == "—"


def test_each_member_has_a_card_with_their_questions():
    owners = cards()
    assert owners == {n: who for n, who, _ in ORDER}
    for member in MEMBERS:
        assert list(owners.values()).count(member) >= 4  # regra do enunciado


def test_every_answer_points_to_the_dashboard():
    blocks = re.split(r"^#### P\d+ · ", section("Cartão de cada integrante"), flags=re.M)[1:]
    assert len(blocks) == 15 and all("**Mostrar:**" in b for b in blocks)


def test_cheat_sheet_covers_all_questions():
    rows = re.findall(r"^\| (\d+) \| ", section("Cola: uma linha por pergunta"), re.M)
    assert [int(n) for n in rows] == list(range(1, 16))


def test_links_to_published_dashboard():
    assert DASHBOARD_URL in ROTEIRO
