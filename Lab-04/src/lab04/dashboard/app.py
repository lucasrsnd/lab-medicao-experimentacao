"""Dashboard do Lab04 — Pearson × Spearman (par P5).

Executar no diretório Lab-04:  streamlit run streamlit_app.py

A página só lê artefatos versionados (data/, outputs/, docs/dashboard/); nada
de simulação pesada acontece ao abrir. Toda seção segue o mesmo padrão:
"O que observar" → gráfico → "Conclusão".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lab04.config import (
    ALPHA, DASHBOARD_URL, N_SIMS, PROJECTS_URL, REPO_URL, SEED, SIMULATIONS_PATH, TESTS,
)
from lab04.dashboard import content, interativo, theme
from lab04.plots import g1_dados, g2_nula, g3_erro_tipo1, g4_poder
from lab04.real_data import load_raw
from lab04.simulation.scenarios import get as get_scenario
from lab04.style import TEST_LABELS

OBSERVE, CONCLUSION = "O que observar", "Conclusão"
# (âncora, título, o que falta e em qual issue, quando ainda não disponível)
SECTIONS = (
    ("cenario", "1. Cenário", "parâmetros dos dados reais (#162)"),
    ("dados", "2. Os dados", "G1 (#162, #163)"),
    ("testes", "3. Como os testes funcionam", "G2 (#161, #159)"),
    ("erro-tipo-i", "4. Erro tipo I", "G3 — Sprint 2 (#164, #167)"),
    ("poder", "5. Poder", "G4 — Sprint 2 (#164, #168)"),
    ("dados-reais", "6. Dados reais", "tabela dos testes nos dados reais — entrega final (#171)"),
    ("conclusao", "7. Conclusão", "expectativa × resultado e recomendação — entrega final (#171)"),
)
# Perguntas da apresentação oral → seção que as responde.
QUESTIONS = (
    ("Cenário, H₀ e H₁", "cenario"),
    ("Unicaudal ou bicaudal?", "cenario"),
    ("Coleta e forma dos dados reais", "dados"),
    ("Dados reais → parâmetros", "dados"),
    ("O que cada teste compara", "testes"),
    ("G2: distribuição sob H₀ e rejeição", "testes"),
    ("O que o p-valor (não) significa", "testes"),
    ("Erros tipo I e II no cenário", "cenario"),
    ("G3: liberal ou conservador?", "erro-tipo-i"),
    ("G4: qual teste tem mais poder?", "poder"),
    ("Violação de pressuposto simulada", "poder"),
    ("E com α = 1%?", "erro-tipo-i"),
    ("Simulação × expectativa", "conclusao"),
    ("Dados reais: mesma conclusão?", "dados-reais"),
    ("Recomendação e limitação", "conclusao"),
)
GLOSSARY = (
    ("Correlação latente ρ", "correlação da normal bivariada usada para gerar os dados; é o tamanho do efeito que a simulação controla (ρ = 0 ⇒ H₀ verdadeira)."),
    ("Postos", "posição de cada valor quando ordenados (1 = menor); empates recebem o posto médio."),
    ("g.l.", "graus de liberdade; nos testes de correlação são n − 2 e definem a forma da curva t."),
    ("Região de rejeição", "valores de t tão extremos que levam a rejeitar H₀; somam α = 5% da área, metade em cada cauda."),
    ("p-valor", "probabilidade de um t pelo menos tão extremo quanto o observado se H₀ fosse verdadeira."),
    ("IC 95%", "faixa de valores plausíveis para a correlação, com 95% de confiança."),
    ("Assimetria", "0 = distribuição simétrica; acima de 1 = cauda longa à direita."),
    ("Erro tipo I", "rejeitar H₀ quando ela é verdadeira (falso positivo)."),
    ("Poder", "proporção de vezes em que o teste detecta um efeito que existe."),
)
N_PERMUTATIONS = 5_000


def num(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def chart(fig: go.Figure) -> None:
    # theme=None mantém o tema claro e as cores definidas em lab04.style.
    st.plotly_chart(fig, width="stretch", theme=None)


# ------------------------------------------------------------------ dados
@st.cache_data
def population_size() -> int:
    return len(load_raw())


@st.cache_data
def load_g1_simulated() -> pd.DataFrame | None:
    real = content.real_params()
    return content.g1_simulated(real.params) if real else None


@st.cache_data
def load_permutation_nulls() -> dict[str, np.ndarray] | None:
    ex = content.example()
    if ex is None:
        return None
    sample = content.example_sample(ex, get_scenario("realista").params)
    return {
        test: g2_nula.permutation_null(
            test, sample["loc"].to_numpy(), sample["defects"].to_numpy(),
            n_perm=N_PERMUTATIONS, rng=np.random.default_rng(SEED),
        )
        for test in TESTS
    }


def availability() -> dict[str, bool]:
    """Seções com artefatos prontos: alimenta o progresso da barra lateral."""
    real = content.real_params() is not None
    simulations = SIMULATIONS_PATH.exists()
    return {
        "cenario": real,
        "dados": real and content.real_sample() is not None,
        "testes": content.example() is not None,
        "erro-tipo-i": simulations,
        "poder": simulations,
        "dados-reais": content.section_parts("06-dados-reais") is not None,
        "conclusao": content.section_parts("07-conclusao") is not None,
    }


# ------------------------------------------------------------- blocos de UI
def callout(kind: str, key: str, title: str, parts: dict[str, str] | None) -> None:
    body = (parts or {}).get(title)
    if body is None:
        return
    with st.container(key=f"{kind}-{key}"):
        st.markdown(f"**{title}:** {body}" if kind == "obs" else f"**{title}**\n\n{body}")


def extra_parts(parts: dict[str, str] | None) -> None:
    """Blocos que não são "O que observar"/"Conclusão", lado a lado."""
    extras = [(k, v) for k, v in (parts or {}).items() if k not in (OBSERVE, CONCLUSION)]
    if not extras:
        return
    for col, (title, body) in zip(st.columns(len(extras)), extras):
        with col:
            if title:
                st.markdown(f"**{title}**")
            st.markdown(body)


def pending(key: str, what: str) -> None:
    with st.container(key=f"pend-{key}"):
        st.markdown(f"⏳ **Em construção.** Chega com: {what}.")


def page_header() -> None:
    left, right = st.columns([3, 2], vertical_alignment="center")
    with left:
        st.title("Pearson × Spearman")
        st.caption("Tamanho da classe (LOC) × número de defeitos · Lab04, par P5 · "
                   "Laboratório de Medição e Experimentação em Engenharia de Software")
    with right:
        cols = st.columns(3)
        cols[0].link_button("Repositório", REPO_URL, width="stretch")
        cols[1].link_button("Projects", PROJECTS_URL, width="stretch")
        if DASHBOARD_URL:
            cols[2].link_button("Dashboard", DASHBOARD_URL, width="stretch")
        else:
            cols[2].link_button("Dashboard", REPO_URL, width="stretch", disabled=True,
                                help="Link público adicionado na entrega final (#171).")


def kpi_row(real: content.RealParams | None) -> None:
    if real is None:
        return
    cards = (
        ("Amostra real", str(real.n), f"classes de {thousands(population_size())} · Apache Ant 1.7",
         "Classes Java sorteadas com semente 42 do dataset PROMISE."),
        ("Sem defeito", f"{num(real.observed['prop_zeros'] * 100, 0)}%", "das classes da amostra",
         "Muitos zeros: os defeitos não seguem uma normal."),
        ("Assimetria de LOC", num(real.observed["assimetria_loc"]), "cauda longa à direita",
         "0 = simétrica; acima de 1 = cauda longa à direita."),
        ("Repetições", thousands(N_SIMS), f"por situação · semente {SEED}",
         "Com 10.000 repetições, a margem de erro de uma proporção fica em ±0,4 p.p."),
    )
    for i, (col, card) in enumerate(zip(st.columns(4), cards)):
        with col, st.container(key=f"card-kpi-{i}"):
            theme.kpi(*card)


def summary_row() -> None:
    parts = content.section_parts("00-resumo")
    if not parts:
        return
    for i, (col, (title, body)) in enumerate(zip(st.columns(len(parts)), parts.items())):
        with col, st.container(key=f"card-res-{i}"):
            theme.card_head(title or "Resumo")
            st.markdown(body)


def sidebar(ready: dict[str, bool]) -> None:
    with st.sidebar:
        st.markdown("### LAB04 · P5\nPearson × Spearman")
        st.markdown("**Seções**")
        st.markdown("\n".join(
            f"- {'✓' if ready[key] else '⏳'} [{label}](#{key})"
            for key, label, _ in SECTIONS
        ) + ("\n- ★ [Simulador de poder (bônus)](#simulador)" if ready["poder"] else ""))
        st.caption("✓ pronto · ⏳ em construção")
        with st.expander("Perguntas da apresentação"):
            st.markdown("\n".join(
                f"{i}. [{q}](#{key})" + ("" if ready[key] else " ⏳")
                for i, (q, key) in enumerate(QUESTIONS, start=1)
            ))
        with st.expander("Glossário"):
            st.markdown("\n".join(f"- **{term}:** {text}" for term, text in GLOSSARY))
        st.caption(
            f"Reprodução: semente {SEED} · α = {num(ALPHA * 100, 0)}% bicaudal · "
            f"{thousands(N_SIMS)} repetições · `streamlit run streamlit_app.py`"
        )


# ---------------------------------------------------------------- seções
def section(key: str):
    container = st.container(key=f"card-sec-{key}")
    with container:
        st.header(dict((k, label) for k, label, _ in SECTIONS)[key], anchor=key)
    return container


def section_scenario(real: content.RealParams | None) -> None:
    with section("cenario"):
        extra_parts(content.section_parts("01-cenario"))
        if real is not None:
            st.caption(f"Fonte dos dados reais: {real.source}.")


def section_data(real: content.RealParams | None) -> None:
    with section("dados"):
        sample, simulated = content.real_sample(), load_g1_simulated()
        if sample is None or simulated is None:
            pending("dados", dict((k, w) for k, _, w in SECTIONS)["dados"])
            return
        parts = content.section_parts("02-dados")
        callout("obs", "dados", OBSERVE, parts)
        chart(g1_dados.figure(sample, simulated))
        with st.expander("Parâmetros da simulação estimados dos dados reais"):
            p = real.params
            st.table(pd.DataFrame([
                {"Variável": "LOC", "Distribuição": "Lognormal",
                 "Parâmetros": f"μ = {num(p.loc_mu)} (mediana ≈ {np.exp(p.loc_mu):.0f} linhas), σ = {num(p.loc_sigma)}"},
                {"Variável": "Defeitos", "Distribuição": "Binomial negativa",
                 "Parâmetros": f"média = {num(p.defects_mean)}, dispersão k = {num(p.defects_dispersion)}"},
            ]).set_index("Variável"))
        callout("concl", "dados", CONCLUSION, parts)


def section_tests() -> None:
    with section("testes"):
        ex = content.example()
        if ex is None:
            pending("testes", dict((k, w) for k, _, w in SECTIONS)["testes"])
            return
        parts = content.section_parts("03-testes")
        extra_parts(parts)
        callout("obs", "testes", OBSERVE, parts)
        st.markdown(
            f"Exemplo: **um** conjunto simulado com n = {ex.n}, correlação latente "
            f"ρ = {num(ex.rho, 1)} (H₁ verdadeira) e semente {ex.seed}."
        )
        show_null = st.toggle(
            "Mostrar a distribuição nula por permutação",
            help="Embaralha os dados do exemplo 5.000 vezes e mostra a distribuição real de t sob H₀.",
        )
        nulls = load_permutation_nulls() if show_null else None
        if show_null:
            st.caption("Atenção: com a permutação ligada, os dois gráficos ficam em escalas verticais diferentes.")
        for col, test in zip(st.columns(2), TESTS):
            with col:
                chart(g2_nula.figure(test, ex.n, ex.results[test].statistic,
                                     null_statistics=nulls[test] if nulls else None))
        st.table(pd.DataFrame([
            {
                "Teste": TEST_LABELS[t],
                "Compara": "valores (linear)" if t == "pearson" else "postos (monotônica)",
                "Correlação": num(r.effect, 3),
                "IC 95%": f"[{num(r.ci_low)}; {num(r.ci_high)}]",
                "t": num(r.statistic),
                "p-valor": num(r.p_value, 4),
                "Decisão (α = 5%)": "Rejeita H₀" if r.p_value < ALPHA else "Não rejeita H₀",
            }
            for t, r in ex.results.items()
        ]).set_index("Teste"))
        callout("concl", "testes", CONCLUSION, parts)


def section_type1(sims: pd.DataFrame | None) -> None:
    with section("erro-tipo-i"):
        if sims is None:
            pending("erro-tipo-i", dict((k, w) for k, _, w in SECTIONS)["erro-tipo-i"])
            return
        parts = content.section_parts("04-erro-tipo1")
        callout("obs", "erro-tipo-i", OBSERVE, parts)
        chart(g3_erro_tipo1.figure(sims))
        verdicts = g3_erro_tipo1.classify(sims)
        st.table(
            verdicts.assign(
                Teste=verdicts["test"].map(TEST_LABELS),
                Taxa=(verdicts["rate"] * 100).map(lambda v: f"{num(v, 1)}%"),
                IC=[f"[{num(lo * 100, 1)}%; {num(hi * 100, 1)}%]"
                    for lo, hi in zip(verdicts["ci_low"], verdicts["ci_high"])],
                Veredicto=verdicts["verdict"].map(g3_erro_tipo1.VERDICT_LABELS),
            )
            .rename(columns={"label": "Situação"})
            .set_index(["Situação", "Teste"])[["Taxa", "IC", "Veredicto"]]
            .rename(columns={"IC": "IC 95%"})
        )
        violations = content.section_parts("q3-violacoes")
        if violations:
            with st.expander("Como as violações de pressuposto foram simuladas (Q3)"):
                for title, body in violations.items():
                    if title:
                        st.markdown(f"**{title}**")
                    st.markdown(body)
        callout("concl", "erro-tipo-i", CONCLUSION, parts)


def section_power(sims: pd.DataFrame | None) -> None:
    with section("poder"):
        if sims is None:
            pending("poder", dict((k, w) for k, _, w in SECTIONS)["poder"])
            return
        parts = content.section_parts("05-poder")
        callout("obs", "poder", OBSERVE, parts)
        chart(g4_poder.figure(sims))
        with st.expander("Ver as taxas de rejeição em tabela"):
            table = sims.assign(Teste=sims["test"].map(TEST_LABELS)).pivot_table(
                index=["label", "effect"], columns="Teste", values="rate", sort=False,
            )
            table.index.names = ["Situação", "ρ latente"]
            st.dataframe(table.style.format(lambda v: f"{num(v * 100, 1)}%"), width="stretch")
        callout("concl", "poder", CONCLUSION, parts)
        with st.container(key="sim-box"):
            st.subheader("Experimente: simulador de poder (bônus)", anchor="simulador")
            st.markdown(
                "Escolha a situação, o tamanho da amostra e o tamanho do efeito e veja o poder dos "
                "dois testes mudar. Teste, por exemplo, **quantas classes seriam necessárias para "
                "chegar a 80%**."
            )
            interativo.render()


def section_pending(key: str, what: str) -> None:
    with section(key):
        pending(key, what)


def main() -> None:
    st.set_page_config(page_title="Lab04 — Pearson × Spearman", page_icon="📊", layout="wide")
    theme.inject()
    ready = availability()
    sidebar(ready)

    real = content.real_params()
    page_header()
    kpi_row(real)
    summary_row()
    section_scenario(real)
    section_data(real)
    section_tests()
    sims = content.simulations()
    section_type1(sims)
    section_power(sims)
    for key, _, what in SECTIONS[5:]:
        section_pending(key, what)


# Rodado direto (streamlit run .../app.py); no deploy, streamlit_app.py chama main().
if __name__ == "__main__":
    main()
