import { NextResponse } from "next/server";
import { requireDashboardSecret } from "@/lib/config";
import { dispatchWorkflow } from "@/lib/github";
import { qualityScore } from "@/lib/workflow";

export async function POST(request: Request) {
  requireDashboardSecret(request);
  const body = (await request.json()) as {
    threadText: string;
    dryRun?: boolean;
    autoPublish?: boolean;
    topic?: string;
    sourceCount?: number;
    format?: string;
    sourceName?: string;
    sourceUrl?: string;
  };
  const quality = qualityScore(body.threadText || "");
  const threshold = Number(process.env.AUTO_PUBLISH_THRESHOLD || 90);
  const dryRun = body.autoPublish ? quality.score < threshold : body.dryRun !== false;
  if (body.autoPublish && !quality.passed) {
    return NextResponse.json({ ok: false, blocked: true, quality }, { status: 422 });
  }

  await dispatchWorkflow("publish-thread.yml", {
    thread_text: body.threadText,
    dry_run: dryRun,
    topic: body.topic || "research ai workflow",
    source_count: String(body.sourceCount ?? 1),
    format: body.format || "workflow_mode",
    source_name: body.sourceName || "",
    source_url: body.sourceUrl || "",
    card_used: false,
  });

  return NextResponse.json({
    ok: true,
    dryRun,
    autoPublish: Boolean(body.autoPublish),
    quality,
  });
}
