"""Testes do coletor (S01-04, #184). Rodar a partir de Lab-05:  pytest"""

from __future__ import annotations

import json
import threading
from collections import Counter
from http.server import ThreadingHTTPServer

import pandas as pd
import pytest

import coleta
import servidor_local


@pytest.fixture(scope="module")
def servidor():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor_local.Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def _alvos(base: str, unidades=("p01", "p02", "p03")) -> coleta.Alvos:
    return coleta.Alvos(nome="teste", software={"nome": "local"},
                        tratamentos={"A": f"{base}/a/{{unidade}}", "B": f"{base}/b/{{unidade}}"},
                        unidades=list(unidades), timeout_s=5)


def test_ler_alvos_valida_config(tmp_path):
    cfg = {"nome": "x", "tratamentos": {"A": "http://h/{unidade}", "B": "http://h/b"}, "unidades": ["u"]}
    caminho = tmp_path / "alvos.json"
    caminho.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(ValueError, match="unidade"):
        coleta.Alvos.ler(caminho)


def test_intervalo_minimo_para_host_externo():
    externo = _alvos("https://exemplo.org")
    local = _alvos("http://127.0.0.1:1")
    assert coleta.intervalo_efetivo(externo, 0.1) == 1.0
    assert coleta.intervalo_efetivo(local, 0.1) == 0.1


def test_plano_balanceado_e_reprodutivel():
    alvos = _alvos("http://127.0.0.1:1")
    plano = coleta.plano_execucao(alvos, repeticoes=4, aquecimento=2, semente=7)
    assert plano == coleta.plano_execucao(alvos, repeticoes=4, aquecimento=2, semente=7)
    medicao = [p for p in plano if p[0] == "medicao"]
    assert len(medicao) == 2 * 3 * 4
    assert len(set(medicao)) == len(medicao)
    assert Counter(p[1] for p in plano if p[0] == "aquecimento") == {"A": 2, "B": 2}
    # Ordem aleatória: o tratamento A não vem sempre primeiro dentro da unidade.
    primeiros = {medicao[i][1] for i in range(0, len(medicao), 2)}
    assert primeiros == {"A", "B"}


def test_aquecer_unidades_cobre_todas():
    alvos = _alvos("http://127.0.0.1:1")
    plano = coleta.plano_execucao(alvos, repeticoes=1, aquecimento=1, semente=7, aquecer_unidades=True)
    aquec = {(p[1], p[2]) for p in plano if p[0] == "aquecimento"}
    assert aquec == {(t, u) for t in ("A", "B") for u in alvos.unidades}


def test_robots_bloqueia_url_externa():
    class Resp:
        status_code = 200
        text = "User-agent: *\nDisallow: /privado/\n"

    class Sessao:
        def get(self, url, timeout):
            return Resp()

    coleta._robots_cache.clear()
    alvos = coleta.Alvos(nome="x", software={}, unidades=["u"],
                         tratamentos={"A": "https://ex.org/publico/{unidade}", "B": "https://ex.org/privado/{unidade}"})
    permitido = coleta.verificar_robots(alvos, Sessao())
    assert permitido == {"https://ex.org/publico/u": True, "https://ex.org/privado/u": False}


def test_coleta_ponta_a_ponta(servidor, tmp_path):
    alvos = _alvos(servidor)
    csv, meta = coleta.coletar(alvos, repeticoes=2, aquecimento=1, semente=1, intervalo_s=0,
                               saida=tmp_path, dormir=lambda s: None)
    df = pd.read_csv(csv)
    assert list(df.columns) == list(coleta.COLUNAS)
    assert set(df["metrica"]) == set(coleta.METRICAS)
    assert len(df) == 2 * 3 * 2 * len(coleta.METRICAS)
    assert (df["valor"] > 0).all()
    v = meta["validacao"]
    assert v["completude"] == 1 and v["nulos"] == 0 and v["duplicatas"] == 0
    log = [json.loads(l) for l in open(str(csv).replace(".csv", ".log.jsonl"), encoding="utf-8")]
    assert len(log) == meta["requisicoes"] == 2 + 12
    assert sum(r["fase"] == "aquecimento" for r in log) == 2
    # Mesma página nos dois tratamentos: tamanho igual por unidade.
    tam = df[df["metrica"] == "tamanho_kb"].pivot_table(index="unidade", columns="tratamento", values="valor")
    assert (tam["A"] == tam["B"]).all()


def test_falha_nao_vira_observacao(servidor, tmp_path):
    alvos = _alvos(servidor)
    alvos.tratamentos["B"] = f"{servidor}/inexistente/x/{{unidade}}"  # 404
    csv, meta = coleta.coletar(alvos, repeticoes=1, aquecimento=0, semente=1, intervalo_s=0,
                               saida=tmp_path, dormir=lambda s: None)
    df = pd.read_csv(csv)
    assert set(df["tratamento"]) == {"A"}
    assert meta["falhas_medicao"] == 3
    assert meta["validacao"]["completude"] == 0.5


def test_validar_detecta_duplicatas_e_negativos():
    alvos = _alvos("http://127.0.0.1:1", unidades=("u",))
    df = pd.DataFrame([("A", "u", 1, "tempo_ms", 10.0), ("A", "u", 1, "tempo_ms", 11.0),
                       ("B", "u", 1, "tempo_ms", -1.0)], columns=list(coleta.COLUNAS))
    v = coleta.validar(df, alvos, repeticoes=1)
    assert v["duplicatas"] == 1 and v["negativos"] == 1


def test_estimativa():
    assert coleta.estimar_duracao_s(100, 1.0, 300) == 100
    assert coleta.estimar_duracao_s(100, 1.0, 2000) == 200
