import { NextResponse } from "next/server";
import { requireDashboardSecret } from "@/lib/config";
import { appendRepoText } from "@/lib/github";
import { buildLearningCandidates } from "@/lib/analytics";

export async function POST(request: Request) {
  requireDashboardSecret(request);
  const body = (await request.json()) as {
    original: string;
    edited: string;
    draftId?: string;
    sourceUrl?: string;
    sourceName?: string;
    score?: number;
    note?: string;
  };
  const entry = buildLearningCandidates(body.original || "", body.edited || "", {
    id: body.draftId === "B" ? "B" : "A",
    label: "",
    candidateTitle: body.sourceName || "",
    sourceUrl: body.sourceUrl || "",
    score: body.score || 0,
    styleHints: [],
    threadText: body.original || "",
  }, body.note || "");
  await appendRepoText(
    "daily-editor/proposals/dashboard-learning-candidates.jsonl",
    `${JSON.stringify(entry)}\n`,
    "Record dashboard learning candidate",
  );
  return NextResponse.json({ ok: true, entry });
}
