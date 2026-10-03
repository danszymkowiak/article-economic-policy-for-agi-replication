from pathlib import Path

import pytest
import yaml

from llm_panel.bootstrap.design_loader import load_design
from llm_panel.domain.design import to_run_specs

EXAMPLE = Path(__file__).parents[2] / "designs" / "example_fake.yaml"


def test_loads_example_design_in_both_modes(tmp_path):
    design = load_design(EXAMPLE)
    assert design.mode == "fractional" and len(to_run_specs(design)) == 4
    data = yaml.safe_load(EXAMPLE.read_text())
    data["mode"] = "full"
    full = tmp_path / "full.yaml"
    full.write_text(yaml.safe_dump(data))
    assert len(to_run_specs(load_design(full))) == 2 * 2 * 1 * 2 * 2 * 2 * 2


def test_missing_factor_rejected(tmp_path):
    data = yaml.safe_load(EXAMPLE.read_text())
    del data["factors"]["presentation_order"]
    p = tmp_path / "d.yaml"
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="presentation_order"):
        load_design(p)


def test_model_without_snapshot_rejected(tmp_path):
    data = yaml.safe_load(EXAMPLE.read_text())
    data["factors"]["model"] = [{"provider": "fake"}]
    p = tmp_path / "d.yaml"
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="snapshot"):
        load_design(p)
