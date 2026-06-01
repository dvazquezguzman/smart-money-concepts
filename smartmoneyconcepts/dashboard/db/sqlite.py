import sqlite3
from datetime import datetime
from typing import Optional

from .base import (
    BaseCandleRepository,
    BaseConfigRepository,
    BaseStrategyRepository,
    BaseTradeRepository,
    Candle,
)
from .schema import (
    ALL_TABLES,
    raw_table,
    agg_table,
    raw_ddl,
    agg_ddl,
)


class SQLiteCandleRepository(BaseCandleRepository):
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def create_tables(self):
        for ddl in ALL_TABLES:
            self.db.executescript(ddl)
        self.db.commit()

    def create_tables_for_symbol(self, symbol: str):
        self.db.executescript(raw_ddl(symbol))
        self.db.executescript(agg_ddl(symbol))
        self.db.commit()

    def _table_for(self, symbol: str, timeframe: str) -> str:
        return raw_table(symbol) if timeframe == "1m" else agg_table(symbol)

    def save_candles(self, candles: list[Candle]):
        by_table: dict[str, list[Candle]] = {}
        for c in candles:
            tbl = self._table_for(c.symbol, c.timeframe)
            by_table.setdefault(tbl, []).append(c)

        for tbl, group in by_table.items():
            is_agg = tbl.startswith("agg_")
            if is_agg:
                self.db.executemany(
                    f"""INSERT OR IGNORE INTO {tbl}
                       (timestamp, timeframe, open, high, low, close, volume)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    [
                        (
                            int(c.timestamp.timestamp()),
                            c.timeframe,
                            c.open,
                            c.high,
                            c.low,
                            c.close,
                            c.volume,
                        )
                        for c in group
                    ],
                )
            else:
                self.db.executemany(
                    f"""INSERT OR IGNORE INTO {tbl}
                       (timestamp, open, high, low, close, volume)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [
                        (
                            int(c.timestamp.timestamp()),
                            c.open,
                            c.high,
                            c.low,
                            c.close,
                            c.volume,
                        )
                        for c in group
                    ],
                )
        self.db.commit()

    def _row_to_candle(self, symbol: str, timeframe: str, row) -> Optional[Candle]:
        ts = row[0]
        if ts is None:
            return None
        if timeframe == "1m":
            return Candle(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(ts),
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5],
                timeframe="1m",
            )
        return Candle(
            symbol=symbol,
            timestamp=datetime.fromtimestamp(ts),
            open=row[2],
            high=row[3],
            low=row[4],
            close=row[5],
            volume=row[6],
            timeframe=timeframe,
        )

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None,
    ) -> list[Candle]:
        tbl = self._table_for(symbol, timeframe)

        if timeframe == "1m":
            if since:
                rows = self.db.execute(
                    f"SELECT timestamp, open, high, low, close, volume "
                    f"FROM {tbl} WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT ?",
                    (int(since.timestamp()), limit),
                ).fetchall()
            else:
                rows = self.db.execute(
                    f"SELECT timestamp, open, high, low, close, volume "
                    f"FROM {tbl} ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        else:
            if since:
                rows = self.db.execute(
                    f"SELECT timestamp, timeframe, open, high, low, close, volume "
                    f"FROM {tbl} WHERE timeframe = ? AND timestamp >= ? "
                    f"ORDER BY timestamp DESC LIMIT ?",
                    (timeframe, int(since.timestamp()), limit),
                ).fetchall()
            else:
                rows = self.db.execute(
                    f"SELECT timestamp, timeframe, open, high, low, close, volume "
                    f"FROM {tbl} WHERE timeframe = ? "
                    f"ORDER BY timestamp DESC LIMIT ?",
                    (timeframe, limit),
                ).fetchall()

        return [
            c
            for r in reversed(rows)
            if (c := self._row_to_candle(symbol, timeframe, r)) is not None
        ]

    def get_last_candle(self, symbol: str, timeframe: str) -> Optional[Candle]:
        tbl = self._table_for(symbol, timeframe)
        if timeframe == "1m":
            row = self.db.execute(
                f"SELECT timestamp, open, high, low, close, volume "
                f"FROM {tbl} ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
        else:
            row = self.db.execute(
                f"SELECT timestamp, timeframe, open, high, low, close, volume "
                f"FROM {tbl} WHERE timeframe = ? ORDER BY timestamp DESC LIMIT 1",
                (timeframe,),
            ).fetchone()
        return self._row_to_candle(symbol, timeframe, row) if row else None

    def delete_duplicates(self, symbol: str, timeframe: str):
        tbl = self._table_for(symbol, timeframe)
        self.db.execute(
            f"DELETE FROM {tbl} WHERE rowid NOT IN ("
            f"  SELECT MIN(rowid) FROM {tbl} GROUP BY timestamp"
            f")"
        )
        self.db.commit()


class SQLiteStrategyRepository(BaseStrategyRepository):
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def save_strategy(self, name: str, definition: str):
        self.db.execute(
            """INSERT INTO strategies (name, definition) VALUES (?, ?)
               ON CONFLICT(name) DO UPDATE SET
               definition = excluded.definition,
               updated_at = strftime('%s', 'now')""",
            (name, definition),
        )
        self.db.commit()

    def get_strategy(self, strategy_id: int) -> Optional[dict]:
        row = self.db.execute(
            "SELECT id, name, definition, created_at, updated_at FROM strategies WHERE id = ?",
            (strategy_id,),
        ).fetchone()
        if row:
            return dict(
                zip(["id", "name", "definition", "created_at", "updated_at"], row)
            )
        return None

    def list_strategies(self) -> list[dict]:
        rows = self.db.execute(
            "SELECT id, name, definition, created_at, updated_at FROM strategies ORDER BY updated_at DESC"
        ).fetchall()
        return [
            dict(zip(["id", "name", "definition", "created_at", "updated_at"], r))
            for r in rows
        ]

    def delete_strategy(self, strategy_id: int):
        self.db.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
        self.db.commit()


class SQLiteTradeRepository(BaseTradeRepository):
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def save_trade(self, trade: dict):
        self.db.execute(
            """INSERT INTO trades
               (strategy_id, mode, symbol, side, entry_price, quantity, entry_index, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'open')""",
            (
                trade.get("strategy_id"),
                trade.get("mode", "paper"),
                trade["symbol"],
                trade["side"],
                trade["entry_price"],
                trade["quantity"],
                trade["entry_index"],
            ),
        )
        self.db.commit()

    def get_trades(
        self, strategy_id: Optional[int] = None, mode: str = "paper"
    ) -> list[dict]:
        if strategy_id:
            cursor = self.db.execute(
                "SELECT * FROM trades WHERE mode = ? AND strategy_id = ? ORDER BY opened_at DESC",
                (mode, strategy_id),
            )
        else:
            cursor = self.db.execute(
                "SELECT * FROM trades WHERE mode = ? ORDER BY opened_at DESC", (mode,)
            )
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_open_positions(self, mode: str = "paper") -> list[dict]:
        cursor = self.db.execute(
            "SELECT * FROM trades WHERE mode = ? AND status = 'open'", (mode,)
        )
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


class SQLiteConfigRepository(BaseConfigRepository):
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def save_config(self, key: str, value: str):
        self.db.execute(
            """INSERT INTO config (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET
               value = excluded.value,
               updated_at = strftime('%s', 'now')""",
            (key, value),
        )
        self.db.commit()

    def get_config(self, key: str) -> Optional[str]:
        row = self.db.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None
