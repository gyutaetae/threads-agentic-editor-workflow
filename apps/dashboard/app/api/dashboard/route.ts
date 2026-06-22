import { NextResponse } from "next/server";
import { kstDate, repoConfig } from "@/lib/config";
import { readRepoJson, readRepoText } from "@/lib/github";
import { Candidate, createDraftOptions } from "@/lib/workflow";
import {
  LearningCandidate,
  buildPromotionSuggestions,
  buildSkillTree,
  candidateStyleHints,
  engagementScore,
  parseCsv,
  parseJsonl,
  rankDrafts,
} from "@/lib/analytics";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const date = url.searchParams.get("date") || kstDate();
  const candidatesPath = `daily-editor/${date}-candidates.json`;
  const candidates = await readRepoJson<Candidate[]>(candidatesPath, []);
  const learningText = await readRepoText("daily-editor/proposals/dashboard-learning-candidates.jsonl").catch(() => "");
  const learningCandidates = parseJsonl<LearningCandidate>(learningText);
  const learningsText = await readRepoText("docs/learnings.md").catch(() => "");
  const styleHints = candidateStyleHints(learningCandidates);
  const drafts = createDraftOptions(candidates, styleHints, learningsText);
  const metricsText = await readRepoText("threads-post-metrics.csv").catch(() => "");
  const metrics = parseCsv(metricsText)
    .map((row) => ({ ...row, engagement: engagementScore(row) }))
    .reverse()
    .slice(0, 20);
  const historyText = await readRepoText("content-history.jsonl").catch(() => "");
  const recentHistory = historyText
    .split(/\r?\n/)
    .filter(Boolean)
    .slice(-8)
    .map((line) => {
      try {
        const item = JSON.parse(line);
        const firstPostId = Array.isArray(item.post_ids) ? item.post_ids[0] : "";
        const threadUrl = item.thread_url || (firstPostId ? `https://www.threads.net/@arxiv.ai/post/${firstPostId}` : "");
        return { ...item, thread_url: threadUrl };
      } catch {
        return null;
      }
    })
    .filter(Boolean)
    .reverse();
  const promotionSuggestions = buildPromotionSuggestions(learningCandidates, parseCsv(metricsText), learningsText);

  return NextResponse.json({
    date,
    repo: repoConfig,
    candidatesPath,
    candidateCount: candidates.length,
    candidates: candidates.slice(0, 5),
    drafts,
    draftRanking: rankDrafts(drafts),
    metrics,
    learningCandidates: learningCandidates.slice(-20).reverse(),
    promotionSuggestions: promotionSuggestions.slice(0, 6),
    skillTree: buildSkillTree(learningsText, learningCandidates, parseCsv(metricsText)),
    learnings: learningsText
      .split(/\r?\n/)
      .filter((line) => line.trim().startsWith("- "))
      .slice(0, 12),
    recentHistory,
    config: {
      autoPublishThreshold: Number(process.env.AUTO_PUBLISH_THRESHOLD || 85),
      dashboardSecretEnabled: Boolean(process.env.DASHBOARD_SECRET),
    },
  });
}
