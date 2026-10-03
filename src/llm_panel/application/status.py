"""status: spend versus ceiling plus row and batch counts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from llm_panel.application.spend import Spend, compute_spend, open_intents, pending_batches
from llm_panel.domain.model_ids import ModelIdReport, check_model_ids
from llm_panel.domain.pricing import SpendSettings
from llm_panel.ports import BatchLedger, ResultStore


@dataclass(frozen=True)
class StatusReport:
    spend: Spend
    rows_by_status: dict[str, int]
    pending_batches: int
    pending_jobs: int
    unreconciled_intents: int = 0
    model_ids: ModelIdReport = ModelIdReport()


def get_status(
    store: ResultStore, ledger: BatchLedger, settings: SpendSettings, external: float = 0.0
) -> StatusReport:
    pending = pending_batches(ledger)
    return StatusReport(
        spend=compute_spend(store, ledger, settings, external),
        rows_by_status=dict(Counter(r.status for r in store.iter_rows())),
        pending_batches=len(pending),
        pending_jobs=sum(len(e["jobs"]) for e in pending),
        unreconciled_intents=len(open_intents(ledger)),
        model_ids=check_model_ids(store.iter_rows()),
    )
