import type { CandlesResponse, IndicatorsResponse, Timeframe } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function getCandles(
  symbol: string,
  timeframe: Timeframe = "1m",
  limit = 200
): Promise<CandlesResponse> {
  const path = `${API_BASE}/api/candles/${encodeURIComponent(symbol)}?timeframe=${timeframe}&limit=${limit}`;
  return fetchJson<CandlesResponse>(path);
}

export function getIndicators(
  symbol: string,
  timeframe: Timeframe = "1m",
  limit = 500
): Promise<IndicatorsResponse> {
  const path = `${API_BASE}/api/indicators/${encodeURIComponent(symbol)}?timeframe=${timeframe}&limit=${limit}`;
  return fetchJson<IndicatorsResponse>(path);
}

export function createWebSocket(symbol: string): WebSocket {
  const wsBase = API_BASE.replace(/^http/, "ws");
  return new WebSocket(`${wsBase}/ws/${encodeURIComponent(symbol)}`);
}

export async function getSymbols(): Promise<string[]> {
  const data = await fetchJson<{ symbols: string[] }>(`${API_BASE}/api/config/symbols`);
  return data.symbols;
}

export async function addSymbol(symbol: string): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/config/symbols?symbol=${encodeURIComponent(symbol)}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to add symbol: ${res.status}`);
  const data = await res.json();
  return data.symbols;
}

export async function removeSymbol(symbol: string): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/config/symbols?symbol=${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to remove symbol: ${res.status}`);
  const data = await res.json();
  return data.symbols;
}

export interface StrategyRecord {
  id: number;
  name: string;
  definition: string;
  created_at: number;
  updated_at: number;
}

export async function getStrategies(): Promise<StrategyRecord[]> {
  return fetchJson<StrategyRecord[]>(`${API_BASE}/api/strategies`);
}

export async function getStrategy(id: number): Promise<StrategyRecord> {
  return fetchJson<StrategyRecord>(`${API_BASE}/api/strategies/${id}`);
}

export async function createStrategy(name: string, definition: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/strategies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, definition }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Failed to create strategy: ${res.status}`);
  }
}

export async function updateStrategy(id: number, definition: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/strategies/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ definition }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Failed to update strategy: ${res.status}`);
  }
}

export async function deleteStrategy(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/strategies/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete strategy: ${res.status}`);
}

export interface TemplateInfo {
  name: string;
  file: string;
}

export async function getTemplates(): Promise<TemplateInfo[]> {
  return fetchJson<TemplateInfo[]>(`${API_BASE}/api/strategies/templates/list`);
}

export async function getTemplate(file: string): Promise<{ name: string; definition: string }> {
  return fetchJson(`${API_BASE}/api/strategies/templates/${encodeURIComponent(file)}`);
}

export interface BacktestResult {
  strategy: string;
  symbol: string;
  timeframe: string;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  total_pnl: number;
  profit_factor: number;
  max_drawdown: number;
  sharpe: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  avg_bars_held: number;
}

export async function runBacktest(
  definition: string,
  start: string,
  end: string,
  symbol: string,
  initialCapital = 10000
): Promise<BacktestResult> {
  const res = await fetch(`${API_BASE}/api/strategies/backtest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ definition, start, end, symbol, initial_capital: initialCapital }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Backtest failed: ${res.status}`);
  }
  return res.json();
}
