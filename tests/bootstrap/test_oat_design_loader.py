from pathlib import Path

import pytest
import yaml

from llm_panel.bootstrap.design_loader import load_oat_design
from llm_panel.domain.oat_design import ModelRef, expand_cells

EXAMPLE = Path(__file__).parents[2] / "designs" / "one_at_a_time_fake.yaml"


def write(tmp_path, data):
    p = tmp_path / "d.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def test_loads_example_into_all_prereg_cells():
    design = load_oat_design(EXAMPLE)
    assert design.baseline.model == ModelRef("fake", "fake-model-2026-01-01")
    assert design.baseline.temperature is None  # provider default
    ids = {c.cell_id for c in expand_cells(design)}
    assert {"B", "B'", "R-T0", "R-T1", "Q1", "Q2a", "Q3c", "Q4"} <= ids
    assert {"D1", "D2", "D2b", "D3"} <= ids
    assert design.order_seed == 20261004


def test_d_cells_are_optional(tmp_path):
    data = yaml.safe_load(EXAMPLE.read_text())
    del data["d_cells"]
    ids = {c.cell_id for c in expand_cells(load_oat_design(write(tmp_path, data)))}
    assert not {"D1", "D2", "D2b", "D3"} & ids


@pytest.mark.parametrize("key", ["baseline", "k_r", "k_q", "rt_temperatures", "order_seed"])
def test_missing_required_key_rejected(tmp_path, key):
    data = yaml.safe_load(EXAMPLE.read_text())
    del data[key]
    with pytest.raises(ValueError, match=key):
        load_oat_design(write(tmp_path, data))


def test_wrong_design_kind_rejected(tmp_path):
    data = yaml.safe_load(EXAMPLE.read_text())
    data["design"] = "fractional"
    with pytest.raises(ValueError, match="one_at_a_time"):
        load_oat_design(write(tmp_path, data))


def test_unknown_d_cell_key_rejected(tmp_path):
    data = yaml.safe_load(EXAMPLE.read_text())
    data["d_cells"]["D1"]["temperature"] = 0.5
    with pytest.raises(ValueError, match="temperature"):
        load_oat_design(write(tmp_path, data))
