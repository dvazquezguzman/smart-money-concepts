"use client";

import { useState, useEffect, useCallback } from "react";
import { getPaperHistory, getLiveHistory } from "@/lib/api";

interface TradeRecord {
  id: number;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number | null;
  quantity: number;
  pnl: number | null;
  exit_reason: string | null;
  opened_at: string;
  closed_at: string | null;
  status: string;
}

type Tab = "paper" | "live";

export default function HistoryPage() {
  const [tab, setTab] = useState<Tab>("paper");
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await (tab === "paper" ? getPaperHistory() : getLiveHistory());
      setTrades(data);
    } catch {
      setError("Failed to load trade history");
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">History</h1>

      <div className="flex gap-1 mb-4">
        <TabButton active={tab === "paper"} onClick={() => setTab("paper")}>
          Paper
        </TabButton>
        <TabButton active={tab === "live"} onClick={() => setTab("live")}>
          Live
        </TabButton>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : trades.length === 0 ? (
        <div className="text-gray-500 text-sm py-12 text-center">
          No trades yet.
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase">
                <th className="text-left px-4 py-3 font-medium">Symbol</th>
                <th className="text-left px-4 py-3 font-medium">Side</th>
                <th className="text-right px-4 py-3 font-medium">Entry</th>
                <th className="text-right px-4 py-3 font-medium">Exit</th>
                <th className="text-right px-4 py-3 font-medium">Qty</th>
                <th className="text-right px-4 py-3 font-medium">PnL</th>
                <th className="text-left px-4 py-3 font-medium">Exit Reason</th>
                <th className="text-left px-4 py-3 font-medium">Opened At</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{t.symbol}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                      t.side === "buy" ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"
                    }`}>
                      {t.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">${t.entry_price.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right">
                    {t.exit_price ? `$${t.exit_price.toFixed(2)}` : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">{t.quantity.toFixed(4)}</td>
                  <td className={`px-4 py-3 text-right font-medium ${
                    t.pnl !== null ? (t.pnl >= 0 ? "text-green-400" : "text-red-400") : ""
                  }`}>
                    {t.pnl !== null
                      ? `${t.pnl >= 0 ? "+" : ""}$${t.pnl.toFixed(2)}`
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-400 capitalize">
                    {t.exit_reason ? t.exit_reason.replace(/_/g, " ") : "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(t.opened_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
        active
          ? "bg-blue-600 text-white"
          : "bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700"
      }`}
    >
      {children}
    </button>
  );
}
