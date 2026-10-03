from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.zen import ZenClient
from tests.contract.model_client_contract import ModelClientContract

OK_BODY = {
    "model": "reported-model",
    "choices": [{"message": {"content": '{"ratings": []}'}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
}


class TestFakeModelClient(ModelClientContract):
    provider = "fake"

    def make_client(self, tmp_path):
        return FakeModelClient(state_path=tmp_path / "fake_state.json")


class TestZenClient(ModelClientContract):
    provider = "opencode"

    def make_client(self, tmp_path):
        return ZenClient(
            tmp_path / "zen",
            env={"OPENCODE_API_KEY": "k"},
            transport=lambda url, headers, body, timeout: (200, OK_BODY),
        )
