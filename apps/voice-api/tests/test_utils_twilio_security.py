import types

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


def test_validate_twilio_noop_in_local(monkeypatch):
    # Import after patching module attributes
    import voice_api.utils.twilio_security as sec

    # Replace settings with a dummy that short-circuits
    dummy_settings = types.SimpleNamespace(is_local=True)
    monkeypatch.setattr(sec, "settings", dummy_settings, raising=False)

    app = FastAPI()

    @app.post("/check", dependencies=[Depends(sec.validate_twilio)])
    def check():  # pragma: no cover - trivial test endpoint
        return {"ok": True}

    client = TestClient(app)
    # No headers/signature required because is_local=True
    resp = client.post("/check", data={"foo": "bar"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.parametrize("is_valid, expected_status", [(True, 200), (False, 403)])
def test_validate_twilio_signature_enforced(monkeypatch, is_valid, expected_status):
    # Import module under test
    import voice_api.utils.twilio_security as sec

    # Fake RequestValidator
    class FakeValidator:
        def __init__(self, *_args, **_kwargs):  # pragma: no cover - trivial init
            pass

        def validate(self, *_args, **_kwargs):
            return is_valid

    monkeypatch.setattr(sec, "RequestValidator", FakeValidator, raising=True)

    # Minimum viable settings
    dummy_settings = types.SimpleNamespace(
        is_local=False, twilio=types.SimpleNamespace(auth_token="x")
    )
    monkeypatch.setattr(sec, "settings", dummy_settings, raising=False)

    app = FastAPI()

    @app.post("/secure", dependencies=[Depends(sec.validate_twilio)])
    def secure():  # pragma: no cover - trivial test endpoint
        return {"ok": True}

    client = TestClient(app)

    form = {"a": "b"}
    headers = {
        "X-Twilio-Signature": "dummy",
        "host": "testserver",  # TestClient default host
        "x-forwarded-proto": "http",
    }

    resp = client.post("/secure", data=form, headers=headers)

    assert resp.status_code == expected_status
    if is_valid:
        assert resp.json() == {"ok": True}
