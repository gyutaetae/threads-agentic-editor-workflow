import { NextResponse } from "next/server";
import { requireDashboardSecret } from "@/lib/config";
import { dispatchWorkflow } from "@/lib/github";
import { qualityScore } from "@/lib/workflow";

type CompareDraft = {
  id: string;
  threadText: string;
  sourceName?: string;
  sourceUrl?: string;
};

export async function POST(request: Request) {
  requireDashboardSecret(request);
  const body = (await request.json()) as { drafts: CompareDraft[] };
  const drafts = (body.drafts || []).slice(0, 2);
  const ranking = drafts
    .map((draft) => ({ id: draft.id, quality: qualityScore(draft.threadText) }))
    .sort((a, b) => b.quality.score - a.quality.score);

  await Promise.all(
    drafts.map((draft) =>
      dispatchWorkflow("publish-thread.yml", {
        thread_text: draft.threadText,
        dry_run: true,
        topic: "research ai workflow compare",
        source_count: "1",
        format: `compare_${draft.id}`,
        source_name: draft.sourceName || "",
        source_url: draft.sourceUrl || "",
        card_used: false,
      }),
    ),
  );

  return NextResponse.json({ ok: true, ranking });
}
