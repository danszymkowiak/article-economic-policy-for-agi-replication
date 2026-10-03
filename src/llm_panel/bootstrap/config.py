"""Load config.yaml. The spend ceiling can be lowered in config but never raised past 15 USD."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from llm_panel.domain.pricing import HARD_CEILING_USD, Price, SpendSettings


@dataclass(frozen=True)
class Config:
    spend: SpendSettings
    approved_providers: frozenset[str]
    raw_store: Path
    ledger: Path
    inputs_dir: Path


def load_config(path: Path | str) -> Config:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "max_spend_usd" not in data:
        raise ValueError("config must set max_spend_usd")
    ceiling = float(data["max_spend_usd"])
    if not 0 <= ceiling <= HARD_CEILING_USD:
        raise ValueError(f"max_spend_usd must be within [0, {HARD_CEILING_USD:g}], got {ceiling}")
    base = path.parent
    paths = data.get("paths") or {}
    prices = {
        snapshot: Price(float(p["input"]), float(p["output"]))
        for snapshot, p in (data.get("prices") or {}).items()
    }
    return Config(
        spend=SpendSettings(
            max_spend_usd=ceiling,
            prices=prices,
            est_output_tokens_per_policy=int(data.get("est_output_tokens_per_policy", 100)),
            chars_per_token=float(data.get("chars_per_token", 4.0)),
            batch_discount=float(data.get("batch_discount", 1.0)),
        ),
        approved_providers=frozenset(data.get("approved_providers") or ()),
        raw_store=base / paths.get("raw_store", "results/raw/rows.jsonl"),
        ledger=base / paths.get("ledger", "results/batches.jsonl"),
        inputs_dir=base / paths.get("inputs_dir", "."),
    )
