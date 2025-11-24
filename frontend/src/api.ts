export type A2ASkill = {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  inputModes: string[];
  outputModes: string[];
  examples: any[];
};

export type A2AAgentCard = {
  name: string;
  url: string;
  description?: string;
  version: string;
  protocolVersion?: string;
  capabilities: Record<string, any>;
  skills: A2ASkill[];
  defaultInputModes: string[];
  defaultOutputModes: string[];
  supportsAuthenticatedExtendedCard: boolean;
  securitySchemes?: Record<string, any>;
  security?: Record<string, any>[];
};

export type Agent = {
  id: string;
  name: string;
  version: string;
  description: string;
  agent_type: string;
  tags: string[];
  owner?: string | null;
  created_at: string;
  a2a_card?: A2AAgentCard;
  git_repo?: string | null;
  git_commit?: string | null;
  container_image?: string | null;
  entrypoint?: string | null;
  validation_status: string;
  last_validated_at?: string | null;
  validation_score?: number | null;
};

export type HealthResponse = {
  status: string;
  service: string;
};

export type AgentFilters = {
  name?: string;
  agent_type?: string;
  tag?: string;
  owner?: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const resp = await fetch("/api/health");
  if (!resp.ok) {
    throw new Error(`Health check failed: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchAgents(filters?: AgentFilters): Promise<Agent[]> {
  const params = new URLSearchParams();
  if (filters?.name) params.set("name", filters.name);
  if (filters?.agent_type) params.set("agent_type", filters.agent_type);
  if (filters?.tag) params.set("tag", filters.tag);
  if (filters?.owner) params.set("owner", filters.owner);

  const query = params.toString();
  const url = query ? `/api/agents?${query}` : "/api/agents";

  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`Failed to fetch agents: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchAgent(id: string): Promise<Agent> {
  const resp = await fetch(`/api/agents/${id}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch agent ${id}: ${resp.status}`);
  }
  return resp.json();
}

export async function createSampleAgent(): Promise<Agent> {
  const payload = {
    name: "frontend-sample-agent",
    version: "0.1.0",
    description: "Sample agent created from the web UI.",
    agent_type: "task",
    tags: ["sample", "frontend"],
    inputs: {},
    outputs: {},
    owner: "web-ui",
    a2a_card: {
      name: "frontend-sample-agent",
      url: "http://localhost:8000/a2a/frontend-sample-agent",
      description: "Sample A2A card from the web UI.",
      version: "0.1.0",
      protocolVersion: "0.2.6",
      capabilities: {},
      skills: [],
      defaultInputModes: ["text/plain"],
      defaultOutputModes: ["text/plain"],
      supportsAuthenticatedExtendedCard: false
    },
    git_repo: "https://github.com/example/frontend-sample-agent",
    git_commit: "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    container_image: "ghcr.io/example/frontend-sample-agent:0.1.0",
    entrypoint: "agents.frontend:SampleAgent"
  };

  const resp = await fetch("/api/agents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Failed to create agent: ${resp.status} ${text}`);
  }

  return resp.json();
}


export async function validateAgent(id: string, score?: number): Promise<Agent> {
  const params = new URLSearchParams();
  if (typeof score === "number") {
    params.set("score", String(score));
  }
  const query = params.toString();
  const url = query ? `/api/agents/${id}/validate?${query}` : `/api/agents/${id}/validate`;

  const resp = await fetch(url, {
    method: "POST"
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Failed to validate agent: ${resp.status} ${text}`);
  }

  return resp.json();
}

