from pathlib import Path

import pytest

from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.zen import ZenClient
from llm_panel.bootstrap.providers import (
    ProviderContext,
    default_registry,
    make_client_factory,
)
from llm_panel.ports import ProviderConfigError


def ctx(tmp_path: Path, **kw) -> ProviderContext:
    return ProviderContext(config_dir=tmp_path, environ=kw.pop("environ", {}), **kw)


def test_default_registry_knows_the_bundled_providers():
    assert {"fake", "opencode"} <= set(default_registry())


def test_factory_builds_each_client_once(tmp_path):
    seen = []

    def build(context):
        seen.append(context)
        return FakeModelClient(provider="acme")

    factory = make_client_factory(ctx(tmp_path), {"acme": build})
    assert factory("acme") is factory("acme")
    assert len(seen) == 1


def test_a_new_provider_needs_no_change_to_core_code(tmp_path):
    client = FakeModelClient(provider="acme")
    factory = make_client_factory(ctx(tmp_path), {**default_registry(), "acme": lambda c: client})
    assert factory("acme") is client


def test_unknown_provider_is_a_config_error_naming_the_known_ones(tmp_path):
    factory = make_client_factory(ctx(tmp_path), default_registry())
    with pytest.raises(ProviderConfigError, match="acme.*fake"):
        factory("acme")


def test_zen_builder_reads_the_key_from_the_context_environment(tmp_path):
    factory = make_client_factory(
        ctx(tmp_path, environ={"OPENCODE_API_KEY": "k"}), default_registry()
    )
    assert isinstance(factory("opencode"), ZenClient)


def test_zen_builder_without_a_key_raises_the_port_level_error(tmp_path):
    factory = make_client_factory(ctx(tmp_path), default_registry())
    with pytest.raises(ProviderConfigError, match="OPENCODE_API_KEY"):
        factory("opencode")


def test_builders_receive_the_cost_estimate_cap(tmp_path):
    context = ctx(tmp_path, est_output_tokens_per_policy=77)
    assert context.est_output_tokens_per_policy == 77
