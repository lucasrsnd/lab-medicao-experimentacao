"""#136: a verificação de entrega acusa segredos, caminhos pessoais e arquivos faltando."""

from lab03 import delivery


def test_detecta_token_e_caminho_pessoal(tmp_path):
    (tmp_path / "a.md").write_text("token ghp_" + "a" * 36, encoding="utf-8")
    (tmp_path / "b.md").write_text("cache em " + "C:" + "\\" + "Users" + "\\" + "Alguem" + "\\" + "x", encoding="utf-8")
    (tmp_path / "c.md").write_text("tudo limpo", encoding="utf-8")
    assert delivery.scan(tmp_path) == ["possível token em a.md", "caminho pessoal em b.md"]


def test_ignora_binarios_e_pastas_de_ambiente(tmp_path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "x.py").write_text("/ho" + "me/alguem/", encoding="utf-8")
    (tmp_path / "dados.gz").write_bytes(b"/ho" + b"me/alguem/x")
    assert delivery.scan(tmp_path) == []


def test_aponta_arquivo_obrigatorio_ausente_e_env_presente(tmp_path):
    (tmp_path / ".env").write_text("GITHUB_TOKEN=x", encoding="utf-8")
    problems = delivery.check(tmp_path)
    assert "ausente: README.md" in problems
    assert any(".env presente" in problem for problem in problems)


def test_entrega_do_repositorio_esta_limpa():
    from pathlib import Path

    assert delivery.scan(Path(__file__).parents[1]) == []
