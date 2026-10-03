"""Provider registry: maps a provider id to a builder, so adding a vendor never edits the CLI.

To add a provider, write an adapter implementing `ports.ModelClient`, give it a
`build(context: ProviderContext) -> ModelClient`, and register it in `default_registry`
(or pass your own registry to `make_client_factory`). See docs/adding-a-provider.md.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from llm_panel.adapters import zen
from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.ports import ModelClient, ProviderConfigError


@dataclass(frozen=True)
class ProviderContext:
    """Everything a builder may need. Credentials come from `environ`, never read from files."""

    config_dir: Path
    environ: Mapping[str, str] = field(default_factory=lambda: os.environ)
    est_output_tokens_per_policy: int = 100
    transports: Mapping[str, Callable] = field(default_factory=dict)  # test seam: provider -> fake


ProviderBuilder = Callable[[ProviderContext], ModelClient]


def _build_fake(context: ProviderContext) -> ModelClient:
    return FakeModelClient(state_path=context.config_dir / "results" / "fake_state.json")


def default_registry() -> dict[str, ProviderBuilder]:
    return {"fake": _build_fake, zen.PROVIDER: zen.build}


def make_client_factory(
    context: ProviderContext, registry: Mapping[str, ProviderBuilder]
) -> Callable[[str], ModelClient]:
    clients: dict[str, ModelClient] = {}

    def factory(provider: str) -> ModelClient:
        if provider not in clients:
            builder = registry.get(provider)
            if builder is None:
                known = ", ".join(sorted(registry))
                raise ProviderConfigError(
                    f"no adapter registered for provider {provider!r} (known: {known})"
                )
            clients[provider] = builder(context)
        return clients[provider]

    return factory
