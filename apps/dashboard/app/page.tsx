"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, GitBranch, History, RefreshCw, Rocket, Save, ShieldCheck, Sparkles } from "lucide-react";

type DraftOption = {
  id: "A" | "B";
  label: string;
  candidateTitle: string;
  sourceUrl: string;
  score: number;
  threadText: string;
};

type Candidate = {
  title?: string;
  url?: string;
  our_angle?: string;
  content_axis?: string;
  format_type?: string;
  score?: { total?: number };
};

type DashboardData = {
  date: string;
  candidateCount: number;
  candidates: Candidate[];
  drafts: DraftOption[];
  recentHistory: Array<{ hook?: string; thread_url?: string; posted_at?: string; source_name?: string }>;
  config: { autoPublishThreshold: number; dashboardSecretEnabled: boolean };
};

type Quality = { score: number; passed: boolean; reasons: string[] };

function firstLine(text: string) {
  return text.split(/\r?\n/).find((line) => line.trim()) || "";
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const text = await response.text();
  if (!response.ok) {
    throw new Error(text || response.statusText);
  }
  return JSON.parse(text) as T;
}

export default function Home() {
  const [date, setDate] = useState("");
  const [secret, setSecret] = useState("");
  const [data, setData] = useState<DashboardData | null>(null);
  const [selected, setSelected] = useState<DraftOption | null>(null);
  const [edited, setEdited] = useState("");
  const [quality, setQuality] = useState<Quality | null>(null);
  const [status, setStatus] = useState("Ready");
  const [busy, setBusy] = useState(false);

  const changed = useMemo(() => selected && selected.threadText !== edited, [selected, edited]);

  async function load(targetDate?: string) {
    setBusy(true);
    setStatus("Loading dashboard context");
    try {
      const query = targetDate ? `?date=${targetDate}` : "";
      const nextData = await jsonFetch<DashboardData>(`/api/dashboard${query}`);
      setData(nextData);
      setDate(nextData.date);
      const first = nextData.drafts[0] || null;
      setSelected(first);
      setEdited(first?.threadText || "");
      setStatus(nextData.drafts.length ? "Drafts ready" : "No candidates found for this date");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load dashboard");
    } finally {
      setBusy(false);
    }
  }

  async function checkQuality(threadText = edited) {
    const nextQuality = await jsonFetch<Quality>("/api/quality", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ threadText }),
    });
    setQuality(nextQuality);
    return nextQuality;
  }

  async function saveLearning() {
    if (!selected) return;
    setBusy(true);
    setStatus("Saving learning candidate");
    try {
      await jsonFetch("/api/learning", {
        method: "POST",
        headers: { "content-type": "application/json", "x-dashboard-secret": secret },
        body: JSON.stringify({ original: selected.threadText, edited, draftId: selected.id }),
      });
      setStatus("Learning candidate saved");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to save learning candidate");
    } finally {
      setBusy(false);
    }
  }

  async function publish(autoPublish: boolean) {
    if (!selected) return;
    setBusy(true);
    setStatus(autoPublish ? "Dispatching auto-publish workflow" : "Dispatching dry-run workflow");
    try {
      const nextQuality = await checkQuality(edited);
      if (autoPublish && nextQuality.score < (data?.config.autoPublishThreshold || 90)) {
        setStatus(`Blocked: score ${nextQuality.score} is below auto-publish threshold`);
        return;
      }
      await jsonFetch("/api/publish", {
        method: "POST",
        headers: { "content-type": "application/json", "x-dashboard-secret": secret },
        body: JSON.stringify({
          threadText: edited,
          dryRun: !autoPublish,
          autoPublish,
          topic: "research ai workflow",
          sourceCount: 1,
          format: "workflow_mode",
          sourceName: selected.candidateTitle,
          sourceUrl: selected.sourceUrl,
        }),
      });
      setStatus(autoPublish ? "Publish workflow dispatched" : "Dry-run workflow dispatched");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to dispatch workflow");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    const savedSecret = window.localStorage.getItem("dashboard-secret") || "";
    setSecret(savedSecret);
    void load();
  }, []);

  useEffect(() => {
    if (!edited) return;
    const handle = window.setTimeout(() => void checkQuality(edited), 300);
    return () => window.clearTimeout(handle);
  }, [edited]);

  return (
    <main>
      <header className="topbar">
        <div>
          <p className="eyebrow">Threads workflow harness</p>
          <h1>@arxiv.ai dashboard</h1>
        </div>
        <div className="top-actions">
          <input value={date} onChange={(event) => setDate(event.target.value)} aria-label="date" />
          <button onClick={() => void load(date)} disabled={busy}>
            <RefreshCw size={16} /> Load
          </button>
        </div>
      </header>

      <section className="status-band">
        <div>
          <strong>{status}</strong>
          <span>{data ? `${data.candidateCount} candidates · auto-publish threshold ${data.config.autoPublishThreshold}` : "Waiting for repo data"}</span>
        </div>
        <label>
          Secret
          <input
            type="password"
            value={secret}
            onChange={(event) => {
              setSecret(event.target.value);
              window.localStorage.setItem("dashboard-secret", event.target.value);
            }}
            placeholder={data?.config.dashboardSecretEnabled ? "required" : "optional"}
          />
        </label>
      </section>

      <div className="grid">
        <section className="panel">
          <div className="panel-title">
            <Sparkles size={18} />
            <h2>Draft Options</h2>
          </div>
          <div className="draft-list">
            {data?.drafts.map((draft) => (
              <button
                key={draft.id}
                className={selected?.id === draft.id ? "draft selected" : "draft"}
                onClick={() => {
                  setSelected(draft);
                  setEdited(draft.threadText);
                }}
              >
                <span>{draft.id}</span>
                <strong>{draft.label}</strong>
                <small>{draft.candidateTitle}</small>
                <em>score {draft.score}</em>
              </button>
            ))}
          </div>

          <div className="panel-title compact">
            <GitBranch size={18} />
            <h2>Candidates</h2>
          </div>
          <div className="candidate-list">
            {data?.candidates.map((candidate, index) => (
              <a key={`${candidate.url}-${index}`} href={candidate.url} target="_blank" rel="noreferrer">
                <strong>{candidate.title}</strong>
                <span>{candidate.our_angle}</span>
              </a>
            ))}
          </div>
        </section>

        <section className="editor">
          <div className="editor-head">
            <div>
              <p className="eyebrow">Selected {selected?.id || "-"}</p>
              <h2>{selected ? firstLine(selected.threadText) : "No draft selected"}</h2>
            </div>
            <div className={quality?.passed ? "score pass" : "score"}>
              <ShieldCheck size={18} />
              {quality?.score ?? "--"}
            </div>
          </div>
          <textarea value={edited} onChange={(event) => setEdited(event.target.value)} />
          <div className="quality">
            {quality?.reasons.map((reason) => (
              <span key={reason}>{reason}</span>
            ))}
          </div>
          <div className="editor-actions">
            <button onClick={() => void checkQuality()} disabled={busy}>
              <Check size={16} /> Check
            </button>
            <button onClick={() => void saveLearning()} disabled={busy || !changed}>
              <Save size={16} /> Save Learning
            </button>
            <button onClick={() => void publish(false)} disabled={busy}>
              <History size={16} /> Dry Run
            </button>
            <button className="primary" onClick={() => void publish(true)} disabled={busy || !quality?.passed}>
              <Rocket size={16} /> Auto Publish
            </button>
          </div>
        </section>

        <section className="panel">
          <div className="panel-title">
            <History size={18} />
            <h2>Recent Publishes</h2>
          </div>
          <div className="history-list">
            {data?.recentHistory.map((item, index) => (
              <a key={`${item.thread_url}-${index}`} href={item.thread_url} target="_blank" rel="noreferrer">
                <strong>{item.hook || "Untitled"}</strong>
                <span>{item.source_name || item.posted_at}</span>
              </a>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
