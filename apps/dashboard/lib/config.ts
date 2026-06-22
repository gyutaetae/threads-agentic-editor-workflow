export const repoConfig = {
  owner: process.env.GITHUB_OWNER || "gyutaetae",
  repo: process.env.GITHUB_REPO || "threads-agentic-editor-workflow",
  branch: process.env.GITHUB_BRANCH || "master",
};

export function requireDashboardSecret(request: Request) {
  const expected = process.env.DASHBOARD_SECRET;
  if (!expected) {
    return;
  }
  const supplied = request.headers.get("x-dashboard-secret");
  if (supplied !== expected) {
    throw new Response("Unauthorized", { status: 401 });
  }
}

export function kstDate(input = new Date()) {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(input);
}
