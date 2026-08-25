import {
  Customer,
  Opportunity,
  CampaignLaunchResult,
  ExperimentMetrics,
  SnapshotData,
  WebhookEventRecord,
} from "@/types";

const getApiBase = () => {
  if (typeof window !== "undefined") {
    // In browser, talk directly to backend port 8000 for maximum speed & reliability
    return "http://127.0.0.1:8000/api/v1";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
};

async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const base = getApiBase();
  const fullUrl = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  try {
    const res = await fetch(fullUrl, options);
    if (!res.ok) {
      // If direct failed, try relative /api/v1 proxy as fallback
      const fallbackUrl = `/api/v1${path.startsWith("/") ? path : `/${path}`}`;
      return await fetch(fallbackUrl, options);
    }
    return res;
  } catch (err) {
    // Retry with relative proxy
    const fallbackUrl = `/api/v1${path.startsWith("/") ? path : `/${path}`}`;
    return await fetch(fallbackUrl, options);
  }
}

export async function generateSimulation(
  merchantName: string = "StyleKart",
  customerCount: number = 500,
  orderCount: number = 2000,
  sessionId?: string
): Promise<{ status: string; data: SnapshotData }> {
  const path = `/simulator/generate?merchant_name=${encodeURIComponent(
    merchantName
  )}&customer_count=${customerCount}&order_count=${orderCount}${
    sessionId ? `&session_id=${encodeURIComponent(sessionId)}` : ""
  }`;
  const res = await apiFetch(path, { method: "POST" });
  if (!res.ok) throw new Error(`Simulation failed: ${res.statusText}`);
  return res.json();
}

export async function loadLocalSimulation(
  sessionId?: string
): Promise<{ status: string; data: SnapshotData }> {
  const path = `/simulator/load-from-local${
    sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ""
  }`;
  const res = await apiFetch(path, { method: "POST" });
  if (!res.ok) throw new Error(`Loading local dataset failed: ${res.statusText}`);
  return res.json();
}

export async function getLocalSnapshot(): Promise<{ status: string; data: SnapshotData }> {
  const res = await apiFetch(`/simulator/local-snapshot`);
  if (!res.ok) throw new Error(`Snapshot retrieval failed: ${res.statusText}`);
  return res.json();
}

export async function scanOpportunities(
  merchantId: string,
  sessionId?: string
): Promise<{
  status: string;
  opportunities_found: number;
  opportunities: Opportunity[];
  action_plan?: {
    opportunity_title: string;
    ai_reasoning: string;
    target_segment: string;
    estimated_gmv: number;
  };
}> {
  const path = `/growth/scan/${merchantId}${
    sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ""
  }`;
  const res = await apiFetch(path, { method: "POST" });
  if (!res.ok) throw new Error(`Opportunity scan failed: ${res.statusText}`);
  return res.json();
}

export async function agenticScanOpportunities(
  merchantId: string,
  sessionId?: string
): Promise<import("@/types").AgenticScanResponse> {
  const path = `/growth/agentic-scan/${merchantId}${
    sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ""
  }`;
  const res = await apiFetch(path, { method: "POST" });
  if (!res.ok) throw new Error(`Agentic scan failed: ${res.statusText}`);
  return res.json();
}

export async function launchCampaign(
  opportunityId: string,
  options?: {
    bypassPermissionGate?: boolean;
    maxAudienceCap?: number;
    sessionId?: string;
  }
): Promise<CampaignLaunchResult> {
  const params = new URLSearchParams();
  if (options?.bypassPermissionGate) {
    params.set("bypass_permission_gate", "true");
  }
  if (options?.maxAudienceCap) {
    params.set("max_audience_cap", options.maxAudienceCap.toString());
  }
  if (options?.sessionId) {
    params.set("session_id", options.sessionId);
  }

  const queryString = params.toString() ? `?${params.toString()}` : "";
  const res = await apiFetch(
    `/campaigns/launch/${opportunityId}${queryString}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`Campaign launch failed: ${res.statusText}`);
  return res.json();
}

export async function triggerWebhookPayment(
  campaignId: string,
  customerId: string,
  amount: number = 2850.0,
  sessionId?: string,
  variant: "treatment" | "control" = "treatment",
  orderId?: string,
): Promise<{
  status: string;
  payment_id: string;
  campaign_id: string;
  customer_id: string;
  metrics: ExperimentMetrics;
}> {
  const params = new URLSearchParams({
    campaign_id: campaignId,
    customer_id: customerId,
    amount: amount.toString(),
    variant,
  });
  if (orderId) params.set("order_id", orderId);
  if (sessionId) params.set("session_id", sessionId);

  const res = await apiFetch(`/experiments/webhook-payment?${params.toString()}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Webhook payment recording failed: ${res.statusText}`);
  return res.json();
}

export async function getExperimentResults(
  campaignId: string,
  sessionId?: string
): Promise<{ status: string; metrics: ExperimentMetrics }> {
  const path = `/experiments/results/${campaignId}${
    sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ""
  }`;
  const res = await apiFetch(path);
  if (!res.ok) throw new Error(`Failed to fetch experiment metrics: ${res.statusText}`);
  return res.json();
}

export async function listCustomers(
  merchantId: string,
  limit: number = 100
): Promise<Customer[]> {
  const path = `/customers/?merchant_id=${encodeURIComponent(merchantId)}&limit=${limit}`;
  const res = await apiFetch(path);
  if (!res.ok) throw new Error(`Failed to fetch customers: ${res.statusText}`);
  return res.json();
}

export async function getLatestTrace(sessionId?: string): Promise<any> {
  const path = `/growth/latest-trace${
    sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ""
  }`;
  const res = await apiFetch(path);
  if (!res.ok) return null;
  return res.json();
}

export async function getRecentWebhooks(): Promise<{
  total: number;
  events: WebhookEventRecord[];
}> {
  const res = await apiFetch(`/webhooks/recent`);
  if (!res.ok) return { total: 0, events: [] };
  return res.json();
}

export async function simulateWebhookEvent(
  campaignId: string,
  customerId: string,
  amount: number = 2850,
  sessionId?: string,
  variant: "treatment" | "control" = "treatment",
  orderId?: string,
): Promise<any> {
  const params = new URLSearchParams({
    campaign_id: campaignId,
    customer_id: customerId,
    amount: amount.toString(),
    variant,
  });
  if (orderId) params.set("order_id", orderId);
  if (sessionId) params.set("session_id", sessionId);

  const res = await apiFetch(
    `/webhooks/simulate-test-event?${params.toString()}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`Simulate webhook event failed: ${res.statusText}`);
  return res.json();
}

export async function chatWithGrowthAgent(
  merchantId: string,
  query: string,
  sessionId?: string
): Promise<{
  status: string;
  reply: string;
  suggested_action?: string;
  suggested_follow_up?: string;
  reasoning_trace?: string;
  provider_used?: string;
  tools_used?: string[];
  tool_data?: Record<string, any>;
}> {
  const res = await apiFetch(`/growth/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      merchant_id: merchantId,
      session_id: sessionId,
      query,
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);
  return res.json();
}

export type ChatStreamEvent =
  | { type: "tools"; tools_used: string[]; tool_data: Record<string, any> }
  | { type: "reasoning"; content: string }
  | { type: "token"; content: string }
  | {
      type: "done";
      reply: string;
      provider_used?: string;
      tools_used?: string[];
      tool_data?: Record<string, any>;
    }
  | { type: "error"; message: string };

/**
 * Streams a strategist answer over SSE, invoking onEvent for each frame.
 * Uses POST (EventSource cannot POST), so it reads the body as a byte stream.
 */
export async function streamChatWithGrowthAgent(
  merchantId: string,
  query: string,
  sessionId: string | undefined,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  const res = await apiFetch(`/growth/chat-stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ merchant_id: merchantId, session_id: sessionId, query }),
  });
  if (!res.ok || !res.body) throw new Error(`Chat stream failed: ${res.statusText}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line; keep any partial tail in the buffer.
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;
      const payload = line.slice(6).trim();
      if (payload === "[DONE]") return;
      try {
        onEvent(JSON.parse(payload) as ChatStreamEvent);
      } catch {
        // Ignore malformed frames rather than aborting the whole stream.
      }
    }
  }
}

export async function listSessions(): Promise<{
  status: string;
  total_sessions: number;
  sessions: Array<{
    session_id: string;
    merchant_id: string;
    last_updated: string;
    top_opportunity: string;
    campaign_id?: string;
    total_audience: number;
    has_experiment: boolean;
    lift_display: string;
    incremental_gmv: number;
  }>;
}> {
  const res = await apiFetch(`/growth/sessions`);
  if (!res.ok) throw new Error(`List sessions failed: ${res.statusText}`);
  return res.json();
}

export async function crossReferenceSessions(
  currentSessionId: string,
  targetSessionId?: string,
  query?: string
): Promise<{
  status: string;
  current_session_id: string;
  target_session_id?: string;
  comparison_narrative: string;
  current_metrics: Record<string, any>;
  target_metrics: Record<string, any>;
  vector_memories: Array<{ id?: string; summary: string; metadata?: Record<string, any> }>;
}> {
  const res = await apiFetch(`/growth/cross-reference`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_session_id: currentSessionId,
      target_session_id: targetSessionId,
      query: query || "Compare conversion lift and revenue recovery across sessions.",
    }),
  });
  if (!res.ok) throw new Error(`Cross-referencing failed: ${res.statusText}`);
  return res.json();
}
