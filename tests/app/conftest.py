from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EURUSD_15M_CSV = REPO_ROOT / "tests" / "test_data" / "EURUSD" / "EURUSD_15M.csv"


@pytest.fixture(scope="session")
def eurusd_15m_df() -> pd.DataFrame:
    """Load the bundled EURUSD 15M test data as a lowercase-OHLCV DataFrame."""
    df = pd.read_csv(EURUSD_15M_CSV)
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df[["open", "high", "low", "close", "volume"]]


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d
