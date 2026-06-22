export type Candidate = {
  title?: string;
  name?: string;
  url?: string;
  description?: string;
  readme_summary?: string;
  our_angle?: string;
  content_axis?: string;
  format_type?: string;
  post_goal?: string;
  source_type?: string;
  score?: { total?: number; final_score?: number } | number;
};

export type DraftOption = {
  id: "A" | "B";
  label: string;
  candidateTitle: string;
  sourceUrl: string;
  score: number;
  styleHints: string[];
  threadText: string;
};

function scoreOf(candidate: Candidate) {
  if (typeof candidate.score === "number") return candidate.score;
  return Number(candidate.score?.total || candidate.score?.final_score || 0);
}

function sourceTitle(candidate: Candidate) {
  return candidate.title || candidate.name || "today source";
}

export function createDraftOptions(candidates: Candidate[], styleHints: string[] = [], learningsText = ""): DraftOption[] {
  const ranked = [...candidates].sort((a, b) => scoreOf(b) - scoreOf(a));
  return ranked.slice(0, 2).map((candidate, index) => {
    const id = index === 0 ? "A" : "B";
    const title = sourceTitle(candidate);
    const sourceUrl = candidate.url || "";
    const angle = candidate.our_angle || "AI research workflow를 검증 가능한 작업 단위로 나누는 법";
    const problem = angle.includes("citation")
      ? "AI가 붙인 citation이 claim을 실제로 받치는지 검증하기 어렵습니다."
      : "AI에게 연구 작업을 한 번에 맡기면 결과가 그럴듯한 글로 끝나기 쉽습니다.";
    const reusable = angle.includes("related work")
      ? "\"관련 논문을 contribution, method, evidence, limitation 기준으로 비교표에 넣어줘.\""
      : "\"이 논문 작업을 reader, synthesizer, critic, citation checker로 나눠줘. 각 역할은 output, evidence, failure mode를 따로 적어줘.\"";
    const learnedLabel = styleHints.includes("keep_label=오늘 적용할 문장") ? "오늘 적용할 문장:" : "바로 써볼 문장:";
    const sourceLabel = styleHints.includes("keep_source_inspection_label=true") || learningsText.includes("- 볼 부분:")
      ? "- 볼 부분:"
      : "- 확인할 부분:";

    return {
      id,
      label: id === "A" ? "Broad hook" : "Deeper workflow",
      candidateTitle: title,
      sourceUrl,
      score: scoreOf(candidate),
      styleHints,
      threadText: [
        [
          id === "A" ? "AI 연구 도구를 볼 때" : `${title}에서 봐야 할 것은`,
          id === "A" ? "기능 개수부터 세면 금방 길을 잃습니다." : "기능 목록보다 작업을 어떻게 나누는지입니다.",
          "",
          problem,
        ].join("\n"),
        [
          "한 요청으로 뭉개면 읽기, 비교, 비판, 작성, 검증이 섞입니다.",
          "",
          "좋은 research workflow는 답을 빨리 받는 구조가 아니라",
          "검증할 수 있는 중간 산출물을 남기는 구조입니다.",
        ].join("\n"),
        [learnedLabel, "", reusable, "", "이렇게 시키면 글보다 먼저 검토 가능한 연구 노트가 나옵니다."].join("\n"),
        [
          "참고해서 볼 만한 것:",
          sourceUrl,
          `${sourceLabel} ${title}에서 연구 작업을 작은 단위로 나누는 방식`,
          "",
          "GitHub stars는 인기 신호일 뿐이고,",
          "연구 품질 증거로 쓰면 안 됩니다.",
        ].join("\n"),
      ].join("\n---\n"),
    };
  });
}

export function qualityScore(threadText: string) {
  const parts = threadText.split(/\n---\n/g).map((part) => part.trim()).filter(Boolean);
  const joined = parts.join("\n");
  const first = parts[0] || "";
  const firstLine = first.split(/\r?\n/).find((line) => line.trim())?.trim() || "";
  let score = 0;
  const reasons: string[] = [];
  const textLength = joined.replace(/\s/g, "").length;
  const koreanChars = (joined.match(/[가-힣]/g) || []).length;
  const workflowTerms = (joined.match(/claim|evidence|citation|limitation|workflow|prompt|AI agent|reader|critic|검증|근거|논문|연구/g) || []).length;

  if (/asdasd|asdf|qwer|test|테스트만|아무말/i.test(joined) || textLength < 160 || koreanChars < 45) {
    return {
      score: Math.min(20, Math.max(0, Math.floor(textLength / 10))),
      passed: false,
      reasons: ["Too short or looks like placeholder text."],
    };
  }

  if (parts.length >= 2 && parts.length <= 4) {
    score += 14;
  } else {
    reasons.push("Thread should have 2-4 parts.");
  }

  const partLengthsOk = parts.every((part) => part.length >= 45 && part.length <= 500);
  if (partLengthsOk) {
    score += 14;
  } else {
    reasons.push("Every part should be 45-500 chars.");
  }

  if (textLength >= 260 && textLength <= 1500) {
    score += 12;
  } else {
    reasons.push("Total text needs enough substance without becoming too long.");
  }

  if (firstLine.length >= 10 && firstLine.length <= 55 && !/^AI 시대|^요즘 AI|^오늘은/.test(firstLine)) {
    score += 12;
  } else {
    reasons.push("Hook should be concrete and not generic.");
  }

  if (!/https?:\/\//.test(first)) {
    score += 8;
  } else {
    reasons.push("Main post contains a link.");
  }

  if (/https?:\/\//.test(threadText) && !threadText.includes("- 볼 부분:") && !threadText.includes("인용 원문:")) {
    reasons.push("Source link needs '- 볼 부분:' or '인용 원문:'.");
  } else {
    score += 10;
  }

  if (/(프롬프트|문장|체크리스트|기준|workflow|claim|evidence|citation|failure mode|output)/i.test(threadText)) {
    score += 14;
  } else {
    reasons.push("Thread needs a reusable work unit.");
  }

  if (workflowTerms >= 5) {
    score += 10;
  } else {
    reasons.push("Needs more concrete research workflow terms.");
  }

  if (!/(무조건|혁명|역대급|미친 생산성|뒤처집니다|끝입니다)/.test(joined)) {
    score += 8;
  } else {
    reasons.push("Avoid hype language.");
  }

  if (!/(^|\n)\s*(#|Reply\s*\d+|Main:|제목:)/i.test(joined)) {
    score += 8;
  } else {
    reasons.push("Remove draft labels or markdown headings.");
  }

  return { score: Math.min(100, Math.max(0, score)), passed: score >= 85, reasons: reasons.length ? reasons : ["Quality gate passed."] };
}

export function summarizeDiff(original: string, edited: string) {
  if (original === edited) return "No edit.";
  const originalLines = new Set(original.split(/\r?\n/).map((line) => line.trim()).filter(Boolean));
  const editedLines = edited.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const added = editedLines.filter((line) => !originalLines.has(line));
  return added.slice(0, 6).join(" / ") || "Edited wording or structure.";
}
