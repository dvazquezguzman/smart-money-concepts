import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import OptimizePage from "../page";

vi.mock("@/lib/api", () => ({
  runOptimization: vi.fn(),
}));

import { runOptimization } from "@/lib/api";

function getAllRunButtons() {
  return screen.getAllByRole("button", { name: /run optimization/i });
}

describe("OptimizePage", () => {
  it("renders the form with YAML textarea and controls", () => {
    render(<OptimizePage />);
    expect(screen.getByText("Strategy Optimizer")).toBeDefined();
    expect(screen.getByText("Strategy YAML")).toBeDefined();
    expect(screen.getByText("Start Date")).toBeDefined();
    expect(screen.getByText("End Date")).toBeDefined();
    expect(getAllRunButtons().length).toBeGreaterThanOrEqual(1);
  });

  it("renders default YAML in textarea", () => {
    render(<OptimizePage />);
    const textareas = screen.getAllByDisplayValue(/Optimized Strategy/);
    expect(textareas.length).toBeGreaterThanOrEqual(1);
  });

  it("shows loading state on run", async () => {
    vi.mocked(runOptimization).mockImplementation(
      () => new Promise(() => {})
    );
    render(<OptimizePage />);
    fireEvent.click(getAllRunButtons()[0]);
    expect(await screen.findAllByText("Running...")).toBeDefined();
  });

  it("displays results table after successful optimization", async () => {
    const mockResult = {
      strategy_name: "Test",
      symbol: "BTC/USDT",
      timeframe: "5m",
      total_combos: 4,
      combos_run: 4,
      results: [
        {
          params: { lookback: 10, target: 2.0 },
          total_trades: 10,
          wins: 6,
          losses: 4,
          win_rate: 0.6,
          total_pnl: 500.0,
          profit_factor: 1.5,
          max_drawdown: 0.1,
          sharpe: 1.2,
          avg_win: 100.0,
          avg_loss: 50.0,
          largest_win: 200.0,
          largest_loss: 80.0,
          avg_bars_held: 5.0,
        },
      ],
    };
    vi.mocked(runOptimization).mockResolvedValue(mockResult as any);
    render(<OptimizePage />);
    fireEvent.click(getAllRunButtons()[0]);
    await waitFor(() => {
      expect(screen.getAllByText("4 of 4 combos").length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getAllByText("$500.00").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("60.0%").length).toBeGreaterThanOrEqual(1);
  });

  it("displays error on failure", async () => {
    vi.mocked(runOptimization).mockRejectedValue(new Error("API error"));
    render(<OptimizePage />);
    fireEvent.click(getAllRunButtons()[0]);
    await waitFor(() => {
      expect(screen.getAllByText("API error").length).toBeGreaterThanOrEqual(1);
    });
  });
});
