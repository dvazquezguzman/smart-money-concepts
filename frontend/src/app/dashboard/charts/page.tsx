"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import SymbolTabs from "@/components/SymbolTabs";
import Chart from "@/components/Chart";
import BotStatus from "@/components/BotStatus";
import { getCandles, getIndicators } from "@/lib/api";
import { TIMEFRAMES, SYMBOLS } from "@/lib/types";
import type {
  Candle,
  Timeframe,
  FVGZone,
  OBZone,
  LiquidityLevel,
  BOSCHoCHPoint,
  SwingPoint,
  IndicatorDict,
  LiquidityDict,
  IndicatorsResponse,
} from "@/lib/types";

function extractFVGZones(data: IndicatorsResponse["fvg"]): FVGZone[] {
  if (!data) return [];
  const zones: FVGZone[] = [];
  let start: number | null = null;
  for (let i = 0; i < data.FVG.length; i++) {
    if (data.FVG[i] !== null && data.FVG[i] !== 0) {
      if (start === null) start = i;
    } else {
      if (start !== null) {
        zones.push({
          startIndex: start,
          endIndex: i - 1,
          top: data.Top[i - 1]!,
          bottom: data.Bottom[i - 1]!,
          type: data.FVG[start] === 1 ? "bullish" : "bearish",
        });
        start = null;
      }
    }
  }
  return zones;
}

function extractLiquidityLevels(data: IndicatorsResponse["liquidity"]): LiquidityLevel[] {
  if (!data) return [];
  const levels: LiquidityLevel[] = [];
  for (let i = 0; i < data.Liquidity.length; i++) {
    if (data.Liquidity[i] !== null && data.Liquidity[i] !== 0) {
      levels.push({
        index: i,
        level: data.Level[i]!,
        type: data.Liquidity[i] === 1 ? "buy" : "sell",
      });
    }
  }
  return levels;
}

export default function ChartsPage() {
  const [symbol, setSymbol] = useState(SYMBOLS[0]);
  const [timeframe, setTimeframe] = useState<Timeframe>("15m");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [fvgZones, setFvgZones] = useState<FVGZone[]>([]);
  const [obZones, setObZones] = useState<OBZone[]>([]);
  const [liquidityLevels, setLiquidityLevels] = useState<LiquidityLevel[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const candleLimit = timeframe === "1m" ? 500 : 200;
      const [candleRes, indicatorRes] = await Promise.all([
        getCandles(symbol, timeframe, candleLimit),
        getIndicators(symbol, timeframe, 500),
      ]);

      if (candleRes.loading) {
        setFetching(true);
        retryRef.current = setTimeout(loadData, 3000);
        return;
      }

      setFetching(false);

      if (indicatorRes.error) {
        setError(indicatorRes.error);
        return;
      }

      setCandles(candleRes.candles);
      setFvgZones(extractFVGZones(indicatorRes.fvg));
      setLiquidityLevels(extractLiquidityLevels(indicatorRes.liquidity));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    loadData();
    return () => {
      if (retryRef.current) clearTimeout(retryRef.current);
    };
  }, [loadData]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Charts</h1>
        <BotStatus label="Indicators" running />
      </div>

      <SymbolTabs active={symbol} onChange={setSymbol} />

      <div className="flex gap-2 mb-4">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              timeframe === tf
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {tf}
          </button>
        ))}
        <div className="ml-auto">
          <button
            onClick={loadData}
            className="px-3 py-1 text-xs font-medium bg-gray-800 text-gray-400 rounded hover:bg-gray-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm mb-4">
          {error}
        </div>
      )}

      {fetching && (
        <div className="bg-blue-900/50 border border-blue-700 text-blue-300 rounded p-3 text-sm mb-4 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Fetching market data for {symbol}...
        </div>
      )}

      <div className="relative">
        {loading && !fetching && (
          <div className="absolute inset-0 bg-gray-950/60 flex items-center justify-center z-10">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        <Chart
          candles={candles}
          fvgZones={fvgZones}
          liquidityLevels={liquidityLevels}
          height={600}
        />
      </div>
    </div>
  );
}
