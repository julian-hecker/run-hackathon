import types
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _mount_twilio_router_with_fakes(is_local: bool = True):
    # Import module under test
    import voice_api.routers.twilio as tw
    import voice_api.utils.twilio_security as sec

    # Patch settings to control protocol selection and avoid env dependency
    dummy_settings = types.SimpleNamespace(is_local=is_local)
    tw.settings = dummy_settings

    # Disable request signature validation dependency on routes
    async def _noop_validate(_req=None):
        return None

    app = FastAPI()
    # Override the dependency used in route decorators to bypass signature checks
    app.dependency_overrides[sec.validate_twilio] = _noop_validate
    app.include_router(tw.twilio_router)
    return app, tw


def test_connect_generates_twiML_local_urls():
    app, _tw = _mount_twilio_router_with_fakes(is_local=True)
    client = TestClient(app)

    form = {
        "From": "+15551234567",
        "To": "+15557654321",
        "Direction": "inbound",
    }

    res = client.post("/twilio/connect", data=form)

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/xml")
    body = res.text
    # Local should use ws/http
    assert "ws://" in body
    assert "http://" in body
    assert "/twilio/stream" in body
    assert "/twilio/callback" in body


def test_connect_generates_twiML_prod_urls():
    app, _tw = _mount_twilio_router_with_fakes(is_local=False)
    client = TestClient(app)

    form = {
        "From": "+15551234567",
        "To": "+15557654321",
        "Direction": "inbound",
    }

    res = client.post("/twilio/connect", data=form)

    assert res.status_code == 200
    body = res.text
    # Prod should use wss/https
    assert "wss://" in body
    assert "https://" in body


def test_callback_returns_204():
    app, _tw = _mount_twilio_router_with_fakes(is_local=True)
    client = TestClient(app)

    form = {
        "AccountSid": "AC123",
        "CallSid": "CA123",
        "StreamSid": "MZ123",
        "StreamName": "test",
        "StreamEvent": "stream-started",
        "Timestamp": datetime.now(timezone.utc).isoformat(),
    }

    res = client.post("/twilio/callback", data=form)
    assert res.status_code == 204


def test_websocket_minimal_handshake(monkeypatch):
    app, tw = _mount_twilio_router_with_fakes(is_local=True)

    # Stub out live messaging primitives used by the websocket handler
    class DummyQueue:
        def __init__(self):
            self.sent = []

        def send_content(self, item):
            self.sent.append(item)

        def close(self):  # pragma: no cover - graceful shutdown
            pass

    async def fake_start_agent_session(_from_phone, _call_sid):
        # live_events: an async iterable that's quickly exhausted
        async def _events():
            if False:
                yield None  # pragma: no cover

        return _events(), DummyQueue()

    async def fake_agent_to_client_messaging(_handler, _events):
        return None

    def fake_send_pcm_to_agent(_pcm, _queue):
        return None

    def fake_text_to_content(text, role):  # echo as tuple for visibility
        return (text, role)

    monkeypatch.setattr(
        tw, "start_agent_session", fake_start_agent_session, raising=True
    )
    monkeypatch.setattr(
        tw, "agent_to_client_messaging", fake_agent_to_client_messaging, raising=True
    )
    monkeypatch.setattr(tw, "send_pcm_to_agent", fake_send_pcm_to_agent, raising=True)
    monkeypatch.setattr(tw, "text_to_content", fake_text_to_content, raising=True)

    client = TestClient(app)

    with client.websocket_connect("/twilio/stream") as ws:
        ws.send_json({"event": "connected"})
        ws.send_json(
            {
                "event": "start",
                "start": {
                    "callSid": "CA123",
                    "customParameters": {"from_phone": "+15551234567"},
                },
                "streamSid": "MZ123",
            }
        )
        # Immediately stop to exit the loop
        ws.send_json({"event": "stop"})
