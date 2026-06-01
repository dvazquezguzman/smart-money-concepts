import re

STRATEGIES_TABLE = """
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""

TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER,
    mode TEXT NOT NULL CHECK(mode IN ('paper', 'live')),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK(side IN ('buy', 'sell')),
    entry_price REAL NOT NULL,
    exit_price REAL,
    quantity REAL NOT NULL,
    entry_index INTEGER NOT NULL,
    exit_index INTEGER,
    exit_reason TEXT,
    pnl REAL,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'closed')),
    opened_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    closed_at INTEGER,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);
CREATE INDEX IF NOT EXISTS idx_trades_open ON trades(status, mode);
"""

CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""

PERFORMANCE_TABLE = """
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER,
    mode TEXT NOT NULL CHECK(mode IN ('paper', 'live')),
    equity REAL NOT NULL,
    timestamp INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);
"""

ALL_TABLES = [
    STRATEGIES_TABLE,
    TRADES_TABLE,
    CONFIG_TABLE,
    PERFORMANCE_TABLE,
]


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower())


def table_id(symbol: str) -> str:
    return _sanitize(symbol)


def raw_table(symbol: str) -> str:
    return f"raw_{table_id(symbol)}"


def agg_table(symbol: str) -> str:
    return f"agg_{table_id(symbol)}"


RAW_DDL = """
CREATE TABLE IF NOT EXISTS {table} (
    timestamp INTEGER PRIMARY KEY,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL
);
"""

AGG_DDL = """
CREATE TABLE IF NOT EXISTS {table} (
    timestamp INTEGER NOT NULL,
    timeframe TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    PRIMARY KEY (timestamp, timeframe)
);
CREATE INDEX IF NOT EXISTS idx_{table}_lookup ON {table}(timeframe, timestamp DESC);
"""


def raw_ddl(symbol: str) -> str:
    return RAW_DDL.format(table=raw_table(symbol))


def agg_ddl(symbol: str) -> str:
    return AGG_DDL.format(table=agg_table(symbol))
