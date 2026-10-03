import json
import threading
import time

import pytest

from llm_panel.adapters.zen import ZenClient, ZenConfigError, urllib_transport
from llm_panel.ports import ModelClient
from tests.domain.test_models import make_job

KEY = "sk-test-secret-123"
OK_BODY = {
    "model": "big-pickle-reported",
    "choices": [{"message": {"content": '{"ratings": []}'}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
}


class ScriptedTransport:
    """Replays a list of (status, payload) or exceptions per call; records every request."""

    def __init__(self, script=None, default=(200, OK_BODY)):
        self.script = list(script or [])
        self.default = default
        self.calls = []
        self._lock = threading.Lock()

    def __call__(self, url, headers, body, timeout):
        with self._lock:
            self.calls.append((url, dict(headers), body, timeout))
            step = self.script.pop(0) if self.script else self.default
        if isinstance(step, Exception):
            raise step
        return step


def make_client(tmp_path, transport=None, **kw):
    sleeps = []
    client = ZenClient(
        tmp_path / "zen",
        env={"OPENCODE_API_KEY": KEY},
        transport=transport or ScriptedTransport(),
        sleep=sleeps.append,
        **kw,
    )
    return client, sleeps


def jobs(n=3):
    return [make_job(prompt=f"prompt {i}", provider="opencode", seed=i) for i in range(n)]


def run(client, js):
    result = client.fetch_results(client.submit_batch(js))
    return {r.job_id: r for r in result.responses}, result


def test_satisfies_port(tmp_path):
    client, _ = make_client(tmp_path)
    assert isinstance(client, ModelClient) and client.provider == "opencode"


def test_missing_key_fails_clearly_and_names_the_variable(tmp_path):
    with pytest.raises(ZenConfigError, match="OPENCODE_API_KEY"):
        ZenClient(tmp_path, env={}, transport=ScriptedTransport())
    with pytest.raises(ZenConfigError, match="OPENCODE_API_KEY"):
        ZenClient(tmp_path, env={"OPENCODE_API_KEY": "  "}, transport=ScriptedTransport())


def test_submit_then_fetch_returns_one_response_per_job(tmp_path):
    client, _ = make_client(tmp_path)
    js = jobs()
    by_id, result = run(client, js)
    assert result.done
    assert set(by_id) == {j.job_id for j in js}
    assert all(
        r.status == "ok" and r.usage == {"input_tokens": 10, "output_tokens": 5}
        for r in by_id.values()
    )
    assert all(r.raw["model"] == "big-pickle-reported" for r in by_id.values())


def test_request_uses_chat_completions_bearer_auth_and_token_cap(tmp_path):
    transport = ScriptedTransport()
    client, _ = make_client(tmp_path, transport, max_tokens_per_policy=120)
    client.submit_batch([make_job(policy_ids=("a", "b", "c"), policy_labels=("a", "b", "c"))])
    url, headers, body, _ = transport.calls[0]
    assert url == "https://opencode.ai/zen/v1/chat/completions"
    assert headers["Authorization"] == f"Bearer {KEY}"
    assert body["max_tokens"] == 360  # 120 per policy x 3 policies


def test_api_key_is_never_persisted(tmp_path):
    transport = ScriptedTransport(script=[(401, {"error": {"message": "nope"}})])
    client, _ = make_client(tmp_path, transport)
    run(client, jobs())
    stored = "".join(p.read_text() for p in (tmp_path / "zen").iterdir())
    assert stored and KEY not in stored


def test_rate_limit_is_retried_with_backoff_then_succeeds(tmp_path):
    transport = ScriptedTransport(script=[(429, {}), (503, {}), (200, OK_BODY)])
    client, sleeps = make_client(tmp_path, transport, max_workers=1)
    by_id, _ = run(client, jobs(1))
    assert next(iter(by_id.values())).status == "ok"
    assert len(transport.calls) == 3
    assert len(sleeps) == 2 and sleeps[1] > sleeps[0] > 0


def test_persistent_server_error_gives_up_after_max_retries(tmp_path):
    transport = ScriptedTransport(default=(500, {"error": "boom"}))
    client, _ = make_client(tmp_path, transport, max_retries=2)
    by_id, _ = run(client, jobs(1))
    resp = next(iter(by_id.values()))
    assert resp.status == "error" and "500" in resp.error
    assert len(transport.calls) == 3  # first try plus two retries


def test_client_errors_are_not_retried(tmp_path):
    transport = ScriptedTransport(default=(401, {"error": {"message": "bad key"}}))
    client, sleeps = make_client(tmp_path, transport)
    by_id, _ = run(client, jobs(1))
    assert next(iter(by_id.values())).status == "error"
    assert len(transport.calls) == 1 and not sleeps


def test_read_timeout_is_not_retried_because_it_may_have_been_billed(tmp_path):
    transport = ScriptedTransport(default=TimeoutError("read timed out"))
    client, sleeps = make_client(tmp_path, transport)
    by_id, _ = run(client, jobs(1))
    resp = next(iter(by_id.values()))
    assert resp.status == "error" and "timed out" in resp.error
    assert len(transport.calls) == 1 and not sleeps


def test_connection_failure_is_retried(tmp_path):
    transport = ScriptedTransport(script=[ConnectionError("refused"), (200, OK_BODY)])
    client, _ = make_client(tmp_path, transport, max_workers=1)
    by_id, _ = run(client, jobs(1))
    assert next(iter(by_id.values())).status == "ok" and len(transport.calls) == 2


def test_one_failing_job_does_not_lose_the_others(tmp_path):
    transport = ScriptedTransport(script=[(400, {"error": "bad"})], default=(200, OK_BODY))
    client, _ = make_client(tmp_path, transport, max_workers=1)
    by_id, _ = run(client, jobs(3))
    assert sorted(r.status for r in by_id.values()) == ["error", "ok", "ok"]


def test_results_survive_a_new_process(tmp_path):
    client, _ = make_client(tmp_path)
    js = jobs()
    batch_id = client.submit_batch(js)
    fresh, _ = make_client(tmp_path)
    result = fresh.fetch_results(batch_id)
    assert result.done and len(result.responses) == len(js)


def test_unknown_batch_raises(tmp_path):
    client, _ = make_client(tmp_path)
    with pytest.raises(KeyError):
        client.fetch_results("zen-nope")


def test_concurrency_is_bounded(tmp_path):
    active, peak, lock = 0, 0, threading.Lock()

    def transport(url, headers, body, timeout):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        return 200, OK_BODY

    client, _ = make_client(tmp_path, transport, max_workers=2)
    run(client, jobs(8))
    assert 1 <= peak <= 2


def test_urllib_transport_against_a_loopback_server():
    from http.server import BaseHTTPRequestHandler, HTTPServer

    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["auth"] = self.headers["Authorization"]
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            code, out = (
                (429, b"<html>slow down</html>")
                if seen["body"]["seed"]
                else (200, json.dumps(OK_BODY).encode())
            )
            self.send_response(code)
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/x"
        hdr = {"Authorization": "Bearer k", "Content-Type": "application/json"}
        assert urllib_transport(url, hdr, {"seed": 0}, 5) == (200, OK_BODY)
        status, payload = urllib_transport(url, hdr, {"seed": 1}, 5)
        assert status == 429 and "slow down" in str(payload)  # non-JSON body is tolerated
        assert seen["auth"] == "Bearer k"
    finally:
        server.shutdown()
        server.server_close()


def test_requests_identify_themselves_with_a_user_agent(tmp_path):
    # Zen sits behind Cloudflare, which rejects urllib's default agent with HTTP 403 / 1010.
    transport = ScriptedTransport()
    client, _ = make_client(tmp_path, transport)
    client.submit_batch(jobs(1))
    assert transport.calls[0][1]["User-Agent"].startswith("llm-panel/")
