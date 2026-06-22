import { Candidate, DraftOption, qualityScore, summarizeDiff } from "./workflow";

export type MetricRow = Record<string, string>;

export type LearningCandidate = {
  created_at?: string;
  date?: string;
  draft_id?: string;
  note?: string;
  diff_summary?: string;
  original?: string;
  edited?: string;
  status?: string;
  source_url?: string;
  source_name?: string;
  quality_score?: number;
};

export type PromotionSuggestion = {
  id: string;
  status: "promote-ready" | "needs-metrics" | "watch";
  score: number;
  title: string;
  evidence: string;
  proposedLearning: string;
  proposedSkill: {
    name: string;
    trigger: string;
    minimalToolset: string[];
    crystallizedPath: string[];
  };
};

export function parseJsonl<T>(text: string): T[] {
  return text
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line) as T;
      } catch {
        return null;
      }
    })
    .filter(Boolean) as T[];
}

export function parseCsv(text: string): MetricRow[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (quoted) {
      if (char === '"' && next === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
      continue;
    }
    if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field || row.length) {
    row.push(field);
    rows.push(row);
  }

  const [headers, ...values] = rows;
  if (!headers) return [];
  return values
    .filter((value) => value.some(Boolean))
    .map((value) =>
      Object.fromEntries(headers.map((header, index) => [header, value[index] || ""])),
    );
}

function intValue(row: MetricRow, key: string) {
  const value = Number(row[key] || 0);
  return Number.isFinite(value) ? value : 0;
}

export function engagementScore(row: MetricRow) {
  const likes = intValue(row, "likes");
  const reposts = intValue(row, "reposts");
  const shares = intValue(row, "shares") || intValue(row, "quotes");
  const comments = intValue(row, "audience_replies") || intValue(row, "replies");
  const visits = intValue(row, "profile_visits");
  return {
    likes,
    reposts,
    shares,
    comments,
    visits,
    weighted: likes * 5 + reposts * 4 + shares * 3 + comments * 2 + visits,
  };
}

export function rankDrafts(drafts: DraftOption[]) {
  return drafts
    .map((draft) => {
      const quality = qualityScore(draft.threadText);
      return {
        id: draft.id,
        title: draft.candidateTitle,
        score: quality.score + Math.min(10, Math.floor(draft.score / 10)),
        reasons: quality.reasons,
      };
    })
    .sort((a, b) => b.score - a.score);
}

export function buildLearningCandidates(original: string, edited: string, draft: DraftOption, note = ""): LearningCandidate {
  const quality = qualityScore(edited);
  return {
    created_at: new Date().toISOString(),
    draft_id: draft.id,
    note,
    diff_summary: summarizeDiff(original, edited),
    original,
    edited,
    source_url: draft.sourceUrl,
    source_name: draft.candidateTitle,
    quality_score: quality.score,
    status: "candidate",
  };
}

function firstLine(text = "") {
  return text.split(/\r?\n/).find((line) => line.trim())?.trim() || "";
}

function learningText(candidate: LearningCandidate) {
  return candidate.edited || candidate.diff_summary || candidate.note || "";
}

function findMetric(candidate: LearningCandidate, metrics: MetricRow[]) {
  const hook = firstLine(candidate.edited);
  return metrics.find((row) => {
    if (candidate.source_url && row.source_url === candidate.source_url) return true;
    if (hook && row.hook === hook) return true;
    return false;
  });
}

export function buildPromotionSuggestions(candidates: LearningCandidate[], metrics: MetricRow[], existingLearnings: string): PromotionSuggestion[] {
  return candidates.slice(-12).reverse().map((candidate, index) => {
    const metric = findMetric(candidate, metrics);
    const engagement = metric ? engagementScore(metric) : null;
    const text = learningText(candidate);
    const concise = candidate.diff_summary || firstLine(text) || "Edited dashboard draft pattern";
    const duplicate = existingLearnings.includes(concise.slice(0, 40));
    const score = engagement ? engagement.weighted : 0;
    const status: PromotionSuggestion["status"] = duplicate
      ? "watch"
      : score >= 5
        ? "promote-ready"
        : metric
          ? "watch"
          : "needs-metrics";

    return {
      id: `${candidate.created_at || "candidate"}-${index}`,
      status,
      score,
      title: firstLine(candidate.edited) || candidate.source_name || "Learning candidate",
      evidence: engagement
        ? `likes ${engagement.likes}, reposts ${engagement.reposts}, shares ${engagement.shares}, comments ${engagement.comments}, visits ${engagement.visits}`
        : "No matched post metrics yet.",
      proposedLearning: `- ${concise}`,
      proposedSkill: {
        name: "research_workflow_crystallized_from_edit",
        trigger: "Use when a user edit improves hook, structure, or reusable unit clarity.",
        minimalToolset: ["candidate", "draft", "quality_gate", "publish_metrics"],
        crystallizedPath: [
          "Start with two draft variants.",
          "Compare local quality and dry-run output.",
          "Save user edit diff as a learning candidate.",
          "Match the edit to post metrics.",
          "Promote only if weighted engagement clears the threshold.",
        ],
      },
    };
  });
}

export function buildSkillTree(learnings: string, candidates: LearningCandidate[], metrics: MetricRow[]) {
  const strongest = [...metrics].sort((a, b) => engagementScore(b).weighted - engagementScore(a).weighted)[0];
  return {
    root: "GenericAgent-style Threads execution harness",
    minimalToolset: ["collect_candidates", "draft_ab", "quality_gate", "publish_dispatch"],
    crystallizedSkills: [
      "citation_verification",
      "agent_role_split",
      "source_to_workflow_template",
      ...candidates.slice(-3).map((candidate) => firstLine(candidate.edited).slice(0, 48)).filter(Boolean),
    ],
    currentRules: learnings
      .split(/\r?\n/)
      .filter((line) => line.trim().startsWith("- "))
      .slice(0, 8),
    strongestSignal: strongest
      ? `${strongest.hook || strongest.thread_url}: weighted ${engagementScore(strongest).weighted}`
      : "No metrics yet.",
  };
}

export function candidateStyleHints(candidates: LearningCandidate[]) {
  const latest = [...candidates].reverse().find((candidate) => candidate.edited);
  if (!latest?.edited) return [];
  const edited = latest.edited;
  const hints = [
    `recent_edit_hook=${firstLine(edited)}`,
    edited.includes("오늘 적용할 문장:") ? "keep_label=오늘 적용할 문장" : "",
    edited.includes("- 볼 부분:") ? "keep_source_inspection_label=true" : "",
    edited.split(/\n---\n/g).length ? `preferred_parts=${edited.split(/\n---\n/g).length}` : "",
  ].filter(Boolean);
  return hints;
}
