import { Octokit } from "@octokit/rest";
import { repoConfig } from "./config";

function octokit() {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (!token) {
    throw new Error("GITHUB_TOKEN or GH_TOKEN is required for dashboard API access.");
  }
  return new Octokit({ auth: token });
}

export async function readRepoText(path: string) {
  const client = octokit();
  const response = await client.repos.getContent({
    ...repoConfig,
    path,
    ref: repoConfig.branch,
  });
  if (Array.isArray(response.data) || response.data.type !== "file") {
    throw new Error(`${path} is not a file.`);
  }
  return Buffer.from(response.data.content, "base64").toString("utf8");
}

export async function readRepoJson<T>(path: string, fallback: T): Promise<T> {
  try {
    return JSON.parse(await readRepoText(path)) as T;
  } catch {
    return fallback;
  }
}

export async function appendRepoText(path: string, appendText: string, message: string) {
  const client = octokit();
  let current = "";
  let sha: string | undefined;
  try {
    const response = await client.repos.getContent({
      ...repoConfig,
      path,
      ref: repoConfig.branch,
    });
    if (!Array.isArray(response.data) && response.data.type === "file") {
      current = Buffer.from(response.data.content, "base64").toString("utf8");
      sha = response.data.sha;
    }
  } catch (error: unknown) {
    const status = typeof error === "object" && error && "status" in error ? (error as { status?: number }).status : undefined;
    if (status !== 404) {
      throw error;
    }
  }

  await client.repos.createOrUpdateFileContents({
    ...repoConfig,
    path,
    branch: repoConfig.branch,
    message,
    content: Buffer.from(current + appendText).toString("base64"),
    sha,
  });
}

export async function dispatchWorkflow(workflowId: string, inputs: Record<string, string | boolean>) {
  const client = octokit();
  await client.actions.createWorkflowDispatch({
    ...repoConfig,
    workflow_id: workflowId,
    ref: repoConfig.branch,
    inputs,
  });
}
