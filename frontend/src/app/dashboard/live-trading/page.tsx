"use client";

import { useState, useEffect, useCallback } from "react";
import { getStrategies, getStrategy, getExchangeKeyStatus } from "@/lib/api";
import type { StrategyRecord } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface LiveSummary {
  connected: boolean;
  running: boolean;
  exchange: string;
  open_positions: number;
  kill_switch: boolean;
}

interface LivePosition {
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  sl_price: number | null;
  tp_price: number | null;
  entry_time: string;
  strategy: string;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export default function LiveTradingPage() {
  const [summary, setSummary] = useState<LiveSummary | null>(null);
  const [positions, setPositions] = useState<LivePosition[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [strategies, setStrategies] = useState<StrategyRecord[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [keysConfigured, setKeysConfigured] = useState<boolean | null>(null);

  const load = useCallback(async () => {
    try {
      const [s, p] = await Promise.all([
        fetchJson<LiveSummary>(`${API_BASE}/api/trading/live/status`),
        fetchJson<LivePosition[]>(`${API_BASE}/api/trading/live/positions`),
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
    getExchangeKeyStatus().then((s) => setKeysConfigured(s.configured)).catch(() => {});
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  const handleStart = async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const s = await getStrategy(selectedId);
      const res = await fetch(`${API_BASE}/api/trading/live/start`, {
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
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setError(null);
    try {
      await fetch(`${API_BASE}/api/trading/live/stop`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop failed");
    }
  };

  const handleKill = async () => {
    if (!confirm("Kill switch will close ALL open positions with market orders. Continue?")) return;
    setError(null);
    try {
      await fetch(`${API_BASE}/api/trading/live/kill`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Kill failed");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Live Trading</h1>
        <div className="flex items-center gap-3">
          {summary && (
            <>
              <span className="text-sm text-gray-400">{summary.exchange}</span>
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  summary.connected ? "bg-green-500" : "bg-red-500"
                }`}
                title={summary.connected ? "Connected" : "Disconnected"}
              />
              {summary.kill_switch && (
                <span className="text-xs text-red-400 font-semibold">KILLED</span>
              )}
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm mb-4">
          {error}
        </div>
      )}

      {keysConfigured === false && (
        <div className="bg-amber-900/50 border border-amber-700 text-amber-300 rounded p-3 text-sm mb-4">
          Exchange API keys not configured.{" "}
          <a href="/dashboard/config" className="underline hover:text-amber-200">
            Configure in Settings
          </a>
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard label="Exchange" value={summary.exchange} />
          <StatCard
            label="Status"
            value={summary.connected ? "Connected" : "Disconnected"}
            color={summary.connected ? "text-green-400" : "text-red-400"}
          />
          <StatCard
            label="Engine"
            value={summary.running ? "Running" : "Stopped"}
            color={summary.running ? "text-green-400" : "text-gray-400"}
          />
          <StatCard label="Open Positions" value={String(summary.open_positions)} />
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded p-4 mb-6">
        <h2 className="text-lg font-semibold mb-3">Controls</h2>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">Strategy</label>
            <select
              value={selectedId ?? ""}
              onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">Select a strategy...</option>
              {strategies.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          {summary?.running ? (
            <button
              onClick={handleStop}
              className="px-4 py-2 text-sm font-medium bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
            >
              Stop
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={!selectedId || loading || keysConfigured === false}
              className="px-4 py-2 text-sm font-medium bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {loading ? "Starting..." : "Start"}
            </button>
          )}
          {summary?.running && (
            <button
              onClick={handleKill}
              className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Kill
            </button>
          )}
        </div>
      </div>

      {positions.length > 0 ? (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Open Positions ({positions.length})</h2>
          {positions.map((p, i) => {
            const isProfitable = p.current_price >= p.entry_price;
            return (
              <div key={i} className="bg-gray-900 border border-gray-800 rounded p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    p.side === "buy" ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"
                  }`}>
                    {p.side.toUpperCase()}
                  </span>
                  <span className="font-semibold">{p.symbol}</span>
                  <span className="text-xs text-gray-500 ml-auto">{p.strategy}</span>
                </div>
                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div><span className="text-gray-500 text-xs block">Qty</span>{p.quantity.toFixed(4)}</div>
                  <div><span className="text-gray-500 text-xs block">Entry</span>${p.entry_price.toFixed(2)}</div>
                  <div><span className="text-gray-500 text-xs block">Current</span>${p.current_price.toFixed(2)}</div>
                  <div><span className="text-gray-500 text-xs block">SL/TP</span>{p.sl_price ? `$${p.sl_price.toFixed(2)}` : "-"} / {p.tp_price ? `$${p.tp_price.toFixed(2)}` : "-"}</div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-gray-500 text-sm">
          No open positions. Set up exchange keys in Config first, then start a strategy.
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-bold ${color || "text-white"}`}>{value}</div>
    </div>
  );
}
