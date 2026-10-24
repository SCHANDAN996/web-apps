"""The one-time consent helper must keep credentials out of the checkout and stdout."""
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def helper(monkeypatch):
    spec = importlib.util.spec_from_file_location('youtube_authorize',
        Path(__file__).resolve().parents[1] / 'scripts' / 'youtube_authorize.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    seen = {}
    class Flow:
        @staticmethod
        def from_client_secrets_file(path, scopes):
            seen['scopes'] = scopes
            return Flow()
        def run_local_server(self, **kwargs):
            seen.update(kwargs)
            return SimpleNamespace(client_id='client', client_secret='SECRET', refresh_token='TOKEN')
    monkeypatch.setitem(sys.modules, 'google_auth_oauthlib.flow', SimpleNamespace(InstalledAppFlow=Flow))
    return module, seen


def test_consent_credentials_stay_private(monkeypatch, tmp_path, capsys):
    module, seen = helper(monkeypatch)
    output = tmp_path / 'credentials.json'
    monkeypatch.setattr(sys, 'argv', ['authorize', 'client.json', str(output)])
    module.main()
    assert seen['login_hint'] == 'all.chandansingh@gmail.com'
    assert seen['access_type'] == 'offline' and seen['prompt'] == 'consent'
    assert set(seen['scopes']) == set(module.SCOPES)
    assert json.loads(output.read_text())['YOUTUBE_REFRESH_TOKEN'] == 'TOKEN'
    if os.name != 'nt':
        assert output.stat().st_mode & 0o777 == 0o600
    assert 'TOKEN' not in capsys.readouterr().out
    with pytest.raises(FileExistsError):
        module.main()


def test_consent_rejects_output_in_repository_before_login(monkeypatch):
    module, seen = helper(monkeypatch)
    output = Path(module.__file__).resolve().parent / 'must-not-write.json'
    monkeypatch.setattr(sys, 'argv', ['authorize', 'client.json', str(output)])
    with pytest.raises(SystemExit):
        module.main()
    assert not seen and not output.exists()
