"""P0.2 acceptance — FidelityConfig round-trips; unknown keys rejected."""

import dataclasses

import pytest

from tatkal_sim.config import FidelityConfig


def test_defaults_are_all_on():
    cfg = FidelityConfig()
    assert all(getattr(cfg, f.name) for f in dataclasses.fields(cfg))
    assert len(dataclasses.fields(cfg)) == 10  # exactly the ten R3 items


def test_json_round_trip():
    cfg = FidelityConfig(retries_enabled=False, bot_cohort=False)
    assert FidelityConfig.from_json(cfg.to_json()) == cfg


def test_json_is_deterministic():
    assert FidelityConfig().to_json() == FidelityConfig().to_json()


def test_unknown_keys_rejected():
    bad = '{"open_loop_arrivals": true, "warp_drive": true}'
    with pytest.raises(ValueError, match="warp_drive"):
        FidelityConfig.from_json(bad)


def test_enabled_toggles_reflect_state():
    cfg = FidelityConfig(wasted_work=False)
    names = cfg.enabled_toggles()
    assert "wasted_work" not in names
    assert "atomic_inventory" in names
    assert len(names) == 9
