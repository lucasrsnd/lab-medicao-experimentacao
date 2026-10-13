import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from lab03.collectors.candidates import select_candidates
from lab03.domain import timestamp
from lab03.github import ApiError, GitHubClient, HttpTransport
from test_candidates import CandidateTransport


@pytest.mark.parametrize('message,reason', [
    ('The history or contributor list is too large to list contributors for this repository via the API.',
     'contributors_too_large'),
    ('Resource not accessible by personal access token', None),
    ('API rate limit exceeded', None),
])
def test_reconhece_somente_limite_especifico_de_contribuidores(monkeypatch, message, reason):
    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 403, 'Forbidden', {},
                        BytesIO(json.dumps({'message': message}).encode()))
    monkeypatch.setattr('lab03.github.urlopen', fail)
    with pytest.raises(ApiError) as error:
        HttpTransport('test-secret').get('https://api.github.com/repos/a/b/contributors')
    assert error.value.reason == reason
    assert message not in str(error.value)
    assert 'test-secret' not in str(error.value)


@pytest.mark.parametrize('reason', ['contributors_too_large', None])
def test_funil_exclui_limite_mas_propaga_403_generico(reason):
    class Unavailable(CandidateTransport):
        def get(self, url):
            if '/contributors?' in url:
                raise ApiError(403, url, reason=reason)
            return super().get(url)
    def select():
        return select_candidates(
            GitHubClient(Unavailable()), timestamp('2025-01-01T00:00:00Z'),
            timestamp('2026-01-01T00:00:00Z'), stars_min_exclusive=1000,
            sample_size=1, minimum_releases=1, minimum_valid_runs=1,
            valid_conclusions=('success', 'failure'),
        )
    if reason:
        output = select()
        assert output['eligible_repositories'] == []
        assert output['funnel']['metadata']['excluded'] == {'contributors_unavailable_api_limit': 1}
    else:
        with pytest.raises(ApiError):
            select()
