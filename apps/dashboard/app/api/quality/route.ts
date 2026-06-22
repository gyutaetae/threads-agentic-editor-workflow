import { NextResponse } from "next/server";
import { qualityScore } from "@/lib/workflow";

export async function POST(request: Request) {
  const body = (await request.json()) as { threadText: string };
  return NextResponse.json(qualityScore(body.threadText || ""));
}
