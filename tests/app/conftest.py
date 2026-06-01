from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

from app import db as _db_module

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


@pytest.fixture(autouse=True)
def _dispose_engines(monkeypatch: pytest.MonkeyPatch):
    """Track every SQLAlchemy engine created by ``app.db`` during a test and
    dispose them at teardown.

    Without this, SQLAlchemy's connection pool keeps a lazy SQLite connection
    open until garbage collection, which Python 3.14 reports as a
    ``ResourceWarning``. Production code (``app.runner``) disposes the engine
    on its own shutdown path; this fixture takes the same responsibility for
    tests so individual cases don't each have to remember.

    We patch ``app.db.create_engine`` (rather than ``init_db``) because every
    test module imports ``init_db`` directly via ``from app.db import init_db``
    -- a name copied at import time -- so patching the function itself
    wouldn't reach them. ``init_db`` resolves ``create_engine`` from
    ``app.db``'s module globals at call time, which we can patch.
    """
    created = []
    real_create_engine = _db_module.create_engine

    def _tracking_create_engine(*args, **kwargs):
        engine = real_create_engine(*args, **kwargs)
        created.append(engine)
        return engine

    monkeypatch.setattr(_db_module, "create_engine", _tracking_create_engine)
    yield
    for engine in created:
        try:
            engine.dispose()
        except Exception:
            # Don't mask a test failure with a teardown error.
            pass
