# Adding a provider

The pipeline talks to models only through the `ModelClient` port (`src/llm_panel/ports.py`).
Adding a vendor means writing one adapter and registering it. Nothing in `application/`,
`domain/` or `bootstrap/cli.py` changes.

## 1. Implement the port

```python
class ModelClient(Protocol):
    provider: str

    def submit_batch(self, jobs: Sequence[RenderedJob]) -> str: ...
    def fetch_results(self, batch_id: str) -> BatchResult: ...
```

- `provider` is the id used in designs and `config.yaml` (e.g. `acme`).
- `submit_batch` submits all jobs as one batch and returns a batch id. A vendor without a batch
  API can make the requests synchronously and persist the results, as `adapters/zen/` does.
- `fetch_results` returns `BatchResult(done=False)` while running. When `done`, it returns exactly
  one `ModelResponse` per job, keyed by `job.job_id`, with `usage` holding `input_tokens` and
  `output_tokens` (spend tracking depends on it) and an `error` message on any non-ok response.
- State must outlive the client object. `submit` and `collect` run as separate cron invocations,
  so a new instance must be able to fetch a batch an earlier one submitted. An unknown batch id
  raises `KeyError`.
- Pin exact model snapshots in designs, never aliases. If the vendor reports which model served a
  request, keep it in `ModelResponse.raw`.
- Never read or log credentials from files. Take the key from `context.environ` and raise a
  `ProviderConfigError` subclass naming the variable if it is missing.
- Keep the vendor wire format (request/response mapping) inside your adapter package.

## 2. Add a builder and register it

```python
# src/llm_panel/adapters/acme/__init__.py
def build(context: ProviderContext) -> ModelClient:
    return AcmeClient(env=context.environ, state_dir=context.config_dir / "results" / "acme")
```

Register it in `default_registry()` in `src/llm_panel/bootstrap/providers.py`:

```python
return {"fake": _build_fake, zen.PROVIDER: zen.build, "acme": acme.build}
```

## 3. Test it without spending money

Subclass the shared contract in `tests/contract/test_model_clients.py`, backing the client with a
fake transport:

```python
class TestAcmeClient(ModelClientContract):
    provider = "acme"

    def make_client(self, tmp_path):
        return AcmeClient(..., transport=fake_transport)
```

Then add adapter-specific tests (retries, error mapping, key handling) under `tests/adapters/`.

## 4. Configure it

In `config.yaml`:

- add the provider to `approved_providers`;
- add a price (USD per million tokens) for each pinned snapshot under `prices`; submission
  refuses a model with no price;
- put the key in `.env` (gitignored) under the variable your adapter documents.

`max_spend_usd` applies across all providers. `submit` needs `--confirm`, and the project rules
require confirming with the maintainer before the first paid call on any new provider.
