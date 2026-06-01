"use client";

import { useState, useEffect, useCallback } from "react";
import type { StrategyRecord, BacktestResult } from "@/lib/api";
import {
  getStrategies,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  getTemplates,
  getTemplate,
  runBacktest,
} from "@/lib/api";
import { SYMBOLS } from "@/lib/types";

type Tab = "list" | "create" | "backtest";

export default function StrategiesPage() {
  const [tab, setTab] = useState<Tab>("list");
  const [strategies, setStrategies] = useState<StrategyRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStrategies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await getStrategies();
      setStrategies(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load strategies");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStrategies();
  }, [loadStrategies]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Strategies</h1>
        <div className="flex gap-2">
          <TabButton active={tab === "list"} onClick={() => setTab("list")}>
            List
          </TabButton>
          <TabButton active={tab === "create"} onClick={() => setTab("create")}>
            New Strategy
          </TabButton>
          <TabButton active={tab === "backtest"} onClick={() => setTab("backtest")}>
            Backtest
          </TabButton>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm mb-4">
          {error}
        </div>
      )}

      {tab === "list" && (
        <StrategyList
          strategies={strategies}
          loading={loading}
          onDelete={async (id) => {
            try {
              await deleteStrategy(id);
              await loadStrategies();
            } catch (e) {
              setError(e instanceof Error ? e.message : "Delete failed");
            }
          }}
        />
      )}

      {tab === "create" && (
        <CreateStrategy
          onCreated={() => {
            loadStrategies();
            setTab("list");
          }}
          onError={setError}
        />
      )}

      {tab === "backtest" && (
        <BacktestPanel strategies={strategies} onError={setError} />
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-sm rounded transition-colors ${
        active
          ? "bg-blue-600 text-white"
          : "bg-gray-800 text-gray-400 hover:text-white"
      }`}
    >
      {children}
    </button>
  );
}

function StrategyList({
  strategies,
  loading,
  onDelete,
}: {
  strategies: StrategyRecord[];
  loading: boolean;
  onDelete: (id: number) => Promise<void>;
}) {
  const [deleting, setDeleting] = useState<number | null>(null);

  if (loading) {
    return <div className="text-gray-500 text-sm">Loading...</div>;
  }

  if (strategies.length === 0) {
    return (
      <div className="text-gray-500 text-sm">
        No strategies saved yet. Create one from the &quot;New Strategy&quot; tab.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {strategies.map((s) => (
        <div
          key={s.id}
          className="bg-gray-900 border border-gray-800 rounded p-4"
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">{s.name}</h3>
            <button
              onClick={async () => {
                setDeleting(s.id);
                await onDelete(s.id);
                setDeleting(null);
              }}
              disabled={deleting === s.id}
              className="text-xs text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
            >
              {deleting === s.id ? "Deleting..." : "Delete"}
            </button>
          </div>
          <pre className="text-xs text-gray-400 overflow-x-auto max-h-32">
            {s.definition}
          </pre>
        </div>
      ))}
    </div>
  );
}

function CreateStrategy({
  onCreated,
  onError,
}: {
  onCreated: () => void;
  onError: (e: string | null) => void;
}) {
  const [name, setName] = useState("");
  const [definition, setDefinition] = useState("");
  const [templates, setTemplates] = useState<{ name: string; file: string }[]>(
    []
  );
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getTemplates()
      .then(setTemplates)
      .catch(() => {});
  }, []);

  const loadTemplate = async (file: string) => {
    try {
      const t = await getTemplate(file);
      setDefinition(t.definition);
      setName(t.name);
    } catch {
      onError("Failed to load template");
    }
  };

  const handleSave = async () => {
    if (!name.trim() || !definition.trim()) {
      onError("Name and definition are required");
      return;
    }
    setSaving(true);
    onError(null);
    try {
      await createStrategy(name.trim(), definition.trim());
      onCreated();
    } catch (e) {
      onError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Load Template
        </label>
        <div className="flex gap-2 flex-wrap">
          {templates.map((t) => (
            <button
              key={t.file}
              onClick={() => loadTemplate(t.file)}
              className="px-3 py-1 text-xs bg-gray-800 text-gray-300 rounded hover:bg-gray-700 transition-colors"
            >
              {t.name}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Strategy Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. My ICT Strategy"
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-400 mb-1">
          YAML Definition
        </label>
        <textarea
          value={definition}
          onChange={(e) => setDefinition(e.target.value)}
          rows={16}
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white font-mono placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save Strategy"}
      </button>
    </div>
  );
}

function BacktestPanel({
  strategies,
  onError,
}: {
  strategies: StrategyRecord[];
  onError: (e: string | null) => void;
}) {
  const [selectedId, setSelectedId] = useState<number | "custom">("custom");
  const [definition, setDefinition] = useState("");
  const [symbol, setSymbol] = useState("BTC/USDT");
  const [start, setStart] = useState("2026-01-01");
  const [end, setEnd] = useState("2026-05-01");
  const [capital, setCapital] = useState(10000);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);

  useEffect(() => {
    if (selectedId !== "custom") {
      const s = strategies.find((s) => s.id === selectedId);
      if (s) setDefinition(s.definition);
    }
  }, [selectedId, strategies]);

  const handleRun = async () => {
    if (!definition.trim()) {
      onError("Definition is required");
      return;
    }
    setRunning(true);
    onError(null);
    setResult(null);
    try {
      const r = await runBacktest(definition, `${start}T00:00:00`, `${end}T23:59:59`, symbol, capital);
      setResult(r);
    } catch (e) {
      onError(e instanceof Error ? e.message : "Backtest failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Strategy
        </label>
        <select
          value={selectedId}
          onChange={(e) =>
            setSelectedId(e.target.value === "custom" ? "custom" : Number(e.target.value))
          }
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
        >
          <option value="custom">Custom (paste below)</option>
          {strategies.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            Symbol
          </label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            Initial Capital
          </label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(Number(e.target.value))}
            min={100}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-400 mb-1">
          YAML Definition
        </label>
        <textarea
          value={definition}
          onChange={(e) => setDefinition(e.target.value)}
          rows={10}
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white font-mono placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      <button
        onClick={handleRun}
        disabled={running}
        className="px-4 py-2 text-sm font-medium bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
      >
        {running ? "Running..." : "Run Backtest"}
      </button>

      {result && <BacktestResultDisplay result={result} />}
    </div>
  );
}

function BacktestResultDisplay({ result }: { result: BacktestResult }) {
  const metrics = [
    { label: "Total Trades", value: result.total_trades },
    { label: "Wins", value: result.wins },
    { label: "Losses", value: result.losses },
    { label: "Win Rate", value: `${(result.win_rate * 100).toFixed(1)}%` },
    { label: "Total PnL", value: `$${result.total_pnl.toFixed(2)}`, color: result.total_pnl >= 0 ? "text-green-400" : "text-red-400" },
    { label: "Profit Factor", value: result.profit_factor === Infinity ? "∞" : result.profit_factor.toFixed(2) },
    { label: "Max Drawdown", value: `${(result.max_drawdown * 100).toFixed(1)}%` },
    { label: "Sharpe", value: result.sharpe.toFixed(2) },
    { label: "Avg Win", value: `$${result.avg_win.toFixed(2)}` },
    { label: "Avg Loss", value: `$${result.avg_loss.toFixed(2)}` },
    { label: "Largest Win", value: `$${result.largest_win.toFixed(2)}` },
    { label: "Largest Loss", value: `$${result.largest_loss.toFixed(2)}` },
    { label: "Avg Bars Held", value: result.avg_bars_held.toFixed(1) },
  ];

  return (
    <div className="mt-6 bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="font-semibold mb-3">Backtest Results</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {metrics.map((m) => (
          <div key={m.label} className="bg-gray-800 rounded p-3">
            <div className="text-xs text-gray-500 mb-1">{m.label}</div>
            <div className={`text-lg font-bold ${m.color || "text-white"}`}>
              {m.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
