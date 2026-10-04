"""OpenCode Zen ModelClient: synchronous chat-completions requests behind the batch port.

Zen has no batch API, so `submit_batch` makes the requests (bounded concurrency) and persists
every response to `<state_dir>/<batch_id>.jsonl`; `fetch_results` reads that file, so a later
`collect` process sees the results. The API key is only ever put in the request header.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from llm_panel.adapters.zen.protocol import build_request, is_retryable, parse_completion
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import BatchResult, ModelResponse
from llm_panel.ports import ProviderConfigError

API_KEY_ENV = "OPENCODE_API_KEY"
DEFAULT_URL = "https://opencode.ai/zen/v1/chat/completions"
USER_AGENT = "llm-panel/0.1 (research pipeline)"

# (url, headers, json body, timeout seconds) -> (http status, parsed json payload)
Transport = Callable[[str, Mapping[str, str], dict, float], tuple[int, dict]]


class ZenConfigError(ProviderConfigError):
    pass


def urllib_transport(url: str, headers: Mapping[str, str], body: dict, timeout: float):
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=dict(headers), method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            status, text = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        status, text = exc.code, exc.read().decode("utf-8", "replace")
    except urllib.error.URLError as exc:  # connect failures: nothing was sent, safe to retry
        raise ConnectionError(str(exc.reason)) from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {"error": text[:200]}
    return status, payload if isinstance(payload, dict) else {"error": text[:200]}


class ZenClient:
    provider = "opencode"

    def __init__(
        self,
        state_dir: Path | str,
        *,
        env: Mapping[str, str] | None = None,
        transport: Transport = urllib_transport,
        sleep: Callable[[float], None] = time.sleep,
        url: str = DEFAULT_URL,
        max_tokens_per_policy: int = 100,
        max_workers: int = 4,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        timeout_seconds: float = 120.0,
    ) -> None:
        key = (os.environ if env is None else env).get(API_KEY_ENV, "").strip()
        if not key:
            raise ZenConfigError(f"{API_KEY_ENV} is not set (put it in .env or the environment)")
        self._key = key
        self._state_dir = Path(state_dir)
        self._transport = transport
        self._sleep = sleep
        self._url = url
        self._max_tokens_per_policy = max_tokens_per_policy
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._timeout = timeout_seconds

    def submit_batch(self, jobs: Sequence[RenderedJob]) -> str:
        batch_id = f"zen-{uuid.uuid4().hex}"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        path = self._state_dir / f"{batch_id}.jsonl"
        with (
            path.open("a", encoding="utf-8") as fh,
            ThreadPoolExecutor(max_workers=self._max_workers) as pool,
        ):
            futures = [pool.submit(self._request, job) for job in jobs]
            for future in as_completed(futures):  # single writer: this thread
                self._write(fh, asdict(future.result()))
            self._write(fh, {"_done": True})
        return batch_id

    def fetch_results(self, batch_id: str) -> BatchResult:
        path = self._state_dir / f"{batch_id}.jsonl"
        if not path.exists():
            raise KeyError(f"unknown batch {batch_id}")
        records = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
        done = any(r.get("_done") for r in records)
        responses = tuple(ModelResponse(**r) for r in records if "job_id" in r)
        return BatchResult(done=done, responses=responses if done else ())

    @staticmethod
    def _write(fh, record: dict) -> None:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    def _request(self, job: RenderedJob) -> ModelResponse:
        body = build_request(job, self._max_tokens_per_policy * job.n_ratings)
        headers = {
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,  # urllib's default agent is blocked (403, code 1010)
        }
        try:
            for attempt in range(self._max_retries + 1):
                try:
                    status, payload = self._transport(self._url, headers, body, self._timeout)
                except TimeoutError as exc:
                    # The request may have been processed and billed: never resend it blindly.
                    return ModelResponse(job.job_id, "error", "", error=f"timed out: {exc}")
                except OSError as exc:  # connection failure
                    status, payload = 0, {"error": f"connection failed: {exc}"}
                    retryable = True
                else:
                    retryable = is_retryable(status)
                if retryable and attempt < self._max_retries:
                    self._sleep(self._backoff * 2**attempt)
                    continue
                if status == 0:
                    return ModelResponse(job.job_id, "error", "", error=payload["error"])
                return parse_completion(job.job_id, status, payload)
        except Exception as exc:  # one bad job must not lose the rest of a paid batch
            return ModelResponse(job.job_id, "error", "", error=f"{type(exc).__name__}: {exc}")
        raise AssertionError("unreachable")
