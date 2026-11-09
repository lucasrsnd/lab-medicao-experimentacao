import re

from lab04.config import LAB_ROOT

ROTEIRO = (LAB_ROOT / "docs" / "roteiro-apresentacao.md").read_text(encoding="utf-8")
QUESTIONS = re.findall(r"^### (\d+)\. .* — (\w+)$", ROTEIRO, re.M)


def test_all_15_questions_in_order_with_one_presenter():
    assert [int(n) for n, _ in QUESTIONS] == list(range(1, 16))


def test_each_member_answers_at_least_four():
    counts = {}
    for _, member in QUESTIONS:
        counts[member] = counts.get(member, 0) + 1
    assert set(counts) == {"Gustavo", "Lucas", "Davi"}
    assert min(counts.values()) >= 4


def test_every_answer_points_to_the_dashboard():
    blocks = re.split(r"^### \d+\. ", ROTEIRO, flags=re.M)[1:]
    assert all("**Mostrar:**" in block for block in blocks)
