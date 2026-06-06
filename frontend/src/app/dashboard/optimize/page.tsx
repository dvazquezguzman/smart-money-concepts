"use client";

import { useState } from "react";
import type { ComboResult, OptimizerResult } from "@/lib/types";
import { runOptimization } from "@/lib/api";

const DEFAULT_YAML = `name: Optimized Strategy
timeframe: 5m
symbol: BTC/USDT
entry_conditions:
  - type: fvg_mitigation
    direction: bullish
    lookback: [5, 10, 15]
exit_conditions:
  - type: target
    value: {min: 1.5, max: 3.0, step: 0.5}
  - type: stop_loss
    value: [1.0, 2.0]
risk:
  position_size_pct: 1.0
  max_positions: 1
`;

type SortKey = keyof ComboResult;

const SORT_LABELS: Record<string, string> = {
  sharpe: "Sharpe",
  total_pnl: "PnL",
  win_rate: "Win Rate",
  profit_factor: "Profit Factor",
  max_drawdown: "Max DD",
  total_trades: "Trades",
};

const NUMERIC_KEYS: SortKey[] = [
  "sharpe",
  "total_pnl",
  "win_rate",
  "profit_factor",
  "max_drawdown",
  "total_trades",
  "wins",
  "losses",
  "avg_win",
  "avg_loss",
  "largest_win",
  "largest_loss",
  "avg_bars_held",
];

function formatMetric(key: string, val: number): string {
  if (key === "win_rate") return `${(val * 100).toFixed(1)}%`;
  if (key === "total_pnl" || key === "avg_win" || key === "avg_loss" || key === "largest_win" || key === "largest_loss") {
    return `$${val.toFixed(2)}`;
  }
  if (key === "profit_factor") return val === Infinity ? "inf" : val.toFixed(2);
  if (key === "max_drawdown") return `${(val * 100).toFixed(1)}%`;
  if (key === "sharpe") return val.toFixed(3);
  return String(val);
}

export default function OptimizePage() {
  const [yaml, setYaml] = useState(DEFAULT_YAML);
  const [start, setStart] = useState("2026-01-01");
  const [end, setEnd] = useState("2026-03-01");
  const [initialCapital, setInitialCapital] = useState(10000);
  const [maxCombos, setMaxCombos] = useState(500);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OptimizerResult | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("sharpe");
  const [sortAsc, setSortAsc] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await runOptimization(yaml, start, end, initialCapital, maxCombos);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Optimization failed");
    } finally {
      setLoading(false);
    }
  }

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === "max_drawdown");
    }
  }

  const sorted = result
    ? [...result.results].sort((a, b) => {
        const aVal = a[sortKey] as number;
        const bVal = b[sortKey] as number;
        return sortAsc ? aVal - bVal : bVal - aVal;
      })
    : [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Strategy Optimizer</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Left panel: Input */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Strategy YAML</label>
            <textarea
              className="w-full h-64 bg-gray-900 border border-gray-800 rounded p-3 text-sm font-mono text-gray-200 focus:outline-none focus:border-blue-500"
              value={yaml}
              onChange={(e) => setYaml(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Start Date</label>
              <input
                type="date"
                className="w-full bg-gray-900 border border-gray-800 rounded p-2 text-sm text-gray-200"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">End Date</label>
              <input
                type="date"
                className="w-full bg-gray-900 border border-gray-800 rounded p-2 text-sm text-gray-200"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Initial Capital</label>
              <input
                type="number"
                className="w-full bg-gray-900 border border-gray-800 rounded p-2 text-sm text-gray-200"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                min={100}
                step={100}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Max Combos</label>
              <input
                type="number"
                className="w-full bg-gray-900 border border-gray-800 rounded p-2 text-sm text-gray-200"
                value={maxCombos}
                onChange={(e) => setMaxCombos(Number(e.target.value))}
                min={1}
                max={5000}
              />
            </div>
          </div>

          <button
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleRun}
            disabled={loading || !yaml.trim()}
          >
            {loading ? "Running..." : "Run Optimization"}
          </button>

          {error && (
            <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Right panel: Results */}
        <div>
          {loading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-sm text-gray-400">
                  {result ? "Running combos..." : `Scanning parameter space...`}
                </p>
              </div>
            </div>
          )}

          {result && !loading && result.results.length === 0 && (
            <div className="flex items-center justify-center h-64 text-gray-500">
              No results returned
            </div>
          )}

          {result && result.results.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-gray-400">
                  {result.combos_run} of {result.total_combos} combos
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left text-gray-500 font-medium py-2 pr-2">#</th>
                      {NUMERIC_KEYS.map((key) => (
                        <th
                          key={key}
                          className="text-right text-gray-500 font-medium py-2 px-2 cursor-pointer hover:text-white"
                          onClick={() => handleSort(key)}
                        >
                          {SORT_LABELS[key] || key}
                          {sortKey === key && (
                            <span className="ml-1">{sortAsc ? "\u25B2" : "\u25BC"}</span>
                          )}
                        </th>
                      ))}
                      <th className="text-right text-gray-500 font-medium py-2 pl-2">Params</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((combo, i) => (
                      <>
                        <tr
                          key={i}
                          className="border-b border-gray-800 hover:bg-gray-800/50 cursor-pointer"
                          onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
                        >
                          <td className="py-2 pr-2 text-gray-500">{i + 1}</td>
                          {NUMERIC_KEYS.map((key) => (
                            <td
                              key={key}
                              className={`text-right py-2 px-2 ${
                                key === "total_pnl"
                                  ? (combo[key] as number) >= 0
                                    ? "text-green-400"
                                    : "text-red-400"
                                  : "text-gray-200"
                              }`}
                            >
                              {formatMetric(key, combo[key] as number)}
                            </td>
                          ))}
                          <td className="text-right py-2 pl-2">
                            <button
                              className="text-blue-400 hover:text-blue-300 text-xs"
                              onClick={(e) => {
                                e.stopPropagation();
                                setExpandedIndex(expandedIndex === i ? null : i);
                              }}
                            >
                              {expandedIndex === i ? "Hide" : "Show"}
                            </button>
                          </td>
                        </tr>
                        {expandedIndex === i && (
                          <tr key={`params-${i}`}>
                            <td colSpan={NUMERIC_KEYS.length + 2} className="bg-gray-900/50 p-3">
                              <pre className="text-xs text-gray-400 overflow-x-auto">
                                {JSON.stringify(combo.params, null, 2)}
                              </pre>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
