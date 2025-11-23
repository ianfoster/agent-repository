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
};

export type HealthResponse = {
  status: string;
  service: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const resp = await fetch("/api/health");
  if (!resp.ok) {
    throw new Error(`Health check failed: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchAgents(): Promise<Agent[]> {
  const resp = await fetch("/api/agents");
  if (!resp.ok) {
    throw new Error(`Failed to fetch agents: ${resp.status}`);
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
    }
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

