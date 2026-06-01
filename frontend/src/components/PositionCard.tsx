interface PositionData {
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

export default function PositionCard({ pos }: { pos: PositionData }) {
  const isProfitable = pos.unrealized_pnl >= 0;
  const pnlPct =
    pos.entry_price > 0
      ? ((pos.current_price - pos.entry_price) / pos.entry_price) * 100
      : 0;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded ${
              pos.side === "buy"
                ? "bg-green-900 text-green-400"
                : "bg-red-900 text-red-400"
            }`}
          >
            {pos.side.toUpperCase()}
          </span>
          <span className="font-semibold">{pos.symbol}</span>
        </div>
        <span className="text-xs text-gray-500">{pos.strategy}</span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <div className="text-gray-500 text-xs">Qty</div>
          <div>{pos.quantity.toFixed(4)}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">Entry</div>
          <div>${pos.entry_price.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">Current</div>
          <div>${pos.current_price.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">PnL</div>
          <div className={isProfitable ? "text-green-400" : "text-red-400"}>
            ${pos.unrealized_pnl.toFixed(2)} ({pnlPct.toFixed(2)}%)
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">SL</div>
          <div>{pos.sl_price ? `$${pos.sl_price.toFixed(2)}` : "-"}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">TP</div>
          <div>{pos.tp_price ? `$${pos.tp_price.toFixed(2)}` : "-"}</div>
        </div>
      </div>
    </div>
  );
}
