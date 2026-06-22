import { NextResponse } from "next/server";
import { kstDate, requireDashboardSecret } from "@/lib/config";
import { appendRepoText } from "@/lib/github";
import { summarizeDiff } from "@/lib/workflow";

export async function POST(request: Request) {
  requireDashboardSecret(request);
  const body = (await request.json()) as {
    original: string;
    edited: string;
    draftId?: string;
    note?: string;
  };
  const entry = {
    created_at: new Date().toISOString(),
    date: kstDate(),
    draft_id: body.draftId || "",
    note: body.note || "",
    diff_summary: summarizeDiff(body.original || "", body.edited || ""),
    original: body.original || "",
    edited: body.edited || "",
    status: "candidate",
    promotion_rule: "Promote only after published metrics show the edit was useful.",
  };
  await appendRepoText(
    "daily-editor/proposals/dashboard-learning-candidates.jsonl",
    `${JSON.stringify(entry)}\n`,
    "Record dashboard learning candidate",
  );
  return NextResponse.json({ ok: true, entry });
}
