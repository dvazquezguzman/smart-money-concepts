"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  CandlestickSeries,
  ColorType,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type IPriceLine,
  type SeriesMarker,
} from "lightweight-charts";
import type {
  Candle,
  FVGZone,
  OBZone,
  LiquidityLevel,
  BOSCHoCHPoint,
  SwingPoint,
} from "@/lib/types";

interface Props {
  candles: Candle[];
  fvgZones?: FVGZone[];
  obZones?: OBZone[];
  liquidityLevels?: LiquidityLevel[];
  bosChochPoints?: BOSCHoCHPoint[];
  swingPoints?: SwingPoint[];
  height?: number;
}

function candlesToSeries(candles: Candle[]): CandlestickData[] {
  return candles.map((c) => ({
    time: (new Date(c.timestamp).getTime() / 1000) as any,
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
  }));
}

const FVG_COLORS = {
  bullish: "rgba(38, 166, 154, 0.3)",
  bearish: "rgba(239, 83, 80, 0.3)",
};

export default function Chart({
  candles,
  fvgZones,
  obZones,
  liquidityLevels,
  bosChochPoints,
  swingPoints,
  height = 600,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);
  const aliveRef = useRef(true);

  useEffect(() => {
    aliveRef.current = true;
    return () => { aliveRef.current = false; };
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#131722" },
        textColor: "#d1d4dc",
      },
      grid: {
        vertLines: { color: "#2a2e39" },
        horzLines: { color: "#2a2e39" },
      },
      crosshair: { mode: 0 },
      timeScale: {
        borderColor: "#2a2e39",
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: "#2a2e39",
      },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderUpColor: "#26a69a",
      borderDownColor: "#ef5350",
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    return () => {
      aliveRef.current = false;
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      priceLinesRef.current = [];
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || candles.length === 0) return;
    seriesRef.current.setData(candlesToSeries(candles));
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  useEffect(() => {
    if (!aliveRef.current) return;
    const series = seriesRef.current;
    if (!series || candles.length === 0) return;

    const markers: SeriesMarker<number>[] = [];

    const candleAt = (i: number) => (i >= 0 && i < candles.length ? candles[i] : null);

    if (fvgZones) {
      for (const zone of fvgZones) {
        const c = candleAt(zone.startIndex);
        if (!c) continue;
        markers.push({
          time: (new Date(c.timestamp).getTime() / 1000) as any,
          position: zone.type === "bullish" ? "belowBar" : "aboveBar",
          shape: "arrowUp",
          color: zone.type === "bullish" ? "#26a69a" : "#ef5350",
          text: "FVG",
        });
      }
    }

    if (obZones) {
      for (const zone of obZones) {
        const c = candleAt(zone.startIndex);
        if (!c) continue;
        markers.push({
          time: (new Date(c.timestamp).getTime() / 1000) as any,
          position: zone.type === "bullish" ? "belowBar" : "aboveBar",
          shape: "square",
          color: zone.type === "bullish" ? "#26a69a" : "#ef5350",
          text: "OB",
        });
      }
    }

    if (bosChochPoints) {
      for (const point of bosChochPoints) {
        const c = candleAt(point.index);
        if (!c) continue;
        markers.push({
          time: (new Date(c.timestamp).getTime() / 1000) as any,
          position: "aboveBar",
          shape: "arrowDown",
          color: point.type === "BOS" ? "#f59e0b" : "#8b5cf6",
          text: point.type,
        });
      }
    }

    if (swingPoints) {
      for (const point of swingPoints) {
        const c = candleAt(point.index);
        if (!c) continue;
        markers.push({
          time: (new Date(c.timestamp).getTime() / 1000) as any,
          position: point.type === "high" ? "aboveBar" : "belowBar",
          shape: "circle",
          color: point.type === "high" ? "#f59e0b" : "#3b82f6",
          text: point.type === "high" ? "H" : "L",
        });
      }
    }

    const markersPlugin = createSeriesMarkers(series, markers as any);
    return () => {
      if (aliveRef.current) markersPlugin.setMarkers([]);
    };
  }, [candles, fvgZones, obZones, bosChochPoints, swingPoints]);

  useEffect(() => {
    if (!aliveRef.current) return;
    const series = seriesRef.current;
    if (!series || !liquidityLevels || liquidityLevels.length === 0) return;

    for (const line of priceLinesRef.current) {
      series.removePriceLine(line);
    }
    priceLinesRef.current = [];

    for (const level of liquidityLevels) {
      const line = series.createPriceLine({
        price: level.level,
        color: level.type === "buy" ? "#26a69a" : "#ef5350",
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: level.type === "buy" ? "Buy Liq" : "Sell Liq",
      });
      priceLinesRef.current.push(line);
    }

    return () => {
      if (!aliveRef.current) return;
      for (const line of priceLinesRef.current) {
        series.removePriceLine(line);
      }
      priceLinesRef.current = [];
    };
  }, [liquidityLevels]);

  return <div ref={containerRef} className="w-full" />;
}
