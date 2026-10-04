"""Load config.yaml. The spend ceiling can be lowered in config but never raised past 15 USD."""

from __future__ import annotations

import glob
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from llm_panel.adapters.jsonl import JsonlBatchLedger, JsonlResultStore
from llm_panel.application.spend import compute_spend
from llm_panel.domain.pricing import HARD_CEILING_USD, Price, SpendSettings


@dataclass(frozen=True)
class Config:
    spend: SpendSettings
    approved_providers: frozenset[str]
    raw_store: Path
    ledger: Path
    inputs_dir: Path
    counts_spend_from: list[Path] = field(default_factory=list)  # config paths/globs
    prompts_dir: Path = Path("prompts")  # study templates, prompts/<call unit>/<wording>.txt
    # evidence level -> directory of per-policy packets (<policy id>.md)
    evidence_packets: dict[str, Path] = field(default_factory=dict)


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
        snapshot: Price(
            float(p["input"]),
            float(p["output"]),
            float(p["input_cached"]) if p.get("input_cached") is not None else None,
        )
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
        counts_spend_from=[base / p for p in data.get("counts_spend_from") or ()],
        prompts_dir=base / paths.get("prompts_dir", "prompts"),
        evidence_packets={
            level: base / d for level, d in (paths.get("evidence_packets") or {}).items()
        },
    )


class ExternalSpendError(RuntimeError):
    """Another ledger's spend could not be read, so the global ceiling cannot be enforced."""


def external_spend(config: Config) -> float:
    """Committed spend (actual + outstanding) in the ledgers of the configs this one lists in
    `counts_spend_from`. Fails closed: an unmatched pattern or unreadable config refuses.
    Not recursive, and this config's own ledger is skipped so nothing is counted twice."""
    own = config.ledger.resolve()
    seen: set[Path] = set()
    total = 0.0
    for pattern in config.counts_spend_from:
        matches = sorted(glob.glob(str(pattern)))
        if not matches:
            raise ExternalSpendError(f"counts_spend_from matched no config: {pattern}")
        for match in matches:
            try:
                other = load_config(match)
                key = other.ledger.resolve()
                if key == own or key in seen:
                    continue
                seen.add(key)
                total += compute_spend(
                    JsonlResultStore(other.raw_store), JsonlBatchLedger(other.ledger), other.spend
                ).committed
            except Exception as exc:  # unreadable store, missing price, bad yaml: fail closed
                raise ExternalSpendError(f"cannot read spend from {match}: {exc}") from exc
    return total
