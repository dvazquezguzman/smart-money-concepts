"use client";

import { useState, useEffect, useCallback } from "react";
import { getPaperStatus, getLiveStatus, getStrategies, getHealth } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

interface PaperStatus {
  balance: number;
  equity: number;
  realized_pnl: number;
  open_positions: number;
  running: boolean;
}

interface LiveStatus {
  connected: boolean;
  running: boolean;
  exchange: string;
  open_positions: number;
}

interface OverviewData {
  paper: PaperStatus | null;
  live: LiveStatus | null;
  strategyCount: number;
  health: { status: string } | null;
}

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const results = await Promise.allSettled([
        getPaperStatus(),
        getLiveStatus(),
        getStrategies(),
        getHealth(),
      ]);

      const allFailed = results.every((r) => r.status === "rejected");

      setData({
        paper: results[0].status === "fulfilled" ? results[0].value : null,
        live: results[1].status === "fulfilled" ? results[1].value : null,
        strategyCount:
          results[2].status === "fulfilled" ? results[2].value.length : 0,
        health: results[3].status === "fulfilled" ? results[3].value : null,
      });
      setError(allFailed ? "Failed to fetch overview data" : null);
    } catch {
      setError("Failed to fetch overview data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Overview</h1>
        {data?.health && (
          <span className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            Server Online
          </span>
        )}
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm mb-4">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div className="grid grid-cols-5 gap-4">
          <StatCard
            label="Paper Balance"
            value={data?.paper ? `$${data.paper.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "Not connected"}
          />
          <StatCard
            label="Paper Equity"
            value={data?.paper ? `$${data.paper.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "Not connected"}
          />
          <StatCard
            label="Realized PnL"
            value={data?.paper ? formatPnl(data.paper.realized_pnl) : "Not connected"}
            color={data?.paper ? (data.paper.realized_pnl >= 0 ? "text-green-400" : "text-red-400") : undefined}
          />
          <StatCard
            label="Paper Positions"
            value={data?.paper ? String(data.paper.open_positions) : "Not connected"}
          />
          <StatCard
            label="Strategies"
            value={String(data?.strategyCount ?? 0)}
          />
        </div>
        <div className="grid grid-cols-5 gap-4">
          <StatCard
            label="Live Exchange"
            value={data?.live?.exchange ?? "Not connected"}
          />
          <StatCard
            label="Live Status"
            value={data?.live ? (data.live.connected ? "Connected" : "Disconnected") : "Not connected"}
            color={data?.live ? (data.live.connected ? "text-green-400" : "text-red-400") : undefined}
          />
          <StatCard
            label="Engine State"
            value={data?.live ? (data.live.running ? "Running" : "Stopped") : "Not connected"}
            color={data?.live ? (data.live.running ? "text-green-400" : "text-gray-400") : undefined}
          />
          <StatCard
            label="Live Positions"
            value={data?.live ? String(data.live.open_positions) : "Not connected"}
          />
          <StatCard
            label="Server Health"
            value={data?.health?.status ?? "Unavailable"}
            color={data?.health ? "text-green-400" : "text-red-400"}
          />
        </div>
      </div>

      {(!data?.paper?.running && !data?.live?.running) && (
        <p className="text-gray-500 text-sm mt-6">
          Start paper or live trading from their respective pages to see real-time performance.
        </p>
      )}
    </div>
  );
}

function formatPnl(pnl: number): string {
  const sign = pnl >= 0 ? "+" : "";
  return `${sign}$${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-bold ${color || "text-white"}`}>{value}</div>
    </div>
  );
}
