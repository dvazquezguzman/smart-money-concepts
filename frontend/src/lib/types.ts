export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CandlesResponse {
  symbol: string;
  timeframe: string;
  count: number;
  candles: Candle[];
  loading?: boolean;
}

export interface IndicatorDict {
  FVG: (number | null)[];
  Top: (number | null)[];
  Bottom: (number | null)[];
  MitigatedIndex: (number | null)[];
}

export interface OBDict {
  OB: (number | null)[];
  Top: (number | null)[];
  Bottom: (number | null)[];
  Percentage: (number | null)[];
  MitigatedIndex: (number | null)[];
}

export interface BOSCHoCHDict {
  BOS: (number | null)[];
  CHOCH: (number | null)[];
}

export interface LiquidityDict {
  Liquidity: (number | null)[];
  Level: (number | null)[];
}

export interface SwingDict {
  High: (number | null)[];
  Low: (number | null)[];
  HighLevel: (number | null)[];
  LowLevel: (number | null)[];
}

export interface RetracementDict {
  Retracement: (number | null)[];
  Top: (number | null)[];
  Bottom: (number | null)[];
}

export interface SessionDict {
  Session: (number | null)[];
  Top: (number | null)[];
  Bottom: (number | null)[];
}

export interface PreviousHighLowDict {
  PreviousHigh: (number | null)[];
  PreviousLow: (number | null)[];
  PreviousHighLevel: (number | null)[];
  PreviousLowLevel: (number | null)[];
}

export interface IndicatorsResponse {
  symbol: string;
  timeframe: string;
  error?: string;
  fvg?: IndicatorDict;
  ob?: OBDict;
  bos_choch?: BOSCHoCHDict;
  liquidity?: LiquidityDict;
  swings?: SwingDict;
  retracements?: RetracementDict;
  sessions_london?: SessionDict;
  previous_high_low?: PreviousHighLowDict;
  candle_count?: number;
}

export interface FVGZone {
  startIndex: number;
  endIndex: number;
  top: number;
  bottom: number;
  type: "bullish" | "bearish";
}

export interface OBZone {
  startIndex: number;
  endIndex: number;
  top: number;
  bottom: number;
  type: "bullish" | "bearish";
}

export interface LiquidityLevel {
  index: number;
  level: number;
  type: "buy" | "sell";
}

export interface BOSCHoCHPoint {
  index: number;
  type: "BOS" | "CHOCH";
}

export interface SwingPoint {
  index: number;
  level: number;
  type: "high" | "low";
}

export interface ComboResult {
  params: Record<string, unknown>;
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

export interface OptimizerResult {
  strategy_name: string;
  symbol: string;
  timeframe: string;
  total_combos: number;
  combos_run: number;
  results: ComboResult[];
}

export type Timeframe = "1m" | "5m" | "15m" | "1H" | "4H";

export const TIMEFRAMES: Timeframe[] = ["1m", "5m", "15m", "1H", "4H"];

export const SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"];
