import { NextResponse } from "next/server";
import { readRepoText } from "@/lib/github";
import { LearningCandidate, buildPromotionSuggestions, parseCsv, parseJsonl } from "@/lib/analytics";

export async function GET() {
  const learningText = await readRepoText("daily-editor/proposals/dashboard-learning-candidates.jsonl").catch(() => "");
  const metricsText = await readRepoText("threads-post-metrics.csv").catch(() => "");
  const learningsText = await readRepoText("docs/learnings.md").catch(() => "");
  const suggestions = buildPromotionSuggestions(
    parseJsonl<LearningCandidate>(learningText),
    parseCsv(metricsText),
    learningsText,
  );
  return NextResponse.json({ suggestions });
}
