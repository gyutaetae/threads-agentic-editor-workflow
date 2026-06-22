import { NextResponse } from "next/server";
import { kstDate, repoConfig } from "@/lib/config";
import { readRepoJson, readRepoText } from "@/lib/github";
import { Candidate, createDraftOptions } from "@/lib/workflow";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const date = url.searchParams.get("date") || kstDate();
  const candidatesPath = `daily-editor/${date}-candidates.json`;
  const candidates = await readRepoJson<Candidate[]>(candidatesPath, []);
  const drafts = createDraftOptions(candidates);
  const historyText = await readRepoText("content-history.jsonl").catch(() => "");
  const recentHistory = historyText
    .split(/\r?\n/)
    .filter(Boolean)
    .slice(-6)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean);

  return NextResponse.json({
    date,
    repo: repoConfig,
    candidatesPath,
    candidateCount: candidates.length,
    candidates: candidates.slice(0, 5),
    drafts,
    recentHistory,
    config: {
      autoPublishThreshold: Number(process.env.AUTO_PUBLISH_THRESHOLD || 90),
      dashboardSecretEnabled: Boolean(process.env.DASHBOARD_SECRET),
    },
  });
}
