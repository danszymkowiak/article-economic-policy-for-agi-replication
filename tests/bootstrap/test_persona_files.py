import csv
import hashlib
from pathlib import Path

import yaml

from llm_panel.bootstrap.cli import main
from llm_panel.bootstrap.inputs_loader import load_inputs, load_provenance


def _inputs(tmp_path):
    (tmp_path / "policies.yaml").write_text(
        yaml.safe_dump([{"id": "p1", "name": "P", "description": "d", "blinded_description": "b"}])
    )
    (tmp_path / "criteria.yaml").write_text(
        yaml.safe_dump([{"id": "c1", "name": "C", "description": "d", "group": "g"}])
    )
    return tmp_path


def test_build_personas_synthetic_writes_loadable_file_with_provenance(tmp_path, capsys):
    out = _inputs(tmp_path)
    cfg = tmp_path / "config.yaml"
    cfg.write_text("max_spend_usd: 1\n")
    code = main(["--config", str(cfg), "build-personas", "synthetic", "--n", "51", "--seed", "7",
                 "--out", str(out)])  # fmt: skip
    assert code == 0
    inputs = load_inputs(out)
    assert len(inputs.personas["reconstructed"]) == 51
    assert inputs.personas["reconstructed"][0].description.startswith("Your traits: {")
    prov = load_provenance(out)["reconstructed"]
    assert prov["stand_in"] is True and prov["seed"] == 7


def test_build_personas_igm_hashes_the_input_file_and_records_it(tmp_path):
    out = _inputs(tmp_path)
    src = tmp_path / "igm_us.csv"
    with src.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["respondent", "country", "q_ubi"])
        w.writeheader()
        w.writerow({"respondent": "r1", "country": "United States", "q_ubi": "Agree"})
    cfg = tmp_path / "config.yaml"
    cfg.write_text("max_spend_usd: 1\n")
    code = main(["--config", str(cfg), "build-personas", "igm", "--records", str(src),
                 "--source", "igm_us", "--origin", "IGM Forum US panel",
                 "--retrieved", "2026-10-04", "--out", str(out)])  # fmt: skip
    assert code == 0
    prov = load_provenance(out)["igm_us"]
    assert prov["input_sha256"] == hashlib.sha256(src.read_bytes()).hexdigest()
    assert prov["stand_in"] is False
    assert load_inputs(out).personas["igm_us"][0].id == "igm_us_01"


def test_loader_still_reads_plain_list_persona_files(tmp_path):
    out = _inputs(tmp_path)
    (out / "personas").mkdir()
    (out / "personas" / "old.yaml").write_text(yaml.safe_dump([{"id": "a", "description": "x"}]))
    assert load_inputs(out).personas["old"][0].id == "a"
    assert "old" not in load_provenance(out)


def test_build_personas_refuses_to_overwrite_an_existing_source(tmp_path, capsys):
    out = _inputs(tmp_path)
    cfg = tmp_path / "config.yaml"
    cfg.write_text("max_spend_usd: 1\n")
    args = ["--config", str(cfg), "build-personas", "synthetic", "--n", "5", "--seed", "1",
            "--out", str(out)]  # fmt: skip
    assert main(args) == 0
    assert main(args) == 2
    assert "exists" in capsys.readouterr().err


def test_build_personas_igm_refuses_identifying_columns(tmp_path, capsys):
    out = _inputs(tmp_path)
    src = tmp_path / "igm.csv"
    src.write_text("respondent,name,q\nr1,Someone,Agree\n")
    cfg = tmp_path / "config.yaml"
    cfg.write_text("max_spend_usd: 1\n")
    code = main(["--config", str(cfg), "build-personas", "igm", "--records", str(src),
                 "--source", "igm_us", "--origin", "o", "--retrieved", "d",
                 "--out", str(out)])  # fmt: skip
    assert code == 2 and "identif" in capsys.readouterr().err
    assert not (out / "personas" / "igm_us.yaml").exists()


def _named_cli(tmp_path, roster, out):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("max_spend_usd: 1\n")
    return main(["--config", str(cfg), "build-personas", "named", "--roster", str(roster),
                 "--source", "named", "--retrieved", "2026-10-04", "--out", str(out)])  # fmt: skip


def test_named_builder_regenerates_the_committed_file_deterministically(tmp_path):
    roster = Path(__file__).parents[2] / "personas" / "sources" / "table7_roster.csv"
    committed = Path(__file__).parents[2] / "personas" / "named.yaml"
    out = _inputs(tmp_path)
    assert _named_cli(tmp_path, roster, out) == 0
    assert (out / "personas" / "named.yaml").read_text("utf-8") == committed.read_text("utf-8")
    doc = yaml.safe_load(committed.read_text("utf-8"))
    assert len(doc["personas"]) == 51
    assert len({p["traits"]["name"] for p in doc["personas"]}) == 51
    assert not any("Cochrane" in p["traits"]["name"] for p in doc["personas"])
    assert "Cochrane" in doc["provenance"]["notes"]
    assert doc["provenance"]["input_sha256"] == hashlib.sha256(roster.read_bytes()).hexdigest()
    assert all(set(p["traits"]) == {"name", "institution", "primary_field"}
               for p in doc["personas"])  # fmt: skip


def test_named_builder_refuses_a_short_roster(tmp_path, capsys):
    out = _inputs(tmp_path)
    src = tmp_path / "roster.csv"
    src.write_text("name,institution,primary_field\nA,B,C\n", "utf-8")
    assert _named_cli(tmp_path, src, out) == 2
    assert "51" in capsys.readouterr().err
    assert not (out / "personas" / "named.yaml").exists()
