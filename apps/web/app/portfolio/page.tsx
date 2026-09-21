"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_URL, extractErrorMessage } from "@/lib/api";

type Position = {
  ticker: string;
  quantity: number;
  average_entry_price: number;
  cost_basis: number;
  current_price: number | null;
  market_value: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_pct: number | null;
  price_error: string | null;
};

type AccountSummary = {
  equity: number;
  total_market_value: number;
  total_unrealized_pnl: number;
  exposure_pct: number;
  position_count: number;
  positions: Position[];
};

type PortfolioResult =
  | { ok: true; portfolio: AccountSummary }
  | { ok: false; error: string };

async function loadPortfolio(): Promise<PortfolioResult> {
  try {
    const res = await fetch(`${API_URL}/portfolio`);
    const body = await res.json();
    if (!res.ok) {
      return { ok: false, error: extractErrorMessage(body) };
    }
    return { ok: true, portfolio: body as AccountSummary };
  } catch {
    return { ok: false, error: "Could not reach the research API. Is it running?" };
  }
}

function money(value: number | null): string {
  if (value === null) return "—";
  const sign = value < 0 ? "-" : "";
  return `${sign}$${Math.abs(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function pct(value: number | null): string {
  if (value === null) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<AccountSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const result = await loadPortfolio();
    if (!result.ok) {
      setError(result.error);
    } else {
      setPortfolio(result.portfolio);
      setError(null);
    }
    setLoading(false);
  }

  useEffect(() => {
    let ignore = false;
    loadPortfolio().then((result) => {
      if (ignore) return;
      if (!result.ok) {
        setError(result.error);
      } else {
        setPortfolio(result.portfolio);
        setError(null);
      }
      setLoading(false);
    });
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="flex flex-1 justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-3xl flex-col gap-6 px-6 py-12">
        <div>
          <Link href="/" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
            &larr; New research
          </Link>
        </div>

        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Portfolio</h1>
          <button
            onClick={refresh}
            disabled={loading}
            className="rounded border border-black/[.15] px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-black/[.04] disabled:opacity-50 dark:border-white/[.2] dark:text-zinc-50 dark:hover:bg-white/[.06]"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </header>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

        {portfolio && (
          <>
            <div className="rounded border border-black/[.08] bg-white p-4 dark:border-white/[.1] dark:bg-zinc-900">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm text-black dark:text-zinc-50 sm:grid-cols-3">
                <dt className="text-zinc-500 dark:text-zinc-400">Equity</dt>
                <dd>{money(portfolio.equity)}</dd>
                <dt className="text-zinc-500 dark:text-zinc-400">Positions</dt>
                <dd>{portfolio.position_count}</dd>
                <dt className="text-zinc-500 dark:text-zinc-400">Total market value</dt>
                <dd>{money(portfolio.total_market_value)}</dd>
                <dt className="text-zinc-500 dark:text-zinc-400">Exposure</dt>
                <dd>{portfolio.exposure_pct.toFixed(2)}%</dd>
                <dt className="text-zinc-500 dark:text-zinc-400">Unrealized P&amp;L</dt>
                <dd
                  className={
                    portfolio.total_unrealized_pnl > 0
                      ? "text-green-600 dark:text-green-400"
                      : portfolio.total_unrealized_pnl < 0
                        ? "text-red-600 dark:text-red-400"
                        : ""
                  }
                >
                  {money(portfolio.total_unrealized_pnl)}
                </dd>
              </dl>
            </div>

            <div className="rounded border border-black/[.08] bg-white dark:border-white/[.1] dark:bg-zinc-900">
              {portfolio.positions.length === 0 ? (
                <p className="p-4 text-sm text-zinc-500">No open positions.</p>
              ) : (
                <table className="w-full text-sm text-black dark:text-zinc-50">
                  <thead>
                    <tr className="border-b border-black/[.08] text-left text-xs uppercase tracking-wide text-zinc-500 dark:border-white/[.1] dark:text-zinc-400">
                      <th className="px-4 py-2 font-medium">Ticker</th>
                      <th className="px-4 py-2 font-medium">Qty</th>
                      <th className="px-4 py-2 font-medium">Avg entry</th>
                      <th className="px-4 py-2 font-medium">Current</th>
                      <th className="px-4 py-2 font-medium">Market value</th>
                      <th className="px-4 py-2 font-medium">Unrealized P&amp;L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.positions.map((p) => (
                      <tr key={p.ticker} className="border-b border-black/[.05] last:border-0 dark:border-white/[.05]">
                        <td className="px-4 py-2 font-medium">{p.ticker}</td>
                        <td className="px-4 py-2">{p.quantity}</td>
                        <td className="px-4 py-2">{money(p.average_entry_price)}</td>
                        <td className="px-4 py-2">
                          {p.price_error ? (
                            <span className="text-xs text-red-600 dark:text-red-400">{p.price_error}</span>
                          ) : (
                            money(p.current_price)
                          )}
                        </td>
                        <td className="px-4 py-2">{money(p.market_value)}</td>
                        <td
                          className={`px-4 py-2 ${
                            (p.unrealized_pnl ?? 0) > 0
                              ? "text-green-600 dark:text-green-400"
                              : (p.unrealized_pnl ?? 0) < 0
                                ? "text-red-600 dark:text-red-400"
                                : ""
                          }`}
                        >
                          {money(p.unrealized_pnl)} ({pct(p.unrealized_pnl_pct)})
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
