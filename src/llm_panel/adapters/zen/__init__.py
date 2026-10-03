"""OpenCode Zen adapter. `build` is the registry entry point (see bootstrap/providers.py)."""

from __future__ import annotations

from llm_panel.adapters.zen.client import (
    API_KEY_ENV,
    ZenClient,
    ZenConfigError,
    urllib_transport,
)

PROVIDER = "opencode"

__all__ = ["API_KEY_ENV", "PROVIDER", "ZenClient", "ZenConfigError", "build", "urllib_transport"]


def build(context) -> ZenClient:
    """Build the client from a `ProviderContext`.

    The output cap equals the per-policy cost estimate, so the estimate bounds the cost.
    """
    extra = {"transport": context.transports[PROVIDER]} if PROVIDER in context.transports else {}
    return ZenClient(
        context.config_dir / "results" / "zen",
        env=context.environ,
        max_tokens_per_policy=context.est_output_tokens_per_policy,
        **extra,
    )
