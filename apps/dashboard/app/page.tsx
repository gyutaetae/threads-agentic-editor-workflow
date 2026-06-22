"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart3, Check, GitBranch, GitCompare, History, Network, RefreshCw, Rocket, Save, ShieldCheck, Sparkles } from "lucide-react";

type DraftOption = {
  id: "A" | "B";
  label: string;
  candidateTitle: string;
  sourceUrl: string;
  score: number;
  styleHints: string[];
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

type PromotionSuggestion = {
  id: string;
  status: string;
  score: number;
  title: string;
  evidence: string;
  proposedLearning: string;
  proposedSkill: { name: string; trigger: string; minimalToolset: string[]; crystallizedPath: string[] };
};

type DashboardData = {
  date: string;
  candidateCount: number;
  candidates: Candidate[];
  drafts: DraftOption[];
  draftRanking: Array<{ id: string; title: string; score: number; reasons: string[] }>;
  metrics: Array<Record<string, string> & { engagement: { likes: number; reposts: number; shares: number; comments: number; visits: number; weighted: number } }>;
  learningCandidates: Array<{ created_at?: string; diff_summary?: string; source_name?: string; edited?: string; status?: string; quality_score?: number }>;
  promotionSuggestions: PromotionSuggestion[];
  skillTree: { root: string; minimalToolset: string[]; crystallizedSkills: string[]; currentRules: string[]; strongestSignal: string };
  learnings: string[];
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
  const [activeTab, setActiveTab] = useState<"draft" | "learning" | "recent">("draft");
  const [promotionSuggestions, setPromotionSuggestions] = useState<PromotionSuggestion[]>([]);

  const changed = useMemo(() => Boolean(selected && selected.threadText !== edited), [selected, edited]);

  async function load(targetDate?: string) {
    setBusy(true);
    setStatus("Loading dashboard context");
    try {
      const query = targetDate ? `?date=${targetDate}` : "";
      const nextData = await jsonFetch<DashboardData>(`/api/dashboard${query}`);
      setData(nextData);
      setDate(nextData.date);
      setPromotionSuggestions(nextData.promotionSuggestions || []);
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
        body: JSON.stringify({
          original: selected.threadText,
          edited,
          draftId: selected.id,
          sourceUrl: selected.sourceUrl,
          sourceName: selected.candidateTitle,
          score: selected.score,
        }),
      });
      setStatus("Learning candidate saved and will influence the next draft load");
      await load(date);
      setActiveTab("learning");
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
      if (autoPublish && nextQuality.score < (data?.config.autoPublishThreshold || 85)) {
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

  async function compareAB() {
    if (!data?.drafts.length) return;
    setBusy(true);
    setStatus("Dispatching A/B dry-run comparison");
    try {
      await jsonFetch("/api/compare", {
        method: "POST",
        headers: { "content-type": "application/json", "x-dashboard-secret": secret },
        body: JSON.stringify({
          drafts: data.drafts.map((draft) => ({
            id: draft.id,
            threadText: draft.threadText,
            sourceName: draft.candidateTitle,
            sourceUrl: draft.sourceUrl,
          })),
        }),
      });
      setStatus("A/B dry-run workflows dispatched");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to dispatch A/B dry run");
    } finally {
      setBusy(false);
    }
  }

  async function generatePromotionSuggestions() {
    setBusy(true);
    setStatus("Generating promotion suggestions");
    try {
      const response = await jsonFetch<{ suggestions: PromotionSuggestion[] }>("/api/promotion");
      setPromotionSuggestions(response.suggestions);
      setStatus("Promotion suggestions refreshed");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to generate promotion suggestions");
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

      <nav className="tabs">
        <button className={activeTab === "draft" ? "tab active" : "tab"} onClick={() => setActiveTab("draft")}>
          <Sparkles size={16} /> Draft Lab
        </button>
        <button className={activeTab === "learning" ? "tab active" : "tab"} onClick={() => setActiveTab("learning")}>
          <Network size={16} /> Learning Loop
        </button>
        <button className={activeTab === "recent" ? "tab active" : "tab"} onClick={() => setActiveTab("recent")}>
          <History size={16} /> Recent Publishes
        </button>
      </nav>

      {activeTab === "draft" && (
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
                  <em>source {draft.score}</em>
                </button>
              ))}
            </div>

            <div className="panel-title compact">
              <GitCompare size={18} />
              <h2>A/B Decision</h2>
            </div>
            <div className="ranking-list">
              {data?.draftRanking.map((item) => (
                <div key={item.id} className="rank-row">
                  <strong>{item.id}</strong>
                  <span>{item.score}</span>
                  <small>{item.reasons[0]}</small>
                </div>
              ))}
            </div>
            <button className="wide" onClick={() => void compareAB()} disabled={busy || !data?.drafts.length}>
              <GitCompare size={16} /> Dry Run A/B
            </button>

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
              {data?.recentHistory.slice(0, 5).map((item, index) => (
                item.thread_url ? (
                  <a key={`${item.thread_url}-${index}`} href={item.thread_url} target="_blank" rel="noreferrer">
                    <strong>{item.hook || "Untitled"}</strong>
                    <span>{item.source_name || item.posted_at}</span>
                  </a>
                ) : (
                  <div key={`${item.hook}-${index}`} className="history-empty">
                    <strong>{item.hook || "Untitled"}</strong>
                    <span>No Threads URL recorded</span>
                  </div>
                )
              ))}
            </div>
          </section>
        </div>
      )}

      {activeTab === "learning" && (
        <div className="learning-grid">
          <section className="panel">
            <div className="panel-title">
              <Network size={18} />
              <h2>Learning Candidates</h2>
            </div>
            <div className="learning-list">
              {data?.learningCandidates.map((candidate, index) => (
                <div key={`${candidate.created_at}-${index}`} className="learning-row">
                  <strong>{candidate.diff_summary || firstLine(candidate.edited || "") || "Saved edit"}</strong>
                  <span>{candidate.source_name || candidate.created_at}</span>
                  <em>quality {candidate.quality_score ?? "-"}</em>
                </div>
              ))}
              {!data?.learningCandidates.length && <p className="muted">No dashboard learning candidates yet.</p>}
            </div>
          </section>

          <section className="panel">
            <div className="panel-title">
              <BarChart3 size={18} />
              <h2>Metrics Evidence</h2>
            </div>
            <div className="metrics-table">
              <div className="metrics-head">
                <span>Hook</span><span>Like</span><span>Repost</span><span>Share</span><span>Comment</span><span>Visit</span><span>Score</span>
              </div>
              {data?.metrics.map((row, index) => (
                <div key={`${row.post_id}-${index}`} className="metrics-row">
                  <a href={row.thread_url} target="_blank" rel="noreferrer">{row.hook || row.post_id}</a>
                  <span>{row.engagement.likes}</span>
                  <span>{row.engagement.reposts}</span>
                  <span>{row.engagement.shares}</span>
                  <span>{row.engagement.comments}</span>
                  <span>{row.engagement.visits}</span>
                  <strong>{row.engagement.weighted}</strong>
                </div>
              ))}
              {!data?.metrics.length && <p className="muted">No committed metrics file yet.</p>}
            </div>
          </section>

          <section className="panel">
            <div className="panel-title">
              <Save size={18} />
              <h2>Promotion Suggestions</h2>
            </div>
            <button className="wide" onClick={() => void generatePromotionSuggestions()} disabled={busy}>
              <Sparkles size={16} /> Generate Promotion Suggestions
            </button>
            <div className="suggestion-list">
              {promotionSuggestions.map((suggestion) => (
                <div key={suggestion.id} className="suggestion">
                  <strong>{suggestion.title}</strong>
                  <span>{suggestion.status} · weighted {suggestion.score}</span>
                  <p>{suggestion.evidence}</p>
                  <code>{suggestion.proposedLearning}</code>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-title">
              <Network size={18} />
              <h2>Skill Tree</h2>
            </div>
            <div className="skill-tree">
              <strong>{data?.skillTree.root}</strong>
              <span>Minimal toolset: {data?.skillTree.minimalToolset.join(" -> ")}</span>
              <span>Strongest signal: {data?.skillTree.strongestSignal}</span>
              <div>
                {data?.skillTree.crystallizedSkills.map((skill) => <em key={skill}>{skill}</em>)}
              </div>
            </div>
            <div className="panel-title compact">
              <h2>docs/learnings.md</h2>
            </div>
            <ul className="rules-list">
              {data?.learnings.map((rule) => <li key={rule}>{rule}</li>)}
            </ul>
          </section>
        </div>
      )}

      {activeTab === "recent" && (
        <section className="panel recent-panel">
          <div className="panel-title">
            <History size={18} />
            <h2>Recent Publishes</h2>
          </div>
          <div className="history-list wide-history">
            {data?.recentHistory.map((item, index) => (
              item.thread_url ? (
                <a key={`${item.thread_url}-${index}`} href={item.thread_url} target="_blank" rel="noreferrer">
                  <strong>{item.hook || "Untitled"}</strong>
                  <span>{item.source_name || item.posted_at}</span>
                </a>
              ) : (
                <div key={`${item.hook}-${index}`} className="history-empty">
                  <strong>{item.hook || "Untitled"}</strong>
                  <span>No Threads URL recorded</span>
                </div>
              )
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
