"use client";

import { useState, useEffect } from "react";
import { getSymbols, addSymbol, removeSymbol, getExchangeKeyStatus, saveExchangeKeys, testExchangeConnection } from "@/lib/api";

export default function ConfigPage() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [newSymbol, setNewSymbol] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [exchangeId, setExchangeId] = useState("binance");
  const [apiKey, setApiKey] = useState("");
  const [secret, setSecret] = useState("");
  const [passphrase, setPassphrase] = useState("");
  const [keysConfigured, setKeysConfigured] = useState(false);
  const [savingKeys, setSavingKeys] = useState(false);
  const [testingConn, setTestingConn] = useState(false);

  const loadSymbols = async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await getSymbols();
      setSymbols(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load symbols");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSymbols();
    getExchangeKeyStatus().then((s) => setKeysConfigured(s.configured)).catch(() => {});
  }, []);

  const handleAdd = async () => {
    const s = newSymbol.trim().toUpperCase();
    if (!s) return;
    setError(null);
    try {
      const updated = await addSymbol(s);
      setSymbols(updated);
      setNewSymbol("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add symbol");
    }
  };

  const handleRemove = async (symbol: string) => {
    setError(null);
    try {
      const updated = await removeSymbol(symbol);
      setSymbols(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove symbol");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Config</h1>

      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Tracked Symbols</h2>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="e.g. SOL/USDT"
            className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={handleAdd}
            className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Add
          </button>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-300 rounded p-3 text-sm mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-gray-500 text-sm">Loading...</div>
        ) : (
          <div className="space-y-2">
            {symbols.map((s) => (
              <div
                key={s}
                className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded px-4 py-2"
              >
                <span className="text-sm font-medium">{s}</span>
                <button
                  onClick={() => handleRemove(s)}
                  className="text-xs text-red-400 hover:text-red-300 transition-colors"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <p className="text-gray-500 text-xs mt-3">
          Adding a symbol here will start fetching its data in the background. Refresh the Charts page after a few seconds.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Exchange API Keys</h2>
        <p className="text-xs text-gray-500 mb-3">
          Keys are encrypted at rest using AES-GCM. A passphrase is required to encrypt/decrypt.
          {keysConfigured && <span className="text-green-400 ml-2">Keys are configured.</span>}
        </p>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Exchange</label>
            <select
              value={exchangeId}
              onChange={(e) => setExchangeId(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="binance">Binance</option>
              <option value="bybit">Bybit</option>
              <option value="okx">OKX</option>
              <option value="kraken">Kraken</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Passphrase (for encryption)</label>
            <input
              type="password"
              value={passphrase}
              onChange={(e) => setPassphrase(e.target.value)}
              placeholder="Enter a passphrase"
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Your API key"
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Secret</label>
            <input
              type="password"
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              placeholder="Your API secret"
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={async () => {
              setSavingKeys(true);
              setError(null);
              try {
                await saveExchangeKeys(exchangeId, apiKey, secret, passphrase);
                setKeysConfigured(true);
                setApiKey("");
                setSecret("");
              } catch (e) {
                setError(e instanceof Error ? e.message : "Save failed");
              } finally {
                setSavingKeys(false);
              }
            }}
            disabled={savingKeys || !apiKey || !secret || !passphrase}
            className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {savingKeys ? "Saving..." : "Save Keys"}
          </button>
          <button
            onClick={async () => {
              setTestingConn(true);
              setError(null);
              try {
                await testExchangeConnection(exchangeId, apiKey, secret);
                alert("Connection successful!");
              } catch (e) {
                setError(e instanceof Error ? e.message : "Test failed");
              } finally {
                setTestingConn(false);
              }
            }}
            disabled={testingConn || !apiKey || !secret}
            className="px-4 py-2 text-sm font-medium bg-gray-700 text-white rounded hover:bg-gray-600 transition-colors disabled:opacity-50"
          >
            {testingConn ? "Testing..." : "Test Connection"}
          </button>
        </div>
      </section>
    </div>
  );
}
