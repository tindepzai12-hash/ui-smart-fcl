from types import SimpleNamespace
import pytest
from backend import ai, db
from test_core import client, H


@pytest.fixture(autouse=True)
def clear_test_key():
    ai.remove()
    yield
    ai.remove()


def test_connection_exercises_structured_responses_and_records_usage(monkeypatch):
    calls = []
    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_parsed=ai.ConnectionResult(status='ok'), usage=SimpleNamespace(input_tokens=20, output_tokens=5))
    def factory(**kwargs):
        assert kwargs['max_retries'] == 0
        return SimpleNamespace(responses=SimpleNamespace(parse=parse))
    monkeypatch.setattr(ai, 'OpenAI', factory)
    ai.configure(' synthetic-secret ', ' gpt-4.1-mini ')
    assert not ai.status()['connected']
    result = client.post('/api/ai/test', headers=H)
    assert result.status_code == 200
    assert result.json()['connected'] and result.json()['checked_at']
    assert 'synthetic-secret' not in result.text
    assert calls[0]['store'] is False
    assert calls[0]['max_output_tokens'] == 64
    assert calls[0]['text_format'] is ai.ConnectionResult
    assert 'Connection test only' in calls[0]['input']
    row = db.one("SELECT * FROM ai_usage WHERE status='connection_test' ORDER BY rowid DESC LIMIT 1")
    assert row['case_id'] is None and row['input_tokens'] == 20 and row['output_tokens'] == 5


@pytest.mark.parametrize('code,body,expected', [
    (401, {}, 'từ chối khóa'),
    (403, {}, 'chưa có quyền'),
    (404, {}, 'Không tìm thấy model'),
    (429, {'error': {'code': 'insufficient_quota'}}, 'ngân sách'),
])
def test_connection_failure_resets_status_and_redacts_errors(monkeypatch, code, body, expected):
    class Failure(Exception):
        status_code = code
    exc = Failure('server body leaks synthetic-secret')
    exc.body = body
    def parse(**kwargs):
        raise exc
    monkeypatch.setattr(ai, 'OpenAI', lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    ai.configure('synthetic-secret', 'gpt-4.1-mini')
    ai._tested = True  # An old successful status must not survive a failed retest.
    result = client.post('/api/ai/test', headers=H)
    assert result.status_code == 422
    assert expected in result.json()['detail']
    assert 'synthetic-secret' not in result.text
    assert ai.status()['configured'] and not ai.status()['connected']
    assert ai.status()['checked_at'] is None


def test_connection_refusal_and_missing_key_cannot_report_connected(monkeypatch):
    result = client.post('/api/ai/test', headers=H)
    assert result.status_code == 422
    ai.configure('synthetic-secret', 'gpt-4.1-mini')
    monkeypatch.setattr(ai, 'OpenAI', lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=lambda **kwargs: SimpleNamespace(output_parsed=None))))
    result = client.post('/api/ai/test', headers=H)
    assert result.status_code == 422
    assert not ai.status()['connected']
    with pytest.raises(ValueError):
        ai.configure('bad key with spaces', 'gpt-4.1-mini')
