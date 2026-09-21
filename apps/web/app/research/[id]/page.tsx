"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { API_URL, extractErrorMessage } from "@/lib/api";

type Evidence = {
  id: string;
  source: string;
  source_url: string | null;
  claim: string;
  published_at: string;
};

type FundamentalReport = {
  summary: string;
  key_findings: string[];
  financial_health: string;
  valuation_view: string;
  catalysts: string[];
  risks: string[];
  model_id: string;
};

type PsychologyReport = {
  summary: string;
  market_temperature: number;
  expectation_gap: string;
  fear_of_loss: number;
  fomo: number;
  narrative_saturation: number;
  crowding: number;
  dominant_narrative: string;
  differentiated_or_contrarian_view: string;
  psychology_confidence: number;
  model_id: string;
};

type RedTeamReport = {
  independent_bear_case: string;
  key_risks: string[];
  thesis_challenges: string[];
  weakest_point_in_thesis: string;
  what_would_invalidate_the_bear_case: string;
  model_id: string;
};

type QuantMetrics = {
  benchmark_ticker: string;
  sector_ticker: string | null;
  lookback_trading_days: number;
  as_of: string;
  cumulative_return: number;
  annualized_volatility: number;
  beta: number;
  correlation_to_benchmark: number;
  max_drawdown: number;
  cumulative_abnormal_return: number;
  sector_relative_return: number | null;
};

type RiskAssessment = {
  suggested_position_size_pct: number;
  stop_loss_distance_pct: number;
  max_position_pct_cap: number;
  notes: string[];
};

type TradeProposal = {
  action: "buy" | "sell" | "hold";
  thesis: string;
  catalyst: string;
  expectation_gap: string;
  risk_notes: string;
  invalidation_conditions: string[];
  uncertainties: string[];
  position_size_pct: number | null;
  stop_loss_distance_pct: number | null;
  model_id: string | null;
};

type HumanDecision = {
  action: string;
  reasoning: string;
  decided_by: string;
  decided_at: string;
};

type ShadowPerformance = {
  shadow_position: {
    ticker: string;
    action: string;
    entry_price: number;
    entry_price_as_of: string;
    frozen_at: string;
  };
  current_price: number;
  current_price_as_of: string;
  days_since_frozen: number;
  raw_price_return_pct: number;
  shadow_return_pct: number;
  human_decision_action: string | null;
};

type ResearchJob = {
  id: string;
  ticker: string;
  status: string;
  created_at: string;
};

type Summary = {
  job: ResearchJob;
  evidence: Evidence[];
  fundamental_report: FundamentalReport | null;
  psychology_report: PsychologyReport | null;
  red_team_report: RedTeamReport | null;
  quant_metrics: QuantMetrics | null;
  risk_assessment: RiskAssessment | null;
  trade_proposal: TradeProposal | null;
  human_decision: HumanDecision | null;
};

const PIPELINE_STEPS = [
  { key: "ingest", label: "Ingest SEC filings", path: "ingest/sec-edgar" },
  { key: "fundamental", label: "Fundamental analysis", path: "analyze/fundamental" },
  { key: "psychology", label: "Psychology analysis", path: "analyze/psychology" },
  { key: "red_team", label: "Red team challenge", path: "analyze/red-team" },
  { key: "quant", label: "Quant metrics", path: "analyze/quant" },
  { key: "risk", label: "Risk assessment", path: "analyze/risk" },
  { key: "synthesize", label: "CIO synthesis", path: "synthesize" },
] as const;

type StepStatus = "idle" | "running" | "done" | "error";

const DECISION_ACTIONS = [
  { value: "approve", label: "Approve" },
  { value: "reject", label: "Reject" },
  { value: "watch", label: "Watch" },
  { value: "request_more_research", label: "Request More Research" },
] as const;

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded border border-black/[.08] bg-white p-4 dark:border-white/[.1] dark:bg-zinc-900">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {title}
      </h2>
      {children}
    </div>
  );
}

function List({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="text-sm text-zinc-500">None</p>;
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm text-black dark:text-zinc-50">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function pct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

type SummaryResult =
  | { ok: true; summary: Summary }
  | { ok: false; error: string };

async function loadSummary(jobId: string): Promise<SummaryResult> {
  try {
    const res = await fetch(`${API_URL}/research/${jobId}/summary`);
    const body = await res.json();
    if (!res.ok) {
      return { ok: false, error: extractErrorMessage(body) };
    }
    return { ok: true, summary: body as Summary };
  } catch {
    return { ok: false, error: "Could not reach the research API. Is it running?" };
  }
}

export default function ResearchDashboard() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;

  const [summary, setSummary] = useState<Summary | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [stepStatus, setStepStatus] = useState<Record<string, StepStatus>>({});
  const [running, setRunning] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);

  const [decisionAction, setDecisionAction] = useState<string>("approve");
  const [reasoning, setReasoning] = useState("");
  const [decidedBy, setDecidedBy] = useState("");
  const [decisionSubmitting, setDecisionSubmitting] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  const [shadowPerformance, setShadowPerformance] = useState<ShadowPerformance | null>(null);
  const [shadowLoading, setShadowLoading] = useState(false);
  const [shadowError, setShadowError] = useState<string | null>(null);

  async function fetchShadowPerformance() {
    setShadowLoading(true);
    setShadowError(null);
    try {
      const res = await fetch(`${API_URL}/research/${jobId}/shadow-performance`);
      const body = await res.json();
      if (!res.ok) {
        setShadowError(extractErrorMessage(body));
        return;
      }
      setShadowPerformance(body as ShadowPerformance);
    } catch {
      setShadowError("Could not reach the research API. Is it running?");
    } finally {
      setShadowLoading(false);
    }
  }

  const fetchSummary = useCallback(async () => {
    const result = await loadSummary(jobId);
    if (!result.ok) {
      setLoadError(result.error);
    } else {
      setSummary(result.summary);
      setLoadError(null);
    }
  }, [jobId]);

  useEffect(() => {
    let ignore = false;
    loadSummary(jobId).then((result) => {
      if (ignore) return;
      if (!result.ok) {
        setLoadError(result.error);
      } else {
        setSummary(result.summary);
        setLoadError(null);
      }
    });
    return () => {
      ignore = true;
    };
  }, [jobId]);

  async function runFullAnalysis() {
    setRunning(true);
    setPipelineError(null);
    setStepStatus({});

    for (const step of PIPELINE_STEPS) {
      setStepStatus((prev) => ({ ...prev, [step.key]: "running" }));
      try {
        const res = await fetch(`${API_URL}/research/${jobId}/${step.path}`, {
          method: "POST",
        });
        const body = await res.json();
        if (!res.ok) {
          setStepStatus((prev) => ({ ...prev, [step.key]: "error" }));
          setPipelineError(`${step.label} failed: ${extractErrorMessage(body)}`);
          break;
        }
        setStepStatus((prev) => ({ ...prev, [step.key]: "done" }));
        await fetchSummary();
      } catch {
        setStepStatus((prev) => ({ ...prev, [step.key]: "error" }));
        setPipelineError(`${step.label} failed: could not reach the research API.`);
        break;
      }
    }

    setRunning(false);
  }

  async function submitDecision(e: React.FormEvent) {
    e.preventDefault();
    setDecisionSubmitting(true);
    setDecisionError(null);
    try {
      const res = await fetch(`${API_URL}/research/${jobId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: decisionAction,
          reasoning,
          decided_by: decidedBy,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setDecisionError(extractErrorMessage(body));
        return;
      }
      await fetchSummary();
    } catch {
      setDecisionError("Could not reach the research API. Is it running?");
    } finally {
      setDecisionSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div className="flex flex-1 items-center justify-center bg-zinc-50 dark:bg-black">
        <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-1 items-center justify-center bg-zinc-50 dark:bg-black">
        <p className="text-sm text-zinc-500">Loading...</p>
      </div>
    );
  }

  const { job, evidence, fundamental_report, psychology_report, red_team_report, quant_metrics, risk_assessment, trade_proposal, human_decision } = summary;

  return (
    <div className="flex flex-1 justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-3xl flex-col gap-6 px-6 py-12">
        <div>
          <Link href="/" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
            &larr; New research
          </Link>
        </div>

        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">
              {job.ticker}
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Job {job.id} &middot; status: {job.status}
            </p>
          </div>
          <button
            onClick={runFullAnalysis}
            disabled={running}
            className="rounded bg-foreground px-4 py-2 text-sm font-medium text-background transition-colors hover:bg-[#383838] disabled:opacity-50 dark:hover:bg-[#ccc]"
          >
            {running ? "Running..." : "Run Full Analysis"}
          </button>
        </header>

        {Object.keys(stepStatus).length > 0 && (
          <div className="rounded border border-black/[.08] bg-white p-4 text-sm dark:border-white/[.1] dark:bg-zinc-900">
            <ul className="space-y-1">
              {PIPELINE_STEPS.map((step) => {
                const status = stepStatus[step.key] ?? "idle";
                const icon =
                  status === "done" ? "✅" : status === "running" ? "⏳" : status === "error" ? "❌" : "○";
                return (
                  <li key={step.key} className="text-black dark:text-zinc-50">
                    {icon} {step.label}
                  </li>
                );
              })}
            </ul>
            {pipelineError && (
              <p className="mt-2 text-red-600 dark:text-red-400">{pipelineError}</p>
            )}
          </div>
        )}

        {trade_proposal && (
          <Card title={`Trade Proposal — ${trade_proposal.action.toUpperCase()}`}>
            <div className="space-y-3 text-sm text-black dark:text-zinc-50">
              <p><span className="font-medium">Thesis:</span> {trade_proposal.thesis}</p>
              <p><span className="font-medium">Catalyst:</span> {trade_proposal.catalyst}</p>
              <p><span className="font-medium">Expectation gap:</span> {trade_proposal.expectation_gap}</p>
              <p><span className="font-medium">Risk notes:</span> {trade_proposal.risk_notes}</p>
              <p>
                <span className="font-medium">Suggested position size:</span>{" "}
                {trade_proposal.position_size_pct?.toFixed(2) ?? "—"}% &middot;{" "}
                <span className="font-medium">Stop-loss distance:</span>{" "}
                {trade_proposal.stop_loss_distance_pct?.toFixed(2) ?? "—"}%
              </p>
              <div>
                <p className="font-medium">Invalidation conditions:</p>
                <List items={trade_proposal.invalidation_conditions} />
              </div>
              <div>
                <p className="font-medium">Uncertainties:</p>
                <List items={trade_proposal.uncertainties} />
              </div>
              {trade_proposal.model_id && (
                <p className="text-xs text-zinc-500">Model: {trade_proposal.model_id}</p>
              )}
            </div>
          </Card>
        )}

        {trade_proposal && (
          <Card title="Shadow Performance">
            <div className="space-y-3 text-sm text-black dark:text-zinc-50">
              <p className="text-xs text-zinc-500">
                Frozen automatically when the proposal was synthesized, regardless of the human decision - this is how the firm grades its own calls against reality before risking real capital.
              </p>
              <button
                onClick={fetchShadowPerformance}
                disabled={shadowLoading}
                className="rounded border border-black/[.15] px-3 py-1.5 text-sm font-medium text-black transition-colors hover:bg-black/[.04] disabled:opacity-50 dark:border-white/[.2] dark:text-zinc-50 dark:hover:bg-white/[.06]"
              >
                {shadowLoading ? "Checking..." : shadowPerformance ? "Refresh" : "Check shadow performance"}
              </button>
              {shadowError && (
                <p className="text-red-600 dark:text-red-400">{shadowError}</p>
              )}
              {shadowPerformance && (
                <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                  <dt className="text-zinc-500 dark:text-zinc-400">Entry price</dt>
                  <dd>${shadowPerformance.shadow_position.entry_price.toFixed(2)} ({shadowPerformance.shadow_position.entry_price_as_of})</dd>
                  <dt className="text-zinc-500 dark:text-zinc-400">Current price</dt>
                  <dd>${shadowPerformance.current_price.toFixed(2)} ({shadowPerformance.current_price_as_of})</dd>
                  <dt className="text-zinc-500 dark:text-zinc-400">Days since frozen</dt>
                  <dd>{shadowPerformance.days_since_frozen}</dd>
                  <dt className="text-zinc-500 dark:text-zinc-400">Shadow return ({shadowPerformance.shadow_position.action})</dt>
                  <dd className={shadowPerformance.shadow_return_pct > 0 ? "text-green-600 dark:text-green-400" : shadowPerformance.shadow_return_pct < 0 ? "text-red-600 dark:text-red-400" : ""}>
                    {pct(shadowPerformance.shadow_return_pct)}
                  </dd>
                  {shadowPerformance.human_decision_action && (
                    <>
                      <dt className="text-zinc-500 dark:text-zinc-400">Human decision</dt>
                      <dd>{shadowPerformance.human_decision_action.replace(/_/g, " ")}</dd>
                    </>
                  )}
                </dl>
              )}
            </div>
          </Card>
        )}

        {fundamental_report && (
          <Card title="Fundamental Analyst">
            <div className="space-y-3 text-sm text-black dark:text-zinc-50">
              <p>{fundamental_report.summary}</p>
              <div>
                <p className="font-medium">Key findings:</p>
                <List items={fundamental_report.key_findings} />
              </div>
              <p><span className="font-medium">Financial health:</span> {fundamental_report.financial_health}</p>
              <p><span className="font-medium">Valuation view:</span> {fundamental_report.valuation_view}</p>
              <div>
                <p className="font-medium">Catalysts:</p>
                <List items={fundamental_report.catalysts} />
              </div>
              <div>
                <p className="font-medium">Risks:</p>
                <List items={fundamental_report.risks} />
              </div>
            </div>
          </Card>
        )}

        {psychology_report && (
          <Card title="Psychology Analyst (independent)">
            <div className="space-y-3 text-sm text-black dark:text-zinc-50">
              <p>{psychology_report.summary}</p>
              <p>
                <span className="font-medium">Market temperature:</span>{" "}
                {psychology_report.market_temperature} (-5 panic .. +5 euphoria)
              </p>
              <p><span className="font-medium">Expectation gap:</span> {psychology_report.expectation_gap}</p>
              <p><span className="font-medium">Dominant narrative:</span> {psychology_report.dominant_narrative}</p>
              <p><span className="font-medium">Differentiated view:</span> {psychology_report.differentiated_or_contrarian_view}</p>
              <p className="text-xs text-zinc-500">
                Fear of loss {psychology_report.fear_of_loss.toFixed(2)} &middot; FOMO {psychology_report.fomo.toFixed(2)} &middot;{" "}
                Narrative saturation {psychology_report.narrative_saturation.toFixed(2)} &middot; Crowding {psychology_report.crowding.toFixed(2)}
              </p>
            </div>
          </Card>
        )}

        {red_team_report && (
          <Card title="Red Team (independent, then challenged the thesis)">
            <div className="space-y-3 text-sm text-black dark:text-zinc-50">
              <p><span className="font-medium">Independent bear case:</span> {red_team_report.independent_bear_case}</p>
              <div>
                <p className="font-medium">Key risks:</p>
                <List items={red_team_report.key_risks} />
              </div>
              <div>
                <p className="font-medium">Thesis challenges:</p>
                <List items={red_team_report.thesis_challenges} />
              </div>
              <p><span className="font-medium">Weakest point in thesis:</span> {red_team_report.weakest_point_in_thesis}</p>
              <p><span className="font-medium">Would invalidate bear case:</span> {red_team_report.what_would_invalidate_the_bear_case}</p>
            </div>
          </Card>
        )}

        {quant_metrics && (
          <Card title="Quant (deterministic)">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-black dark:text-zinc-50 sm:grid-cols-3">
              <dt className="text-zinc-500 dark:text-zinc-400">Cumulative return</dt>
              <dd>{pct(quant_metrics.cumulative_return)}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Annualized vol</dt>
              <dd>{pct(quant_metrics.annualized_volatility)}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Beta vs {quant_metrics.benchmark_ticker}</dt>
              <dd>{quant_metrics.beta.toFixed(2)}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Correlation</dt>
              <dd>{quant_metrics.correlation_to_benchmark.toFixed(2)}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Max drawdown</dt>
              <dd>{pct(quant_metrics.max_drawdown)}</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Abnormal return</dt>
              <dd>{pct(quant_metrics.cumulative_abnormal_return)}</dd>
              {quant_metrics.sector_ticker && (
                <>
                  <dt className="text-zinc-500 dark:text-zinc-400">
                    Vs {quant_metrics.sector_ticker}
                  </dt>
                  <dd>{pct(quant_metrics.sector_relative_return)}</dd>
                </>
              )}
            </dl>
            <p className="mt-2 text-xs text-zinc-500">
              As of {quant_metrics.as_of} &middot; {quant_metrics.lookback_trading_days} trading days
            </p>
          </Card>
        )}

        {risk_assessment && (
          <Card title="Risk (deterministic)">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-black dark:text-zinc-50 sm:grid-cols-3">
              <dt className="text-zinc-500 dark:text-zinc-400">Suggested size</dt>
              <dd>{risk_assessment.suggested_position_size_pct.toFixed(2)}%</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Max cap</dt>
              <dd>{risk_assessment.max_position_pct_cap.toFixed(2)}%</dd>
              <dt className="text-zinc-500 dark:text-zinc-400">Stop-loss distance</dt>
              <dd>{risk_assessment.stop_loss_distance_pct.toFixed(2)}%</dd>
            </dl>
            {risk_assessment.notes.length > 0 && (
              <div className="mt-2">
                <List items={risk_assessment.notes} />
              </div>
            )}
          </Card>
        )}

        {evidence.length > 0 && (
          <Card title={`Evidence (${evidence.length})`}>
            <ul className="space-y-2 text-sm text-black dark:text-zinc-50">
              {evidence.map((e) => (
                <li key={e.id}>
                  {e.source_url ? (
                    <a
                      href={e.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {e.claim}
                    </a>
                  ) : (
                    e.claim
                  )}
                  <span className="text-xs text-zinc-500"> &middot; {e.published_at.slice(0, 10)}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        <Card title="Human Decision">
          {human_decision ? (
            <div className="space-y-2 text-sm text-black dark:text-zinc-50">
              <p>
                <span className="font-medium">{human_decision.action.replace(/_/g, " ").toUpperCase()}</span>{" "}
                by {human_decision.decided_by} on {human_decision.decided_at.slice(0, 10)}
              </p>
              <p className="text-zinc-600 dark:text-zinc-400">{human_decision.reasoning}</p>
            </div>
          ) : trade_proposal ? (
            <form onSubmit={submitDecision} className="flex flex-col gap-3">
              <div className="flex flex-wrap gap-2">
                {DECISION_ACTIONS.map((opt) => (
                  <label
                    key={opt.value}
                    className={`cursor-pointer rounded border px-3 py-1.5 text-sm ${
                      decisionAction === opt.value
                        ? "border-foreground bg-foreground text-background"
                        : "border-black/[.15] text-black dark:border-white/[.2] dark:text-zinc-50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="action"
                      value={opt.value}
                      checked={decisionAction === opt.value}
                      onChange={(e) => setDecisionAction(e.target.value)}
                      className="sr-only"
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
              <textarea
                value={reasoning}
                onChange={(e) => setReasoning(e.target.value)}
                placeholder="Reasoning (required) - this is stored as proprietary research data"
                rows={3}
                className="rounded border border-black/[.15] bg-white px-3 py-2 text-sm text-black dark:border-white/[.2] dark:bg-zinc-900 dark:text-zinc-50"
              />
              <input
                type="text"
                value={decidedBy}
                onChange={(e) => setDecidedBy(e.target.value)}
                placeholder="Your name"
                className="rounded border border-black/[.15] bg-white px-3 py-2 text-sm text-black dark:border-white/[.2] dark:bg-zinc-900 dark:text-zinc-50"
              />
              {decisionError && (
                <p className="text-sm text-red-600 dark:text-red-400">{decisionError}</p>
              )}
              <button
                type="submit"
                disabled={decisionSubmitting || reasoning.trim() === "" || decidedBy.trim() === ""}
                className="self-start rounded bg-foreground px-4 py-2 text-sm font-medium text-background transition-colors hover:bg-[#383838] disabled:opacity-50 dark:hover:bg-[#ccc]"
              >
                {decisionSubmitting ? "Recording..." : "Record decision"}
              </button>
            </form>
          ) : (
            <p className="text-sm text-zinc-500">
              Run the full analysis to generate a trade proposal before recording a decision.
            </p>
          )}
        </Card>
      </main>
    </div>
  );
}
