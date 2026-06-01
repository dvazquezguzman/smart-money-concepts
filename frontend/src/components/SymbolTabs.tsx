"use client";

import { useState, useEffect } from "react";
import { getSymbols } from "@/lib/api";

interface Props {
  active: string;
  onChange: (symbol: string) => void;
}

export default function SymbolTabs({ active, onChange }: Props) {
  const [symbols, setSymbols] = useState<string[]>(["BTC/USDT"]);

  useEffect(() => {
    getSymbols()
      .then(setSymbols)
      .catch(() => {}); // fallback to default
  }, []);

  return (
    <div className="flex gap-1 border-b border-gray-700 pb-1 mb-4 overflow-x-auto">
      {symbols.map((s) => (
        <button
          key={s}
          onClick={() => onChange(s)}
          className={`px-4 py-2 text-sm font-medium rounded-t transition-colors shrink-0 ${
            active === s
              ? "bg-gray-800 text-white border-b-2 border-blue-500"
              : "text-gray-400 hover:text-white hover:bg-gray-800"
          }`}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
