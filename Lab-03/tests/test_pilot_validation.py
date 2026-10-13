import json
from pathlib import Path

import pytest

from lab03.cli import main as collect
from lab03.validation import main, validate_pilot
from test_pilot import PilotTransport


@pytest.fixture
def pilot_report(tmp_path, monkeypatch):
    config = json.loads((Path(__file__).parents[1] / 'config/estudo.json').read_text(encoding='utf-8'))
    config['window'].update(start='2025-03-01T00:00:00Z', end='2026-03-01T00:00:00Z')
    config['population']['initial_sprint_sample'] = 2
    config_path = tmp_path / 'config.json'
    config_path.write_text(json.dumps(config), encoding='utf-8')
    monkeypatch.setenv('GITHUB_TOKEN', 'test-token')
    monkeypatch.setattr('lab03.cli.HttpTransport', lambda token: PilotTransport(2))
    report_path = tmp_path / 'report.json'
    assert collect(['--config', str(config_path), '--pilot', '--cache', str(tmp_path / 'cache.sqlite3'),
                    '--output', str(report_path)]) == 0
    return json.loads(report_path.read_text(encoding='utf-8'))


def test_valida_contratos_e_contagens_do_piloto(pilot_report):
    evidence = validate_pilot(pilot_report, target=2, required=('pilot/project-001',))
    assert evidence['counts']['releases'] == 10
    assert evidence['counts']['workflow_runs'] == 100
    assert evidence['status'] == 'validated'


@pytest.mark.parametrize('failure', ['duplicate', 'snapshot', 'branch', 'release', 'counts', 'config'])
def test_rejeita_evidencia_inconsistente(pilot_report, failure):
    if failure == 'duplicate':
        pilot_report['repositories'][1] = pilot_report['repositories'][0]
    elif failure == 'snapshot':
        pilot_report['source'] = 'snapshot'
    elif failure == 'branch':
        pilot_report['repositories'][0]['workflow_runs'][0]['branch'] = 'feature'
    elif failure == 'release':
        pilot_report['repositories'][0]['report']['catalog']['releases'][0]['prerelease'] = True
    elif failure == 'counts':
        pilot_report['execution']['counts']['commits'] += 1
    else:
        pilot_report['configuration']['sha256'] = 'incorrect'
    with pytest.raises(ValueError):
        validate_pilot(pilot_report, target=2)


def test_manifesto_so_muda_apos_validacao(tmp_path, pilot_report):
    artifact = tmp_path / 'pilot.json'
    artifact.write_text(json.dumps(pilot_report), encoding='utf-8')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'target_eligible_repositories': 100, 'execution_status': 'in_progress'}))
    previous = manifest.read_bytes()
    with pytest.raises(SystemExit):
        main(['--input', str(artifact), '--manifest', str(manifest)])
    assert manifest.read_bytes() == previous
    manifest.write_text(json.dumps({'target_eligible_repositories': 2, 'execution_status': 'in_progress'}))
    assert main(['--input', str(artifact), '--manifest', str(manifest)]) == 0
    result = json.loads(manifest.read_text(encoding='utf-8'))
    assert result['execution_status'] == 'completed'
    assert len(result['execution_evidence']['artifact_sha256']) == 64
