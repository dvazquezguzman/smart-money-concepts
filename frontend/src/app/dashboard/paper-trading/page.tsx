"use client";

import { useState, useEffect, useCallback } from "react";
import { getStrategies, getStrategy } from "@/lib/api";
import type { StrategyRecord } from "@/lib/api";
import PositionCard from "@/components/PositionCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Position {
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  realized_pnl: number;
  sl_price: number | null;
  tp_price: number | null;
  entry_time: string;
  strategy: string;
}

interface Summary {
  balance: number;
  open_positions: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_equity: number;
  running: boolean;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export default function PaperTradingPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [strategies, setStrategies] = useState<StrategyRecord[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [s, p] = await Promise.all([
        fetchJson<Summary>(`${API_BASE}/api/trading/paper/status`),
        fetchJson<Position[]>(`${API_BASE}/api/trading/paper/positions`),
      ]);
      setSummary(s);
      setPositions(p);
    } catch {
      // backend may not be ready
    }
  }, []);

  useEffect(() => {
    load();
    getStrategies().then(setStrategies).catch(() => {});
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  const handleStart = async () => {
    if (!selectedId) return;
    setStarting(true);
    setError(null);
    try {
      const s = await getStrategy(selectedId);
      const res = await fetch(`${API_BASE}/api/trading/paper/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ definition: s.definition }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Start failed");
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Start failed");
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    setError(null);
    try {
      await fetch(`${API_BASE}/api/trading/paper/stop`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop failed");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Paper Trading</h1>
        <div className="flex items-center gap-3">
          {summary && (
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                summary.running ? "bg-green-500" : "bg-gray-500"
              }`}
              title={summary.running ? "Running" : "Stopped"}
            />
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm mb-4">
          {error}
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard label="Balance" value={`$${summary.balance.toFixed(2)}`} />
          <StatCard
            label="Equity"
            value={`$${summary.total_equity.toFixed(2)}`}
          />
          <StatCard
            label="Realized PnL"
            value={`$${summary.realized_pnl.toFixed(2)}`}
            color={
              summary.realized_pnl >= 0 ? "text-green-400" : "text-red-400"
            }
          />
          <StatCard
            label="Unrealized PnL"
            value={`$${summary.unrealized_pnl.toFixed(2)}`}
            color={
              summary.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"
            }
          />
          <StatCard
            label="Open Positions"
            value={String(summary.open_positions)}
          />
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded p-4 mb-6">
        <h2 className="text-lg font-semibold mb-3">Controls</h2>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">
              Strategy
            </label>
            <select
              value={selectedId ?? ""}
              onChange={(e) =>
                setSelectedId(e.target.value ? Number(e.target.value) : null)
              }
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">Select a strategy...</option>
              {strategies.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          {summary?.running ? (
            <button
              onClick={handleStop}
              className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Stop
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={!selectedId || starting}
              className="px-4 py-2 text-sm font-medium bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {starting ? "Starting..." : "Start"}
            </button>
          )}
        </div>
      </div>

      {positions.length > 0 ? (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">
            Open Positions ({positions.length})
          </h2>
          {positions.map((p, i) => (
            <PositionCard key={i} pos={p} />
          ))}
        </div>
      ) : (
        <div className="text-gray-500 text-sm">
          No open positions. Start a strategy to begin paper trading.
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-bold ${color || "text-white"}`}>
        {value}
      </div>
    </div>
  );
}
