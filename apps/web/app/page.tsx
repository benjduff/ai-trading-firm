"use client";

import Link from "next/link";
import { useState } from "react";
import { API_URL, extractErrorMessage } from "@/lib/api";

type ResearchJob = {
  id: string;
  ticker: string;
  created_at: string;
  status: string;
  as_of: string;
  requested_by: string | null;
};

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setJob(null);

    try {
      const res = await fetch(`${API_URL}/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker }),
      });
      const body = await res.json();

      if (!res.ok) {
        setError(extractErrorMessage(body));
        return;
      }

      setJob(body as ResearchJob);
    } catch {
      setError("Could not reach the research API. Is it running?");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-md flex-col gap-6 px-6 py-24">
        <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">
          Investigate a ticker
        </h1>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="e.g. OXY"
            className="flex-1 rounded border border-black/[.15] bg-white px-3 py-2 text-black dark:border-white/[.2] dark:bg-zinc-900 dark:text-zinc-50"
          />
          <button
            type="submit"
            disabled={submitting || ticker.trim() === ""}
            className="rounded bg-foreground px-4 py-2 font-medium text-background transition-colors hover:bg-[#383838] disabled:opacity-50 dark:hover:bg-[#ccc]"
          >
            {submitting ? "Investigating…" : "Investigate"}
          </button>
        </form>

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        )}

        {job && (
          <div className="rounded border border-black/[.08] bg-white p-4 text-sm dark:border-white/[.1] dark:bg-zinc-900">
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-black dark:text-zinc-50">
              <dt className="text-zinc-500 dark:text-zinc-400">Job ID</dt>
              <dd className="font-mono">{job.id}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Ticker</dt>
              <dd>{job.ticker}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Status</dt>
              <dd>{job.status}</dd>
            </dl>
            <Link
              href={`/research/${job.id}`}
              className="mt-3 inline-block text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
              View research &rarr;
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}
