from datetime import datetime, timedelta

import pytest

from lab03.domain import Window, timestamp
from lab03.metrics import calculate_deployment_frequency


def test_frequencia_usa_duracao_exata_e_janela_semiaberta():
    start = timestamp("2024-01-01T00:00:00Z")
    end = start + timedelta(days=14, hours=12)
    window = Window(start, end)
    result = calculate_deployment_frequency(
        [
            start - timedelta(microseconds=1),
            start,
            start + timedelta(days=7),
            end,
        ],
        window,
    )
    assert result.releases_in_window == 2
    assert result.window_seconds == 14.5 * 24 * 60 * 60
    assert result.window_weeks == 14.5 / 7
    assert result.releases_per_week == pytest.approx(2 / (14.5 / 7))


@pytest.mark.parametrize("published_at", [
    [None],
    ["2025-01-01T00:00:00Z"],
    [datetime(2025, 1, 1)],
])
def test_frequencia_rejeita_datas_nao_datetime(published_at):
    window = Window(timestamp("2025-01-01T00:00:00Z"), timestamp("2025-02-01T00:00:00Z"))
    with pytest.raises((TypeError, ValueError)):
        calculate_deployment_frequency(published_at, window)
