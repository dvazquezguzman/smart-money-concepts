from __future__ import annotations

from pathlib import Path

import pytest

from app.config import AppConfig, load_config


def test_load_config_from_yaml(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
        data_dir: ./data
        exchange: binance
        poll_interval_seconds: 5
        risk:
          daily_loss_limit_quote: 100.0
          max_open_positions: 3
          max_trades_per_day: 20
          symbol_allowlist: ["BTC/USDT"]
        paper:
          starting_balance_quote: 1000.0
          fee_rate: 0.001
          slippage_bps: 2
        """
    )
    cfg = load_config(cfg_path)
    assert isinstance(cfg, AppConfig)
    assert cfg.exchange == "binance"
    assert cfg.poll_interval_seconds == 5
    assert cfg.risk.daily_loss_limit_quote == 100.0
    assert cfg.risk.symbol_allowlist == ["BTC/USDT"]
    assert cfg.paper.starting_balance_quote == 1000.0
    assert cfg.paper.fee_rate == 0.001
    assert cfg.paper.slippage_bps == 2


def test_missing_required_field_raises(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("exchange: binance\n")
    with pytest.raises(ValueError, match="risk"):
        load_config(cfg_path)
