"""TASK-33 end to end: a one-at-a-time design file through plan, fake submit and collect, plus
call counts on the real study inputs. No network, no paid calls."""

import shutil
from pathlib import Path

import pytest
import yaml

from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.smoketest import ratings_from_store
from llm_panel.bootstrap.cli import main
from llm_panel.bootstrap.config import load_config
from llm_panel.bootstrap.design_loader import load_oat_design
from llm_panel.bootstrap.inputs_loader import load_packets, load_study_materials
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.oat_design import expand_cells
from llm_panel.domain.study_jobs import count_cell_calls, jobs_for_cell_repeat
from tests.name_patterns import names_found

REPO = Path(__file__).parents[1]
SNAP = "fake-model-2026-01-01"
POLICY_IDS = ("ubi", "nit", "ui")


def _personas(source, n):
    return {"personas": [{"id": f"{source}_{i}", "description": f"{source} {i}"} for i in range(n)]}


@pytest.fixture
def project(tmp_path):
    inputs = tmp_path / "inputs"
    (inputs / "personas").mkdir(parents=True)
    (inputs / "personas" / "named.yaml").write_text(yaml.safe_dump(_personas("named", 3)))
    (inputs / "personas" / "reconstructed.yaml").write_text(yaml.safe_dump(_personas("rec", 3)))
    policies = [
        {"id": "ubi", "name": "Universal Basic Income (UBI)", "description": "Cash for all."},
        {"id": "nit", "name": "Negative Income Tax (NIT)", "description": "Cash below a line."},
        {"id": "ui", "name": "Unemployment Insurance (UI)", "description": "Cash after job loss."},
    ]
    for p in policies:
        p["blinded_description"] = p["description"]
    (inputs / "policies.yaml").write_text(yaml.safe_dump(policies))
    criteria = [
        {"id": "standards_of_living", "name": "Standards of Living", "description": "x"},
        {"id": "full_transformation", "name": "Full Transformation", "description": "y"},
    ]
    (inputs / "criteria.yaml").write_text(yaml.safe_dump(criteria))
    paras = inputs / "description_paraphrases"
    paras.mkdir()
    for lv in ("para_1", "para_2", "para_3"):
        (paras / f"{lv}.yaml").write_text(yaml.safe_dump({p: f"{p} {lv}" for p in POLICY_IDS}))
    packets = tmp_path / "packets"
    packets.mkdir()
    for p in policies:
        (packets / f"{p['id']}.md").write_text(
            f"# Evidence packet: {p['name']}\n\nStudies of {p['name']} found effects.\n"
        )
    shutil.copytree(REPO / "prompts", tmp_path / "prompts")
    cfg = {
        "max_spend_usd": 15,
        "approved_providers": ["fake"],
        "paths": {
            "raw_store": "raw.jsonl", "ledger": "ledger.jsonl", "inputs_dir": "inputs",
            "prompts_dir": "prompts", "evidence_packets": {"wikipedia": "packets"},
        },
        "prices": {SNAP: {"input": 1.0, "output": 5.0}, "fake-2": {"input": 1.0, "output": 5.0}},
    }  # fmt: skip
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg))
    design = yaml.safe_load((REPO / "designs" / "one_at_a_time_fake.yaml").read_text())
    design.update(k_r=1, k_q=1, d2_repeats=2, n_personas=3)
    design["d_cells"]["D3"] = {"model": {"provider": "fake", "snapshot": "fake-2"}}
    (tmp_path / "design.yaml").write_text(yaml.safe_dump(design))
    return tmp_path


def run(project, *args, client):
    argv = ["--config", str(project / "config.yaml"), *args]
    return main(argv, client_factory=lambda provider: client, now=lambda: "2026-10-04T00:00:00Z")


# per repeat: persona x policy cells 3 x 3 = 9 calls; D1 3 x 2 = 6; D2 3 policies
# B 9 + B' 9 + R-T 18 + Q1 9 + Q2 27 + Q3 27 + Q4 9 + D1 6 + D2 6 + D2b 9 + D3 9
EXPECTED_CALLS = 9 + 9 + 18 + 9 + 27 + 27 + 9 + 6 + 6 + 9 + 9


def test_plan_reads_one_at_a_time_design_and_counts_calls_per_cell(project, capsys):
    client = FakeModelClient()
    assert run(project, "plan", "--design", str(project / "design.yaml"), client=client) == 0
    out = capsys.readouterr().out
    assert "design: one_at_a_time (16 cells)" in out
    assert f"calls (all configs, before dedupe): {EXPECTED_CALLS}" in out
    assert f"jobs to submit: {EXPECTED_CALLS}" in out
    assert "  B: 9 calls (9 per repeat x 1), 18 ratings, estimated $" in out
    assert "  D1: 6 calls (6 per repeat x 1), 18 ratings" in out
    assert "  D2: 6 calls (3 per repeat x 2), 12 ratings" in out
    assert client.submitted_batches == []


def test_fake_submit_and_collect_store_validated_rows(project, capsys):
    client = FakeModelClient()
    design = ["--design", str(project / "design.yaml")]
    assert run(project, "submit", "--confirm", *design, client=client) == 0
    assert run(project, "collect", client=client) == 0
    store = JsonlResultStore(project / "raw.jsonl")
    rows = list(store.iter_rows())
    assert len(rows) == EXPECTED_CALLS and {r.status for r in rows} == {"ok"}
    ratings, ok, total = ratings_from_store(store)
    assert ok == total == EXPECTED_CALLS
    # every persona x policy call gives 2 criterion ratings, every D1 call 3 policy ratings
    assert len(ratings) == (EXPECTED_CALLS - 6) * 2 + 6 * 3
    cells = {RenderedJob.from_dict(r.request).cell_id for r in rows}
    assert len(cells) == 16
    q1 = [r for r in rows if r.request["cell_id"] == "Q1"]
    assert q1 and all(names_found(r.request["prompt"]) == [] for r in q1)
    capsys.readouterr()
    run(project, "plan", *design, client=client)
    assert "jobs to submit: 0" in capsys.readouterr().out  # reruns skip finished jobs


def test_jobs_are_submitted_in_the_recorded_run_order_with_b_prime_last(project):
    client = FakeModelClient()
    run(project, "submit", "--confirm", "--design", str(project / "design.yaml"), client=client)
    (batch,) = client._batches.values()
    cells = [j.cell_id for j in batch]
    assert cells[-9:] == ["B'"] * 9 and "B'" not in cells[:-9]
    assert cells[:9] != ["B"] * 9 or cells[9:18] != ["B'"] * 9  # interleaved, not cell by cell


def test_packets_must_cover_every_policy(tmp_path):
    (tmp_path / "ubi.md").write_text("x")
    with pytest.raises(ValueError, match="packets"):
        load_packets(tmp_path, ("ubi", "nit"))


# --- real study inputs --------------------------------------------------------------------


@pytest.fixture(scope="module")
def study():
    config = load_config(REPO / "config.yaml")
    cells = {
        c.cell_id: c
        for c in expand_cells(load_oat_design(REPO / "designs" / "one_at_a_time_fake.yaml"))
    }
    return load_study_materials(config), cells


def test_real_packets_are_wired_one_per_policy(study):
    m, _ = study
    assert set(m.packets) == {"wikipedia"}
    assert set(m.packets["wikipedia"]) == {p.id for p in m.policies}
    assert m.packets["wikipedia"]["ubi"].startswith("# Evidence packet: Universal Basic Income")


def test_real_counts_561_per_baseline_repeat_663_per_joint_repeat_11_per_d2_repeat(study):
    m, cells = study
    per_repeat = {cid: count_cell_calls(c, m).calls // c.repeats for cid, c in cells.items()}
    assert per_repeat["B"] == 561 and per_repeat["Q1"] == 561 and per_repeat["D2b"] == 561
    assert per_repeat["D1"] == 663 and per_repeat["D2"] == 11
    assert len(jobs_for_cell_repeat(cells["B"], 0, m)) == 561
    assert len(jobs_for_cell_repeat(cells["D1"], 0, m)) == 663
    # prereg s5 full plan: 561 (k_R + 2) + 7,395 k_Q at the example's k_R = 5, k_Q = 3
    assert sum(count_cell_calls(c, m).calls for c in cells.values()) == 26112


def test_real_q1_prompts_show_no_policy_name_in_prompt_or_packet(study):
    m, cells = study
    jobs = jobs_for_cell_repeat(cells["Q1"], 0, m)
    for j in jobs[:11]:  # one persona, all 11 policies (the packet is the same for every persona)
        assert names_found(j.prompt) == [], (j.policy_ids, names_found(j.prompt))


def test_every_real_packet_is_denamed_completely(study):
    from llm_panel.domain.denaming import denamed_packet
    from llm_panel.domain.study_prompt import neutral_codes

    m, _ = study
    codes = neutral_codes(m.policies)
    for pid, text in m.packets["wikipedia"].items():
        assert names_found(text), pid  # the rule has something to remove
        out = denamed_packet(text, pid, m.policies, codes)
        assert names_found(out) == [], (pid, names_found(out))
        assert out.splitlines()[0] == f"# Evidence packet: {codes[pid]}"


# --- --max-jobs (TASK-12): the first N jobs still to submit, in run order -----------------


def _submitted(client):
    return [j for batch in client._batches.values() for j in batch]


def test_max_jobs_submits_the_first_n_jobs_in_run_order(project):
    design = ["--design", str(project / "design.yaml")]
    full = FakeModelClient()
    run(project, "submit", "--confirm", *design, client=full)
    order = [j.job_id for j in _submitted(full)]
    (project / "raw.jsonl").unlink(missing_ok=True)
    (project / "ledger.jsonl").unlink()
    some = FakeModelClient()
    assert run(project, "submit", "--confirm", "--max-jobs", "5", *design, client=some) == 0
    assert [j.job_id for j in _submitted(some)] == order[:5]
    # staged runs: the next call takes the next 5 (the first 5 are in flight)
    assert run(project, "submit", "--confirm", "--max-jobs", "5", *design, client=some) == 0
    assert [j.job_id for j in _submitted(some)] == order[:10]


def test_max_jobs_plan_counts_and_costs_only_the_selected_jobs(project, capsys):
    design = ["--design", str(project / "design.yaml")]
    client = FakeModelClient()
    run(project, "plan", *design, client=client)
    full = capsys.readouterr().out
    assert run(project, "plan", "--max-jobs", "4", *design, client=client) == 0
    out = capsys.readouterr().out
    assert "jobs to submit: 4" in out
    assert f"selected by --max-jobs 4: first 4 of {EXPECTED_CALLS} jobs in run order" in out

    def total(text):
        return float(text.split("estimated total: $")[1].split()[0])

    assert 0 < total(out) < total(full)
    assert client.submitted_batches == []


def test_max_jobs_spend_ceiling_checks_only_the_selected_jobs(project, capsys):
    design = ["--design", str(project / "design.yaml")]
    client = FakeModelClient()
    run(project, "plan", "--max-jobs", "2", *design, client=client)
    two = float(capsys.readouterr().out.split("estimated total: $")[1].split()[0])
    cfg = yaml.safe_load((project / "config.yaml").read_text())
    cfg["max_spend_usd"] = two * 1.5  # room for the 2 selected jobs, not for the full design
    (project / "config.yaml").write_text(yaml.safe_dump(cfg))
    assert run(project, "submit", "--confirm", *design, client=client) == 2
    assert run(project, "submit", "--confirm", "--max-jobs", "2", *design, client=client) == 0
    assert len(_submitted(client)) == 2


@pytest.mark.parametrize("bad", ["0", "-1", "x"])
def test_max_jobs_must_be_a_positive_integer(project, bad):
    with pytest.raises(SystemExit):
        run(project, "plan", "--max-jobs", bad, "--design", str(project / "design.yaml"),
            client=FakeModelClient())  # fmt: skip


# --- --cells: run one unit of the design (prereg s8 priority order) -------------------------


DRIFT = "B'"


def _cell_counts(out):
    return dict(
        (ln.split(":")[0].strip(), int(ln.split(":")[1].split()[0]))
        for ln in out.splitlines()
        if ln.startswith("  ") and "calls (" in ln
    )


def test_cells_plan_covers_only_the_named_cells_and_costs_less(project, capsys):
    design = ["--design", str(project / "design.yaml")]
    client = FakeModelClient()
    run(project, "plan", *design, client=client)
    full = capsys.readouterr().out
    assert run(project, "plan", "--cells", "B,B'", *design, client=client) == 0
    out = capsys.readouterr().out
    assert set(_cell_counts(out)) == {"B", "B'"}
    assert _cell_counts(out)["B"] == _cell_counts(full)["B"]
    counts = _cell_counts(out)
    assert f"jobs to submit: {counts['B'] + counts[DRIFT]}" in out


def test_cells_submit_sends_only_those_jobs_in_the_recorded_relative_order(project):
    design = ["--design", str(project / "design.yaml")]
    full = FakeModelClient()
    run(project, "submit", "--confirm", *design, client=full)
    order = [(j.cell_id, j.job_id) for j in _submitted(full)]
    (project / "raw.jsonl").unlink(missing_ok=True)
    (project / "ledger.jsonl").unlink()
    some = FakeModelClient()
    assert run(project, "submit", "--confirm", "--cells", "B,B'", *design, client=some) == 0
    expected = [j for c, j in order if c in ("B", "B'")]
    assert [j.job_id for j in _submitted(some)] == expected
    assert {j.cell_id for j in _submitted(some)} == {"B", "B'"}


def test_cells_combines_with_max_jobs_and_rejects_unknown_cells(project):
    design = ["--design", str(project / "design.yaml")]
    client = FakeModelClient()
    assert run(project, "submit", "--confirm", "--cells", "B", "--max-jobs", "2", *design,
               client=client) == 0  # fmt: skip
    assert len(_submitted(client)) == 2
    assert {j.cell_id for j in _submitted(client)} == {"B"}
    with pytest.raises(SystemExit):
        run(project, "plan", "--cells", "B,nope", *design, client=client)
