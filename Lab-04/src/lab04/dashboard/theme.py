"""Aparência do dashboard: cartões brancos sobre fundo tingido e cabeçalhos escuros.

As cores de página e da barra lateral ficam em ``.streamlit/config.toml``; aqui só
o que o tema do Streamlit não cobre. Os elementos são localizados pela classe
``st-key-<key>`` que o Streamlit dá a containers com ``key``:

- ``card-*``      cartão branco (indicadores, resumo, seções)
- ``card-sec-*``  cartão de seção; o ``st.header`` vira a faixa escura do topo
- ``obs-*``       chamada "O que observar" (antes do gráfico)
- ``concl-*``     chamada "Conclusão" (depois do gráfico)
- ``pend-*``      aviso de seção que chega numa próxima entrega
"""

from html import escape

import streamlit as st

HEAD = "#2B2D3A"
INK = "#1F2430"
MUTED = "#5B6270"

CSS = f"""
<style>
[class*="st-key-card-"] {{
  background: #FFFFFF; border: 1px solid #D9E0DE; border-radius: 12px;
  padding: 1rem 1.25rem 1.25rem; box-shadow: 0 1px 3px rgba(31, 36, 48, .08);
}}
[class*="st-key-card-sec-"] h2 {{
  background: {HEAD}; color: #FFFFFF; font-size: 1rem; font-weight: 600;
  letter-spacing: .06em; text-transform: uppercase; padding: .6rem .9rem;
  border-radius: 8px; margin: 0 0 .25rem 0;
}}
[class*="st-key-card-sec-"] h2 a {{ display: none; }}
.card-head {{
  background: {HEAD}; color: #FFFFFF; font-size: .78rem; font-weight: 600;
  letter-spacing: .08em; text-transform: uppercase; padding: .45rem .75rem;
  border-radius: 8px; margin-bottom: .6rem;
}}
.kpi-value {{ font-size: 2.1rem; font-weight: 700; color: {INK}; line-height: 1.15; }}
.kpi-note {{ font-size: .9rem; color: {MUTED}; }}
[class*="st-key-obs-"] {{
  border-left: 4px solid #8A94A6; background: #F4F6F8;
  padding: .6rem .9rem; border-radius: 0 8px 8px 0;
}}
[class*="st-key-concl-"] {{
  border-left: 4px solid {HEAD}; background: #EEF2F1;
  padding: .75rem 1rem; border-radius: 0 8px 8px 0;
}}
[class*="st-key-pend-"] {{
  color: {MUTED}; background: #F4F6F8; border: 1px dashed #B8C0CC;
  border-radius: 8px; padding: .8rem 1rem;
}}
[data-testid="stSidebar"] a {{ color: #E8EAED; }}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def card_head(title: str) -> None:
    st.markdown(f'<div class="card-head">{escape(title)}</div>', unsafe_allow_html=True)


def kpi(label: str, value: str, note: str, tip: str) -> None:
    """Cartão de indicador; ``tip`` explica o termo ao passar o mouse."""
    card_head(f"{label} ⓘ")
    st.markdown(
        f'<div title="{escape(tip)}"><div class="kpi-value">{escape(value)}</div>'
        f'<div class="kpi-note">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )
