import inspect

from llm_panel.ports import BatchLedger, ModelClient, ResultStore


def public(proto):
    return {n for n, _ in inspect.getmembers(proto, inspect.isfunction) if not n.startswith("_")}


def test_model_client_port_methods():
    assert public(ModelClient) == {"submit_batch", "fetch_results"}


def test_result_store_port_is_append_only():
    assert public(ResultStore) == {"append", "exists", "iter_rows"}


def test_ledger_port_methods():
    assert public(BatchLedger) == {"record", "entries"}


def test_stub_adapters_satisfy_ports():
    class Client:
        provider = "x"

        def submit_batch(self, jobs):
            return "b"

        def fetch_results(self, batch_id):
            return None

    class Store:
        def append(self, row): ...
        def exists(self, job_id):
            return False

        def iter_rows(self):
            return iter(())

    assert isinstance(Client(), ModelClient)
    assert isinstance(Store(), ResultStore)
    assert not isinstance(object(), ResultStore)
