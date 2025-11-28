import React, { useEffect, useState, FormEvent } from "react";

type Agent = {
  id: string;
  name: string;
  version: string;
  description?: string;
  agent_type?: string;
  tags?: string[];
  owner?: string | null;
  validation_status?: string;
  last_validated_at?: string | null;
  created_at?: string;
  updated_at?: string;
};

type Location = {
  id: string;
  name: string;
  location_type: string;
  config: Record<string, any>;
  is_active: boolean;
  created_at?: string;
};

type Deployment = {
  id: string;
  agent_id: string;
  location_id: string;
  status: string;
  last_error?: string | null;
  local_path?: string | null;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
};

type Instance = {
  instance_id: string;
  agent_id: string;
  status: string;
  location_name?: string;
  lastResult?: any;
};

type Tab = "agents" | "locations" | "deployments";

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("agents");

  // Health
  const [health, setHealth] = useState<{ status: string; service: string } | null>(
    null
  );
  const [healthError, setHealthError] = useState<string | null>(null);

  // Agents
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentsLoading, setAgentsLoading] = useState(false);
  const [agentsError, setAgentsError] = useState<string | null>(null);

  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentVersion, setNewAgentVersion] = useState("0.1.0");
  const [newAgentDescription, setNewAgentDescription] = useState("");
  const [newAgentType, setNewAgentType] = useState("task");
  const [newAgentOwner, setNewAgentOwner] = useState("");
  const [newAgentTags, setNewAgentTags] = useState("");
  const [newAgentGitRepo, setNewAgentGitRepo] = useState("");
  const [newAgentGitCommit, setNewAgentGitCommit] = useState("");
  const [newAgentEntrypoint, setNewAgentEntrypoint] = useState("");

  const [registerAgentBusy, setRegisterAgentBusy] = useState(false);

  // Locations
  const [locations, setLocations] = useState<Location[]>([]);
  const [locationsLoading, setLocationsLoading] = useState(false);
  const [locationsError, setLocationsError] = useState<string | null>(null);

  const [newLocationName, setNewLocationName] = useState("");
  const [newLocationType, setNewLocationType] = useState("local");
  const [newLocationConfig, setNewLocationConfig] = useState<string>("{}");
  const [registerLocationBusy, setRegisterLocationBusy] = useState(false);

  // Deployments
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [deploymentsLoading, setDeploymentsLoading] = useState(false);
  const [deploymentsError, setDeploymentsError] = useState<string | null>(null);

  const [deployAgentId, setDeployAgentId] = useState<string>("");
  const [deployLocationId, setDeployLocationId] = useState<string>("");
  const [deployBusy, setDeployBusy] = useState(false);

  // Instances (Phase 3)
  const [instances, setInstances] = useState<Instance[]>([]);
  const [instancesError, setInstancesError] = useState<string | null>(null);

  const [instanceAgentId, setInstanceAgentId] = useState<string>("");
  const [instanceLocationName, setInstanceLocationName] = useState<string>("");

  const [instanceInitJson, setInstanceInitJson] = useState<string>("{}");

  const [startingInstance, setStartingInstance] = useState(false);
  const [callingInstanceId, setCallingInstanceId] = useState<string | null>(null);

  const [callActionName, setCallActionName] = useState("greet");
  const [callPayloadJson, setCallPayloadJson] = useState<string>("{}");

  const readyInstanceLocations = deployments
    .filter((d) => d.agent_id === instanceAgentId && d.status === "ready")
    .map((d) => {
      const loc = locations.find((l) => l.id === d.location_id);
      return {
        locationName: loc ? loc.name : d.location_id,
        label: loc ? `${loc.name} (${loc.location_type})` : d.location_id,
      };
    });

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  async function fetchJSON<T = any>(url: string, options: RequestInit = {}): Promise<T> {
    const resp = await fetch(url, options);
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${text}`);
    }
    return resp.json();
  }

  // ---------------------------------------------------------------------------
  // Loaders
  // ---------------------------------------------------------------------------

  const loadHealth = async () => {
    try {
      const data = await fetchJSON<{ status: string; service: string }>("/api/health");
      setHealth(data);
      setHealthError(null);
    } catch (err: any) {
      setHealthError(err.message ?? String(err));
      setHealth(null);
    }
  };

  const loadAgents = async () => {
    try {
      setAgentsLoading(true);
      const data = await fetchJSON<Agent[]>("/api/agents");
      setAgents(data);
      setAgentsError(null);
      if (selectedAgent) {
        const stillThere = data.find((a) => a.id === selectedAgent.id);
        setSelectedAgent(stillThere ?? null);
      }
    } catch (err: any) {
      setAgentsError(err.message ?? String(err));
    } finally {
      setAgentsLoading(false);
    }
  };

  const loadLocations = async () => {
    try {
      setLocationsLoading(true);
      const data = await fetchJSON<Location[]>("/api/locations");
      setLocations(data);
      setLocationsError(null);
    } catch (err: any) {
      setLocationsError(err.message ?? String(err));
    } finally {
      setLocationsLoading(false);
    }
  };

  const loadDeploymentsForAgent = async (agentId: string) => {
    if (!agentId) {
      setDeployments([]);
      return;
    }
    try {
      setDeploymentsLoading(true);
      const data = await fetchJSON<Deployment[]>(
        `/api/agents/${agentId}/deployments`
      );
      setDeployments(data);
      setDeploymentsError(null);
    } catch (err: any) {
      setDeploymentsError(err.message ?? String(err));
      setDeployments([]);
    } finally {
      setDeploymentsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadHealth();
    loadAgents();
    loadLocations();
  }, []);

  // When agents list changes, reset selected agent and location
  useEffect(() => {
    setInstanceAgentId("");
    setInstanceLocationName("");
  }, [agents]);

  // Reload deployments when selected deployAgentId changes
  useEffect(() => {
    if (deployAgentId) {
      loadDeploymentsForAgent(deployAgentId);
    } else {
      setDeployments([]);
    }
  }, [deployAgentId]);

  // ---------------------------------------------------------------------------
  // Agent actions
  // ---------------------------------------------------------------------------

  const handleRegisterAgent = async (e: FormEvent) => {
    e.preventDefault();
    if (!newAgentName.trim()) {
      setAgentsError("Agent name is required.");
      return;
    }

    const payload: any = {
      name: newAgentName.trim(),
      version: newAgentVersion.trim() || "0.1.0",
      description: newAgentDescription.trim() || "(no description)",
      agent_type: newAgentType.trim() || "task",
      tags: newAgentTags
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0),
      owner: newAgentOwner.trim() || null,
      git_repo: newAgentGitRepo.trim() || null,
      git_commit: newAgentGitCommit.trim() || null,
      entrypoint: newAgentEntrypoint.trim() || null,
    };

    try {
      setRegisterAgentBusy(true);
      await fetchJSON("/api/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setNewAgentName("");
      setNewAgentVersion("0.1.0");
      setNewAgentDescription("");
      setNewAgentType("task");
      setNewAgentOwner("");
      setNewAgentTags("");
      setNewAgentGitRepo("");
      setNewAgentGitCommit("");
      setNewAgentEntrypoint("");
      await loadAgents();
    } catch (err: any) {
      setAgentsError(err.message ?? String(err));
    } finally {
      setRegisterAgentBusy(false);
    }
  };

  const handleValidateAgent = async (agent: Agent) => {
    try {
      const url = `/api/agents/${agent.id}/validate`;
      const updated = await fetchJSON<Agent>(url, { method: "POST" });
      setAgents((prev) =>
        prev.map((a) => (a.id === updated.id ? { ...a, ...updated } : a))
      );
      setSelectedAgent((prev) =>
        prev && prev.id === updated.id ? { ...prev, ...updated } : prev
      );
    } catch (err: any) {
      setAgentsError(err.message ?? String(err));
    }
  };

  const handleUnregisterAgent = async (agent: Agent) => {
    if (!window.confirm(`Unregister agent "${agent.name}"? This cannot be undone.`)) {
      return;
    }
    try {
      await fetchJSON(`/api/agents/${agent.id}`, { method: "DELETE" });
      await loadAgents();
      if (selectedAgent && selectedAgent.id === agent.id) {
        setSelectedAgent(null);
      }
    } catch (err: any) {
      setAgentsError(err.message ?? String(err));
    }
  };

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgent(agent);
  };

  // ---------------------------------------------------------------------------
  // Location actions
  // ---------------------------------------------------------------------------

  const handleRegisterLocation = async (e: FormEvent) => {
    e.preventDefault();
    if (!newLocationName.trim()) {
      setLocationsError("Location name is required.");
      return;
    }

    let configObj: Record<string, any> = {};
    if (newLocationConfig.trim()) {
      try {
        configObj = JSON.parse(newLocationConfig);
      } catch (err: any) {
        setLocationsError(
          err?.message ??
            "Failed to parse location config JSON. Ensure it is a valid JSON object."
        );
        return;
      }
    }

    const payload: any = {
      name: newLocationName.trim(),
      location_type: newLocationType.trim() || "local",
      config: configObj,
      is_active: true,
    };

    try {
      setRegisterLocationBusy(true);
      await fetchJSON("/api/locations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setNewLocationName("");
      setNewLocationType("local");
      setNewLocationConfig("{}");
      await loadLocations();
    } catch (err: any) {
      setLocationsError(err.message ?? String(err));
    } finally {
      setRegisterLocationBusy(false);
    }
  };

  const handleUnregisterLocation = async (loc: Location) => {
    if (
      !window.confirm(
        `Unregister location "${loc.name}"? This will prevent future deployments.`
      )
    ) {
      return;
    }
    try {
      await fetchJSON(`/api/locations/${loc.id}`, { method: "DELETE" });
      await loadLocations();
    } catch (err: any) {
      setLocationsError(err.message ?? String(err));
    }
  };

  // ---------------------------------------------------------------------------
  // Deployment actions
  // ---------------------------------------------------------------------------

  const handleDeploy = async (e: FormEvent) => {
    e.preventDefault();
    if (!deployAgentId) {
      setDeploymentsError("Please select an agent to deploy.");
      return;
    }
    if (!deployLocationId) {
      setDeploymentsError("Please select a location.");
      return;
    }
    setDeploymentsError(null);

    const payload = {
      agent_id: deployAgentId,
      location_id: deployLocationId,
    };

    try {
      setDeployBusy(true);
      const dep = await fetchJSON<Deployment>("/api/deployments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      // Refresh deployments for this agent (prepend new one)
      setDeployments((prev) => [dep, ...prev]);
    } catch (err: any) {
      setDeploymentsError(err.message ?? String(err));
    } finally {
      setDeployBusy(false);
    }
  };

  const handleDeleteDeployment = async (dep: Deployment) => {
    if (!window.confirm(`Delete deployment ${dep.id}?`)) {
      return;
    }
    try {
      await fetchJSON(`/api/deployments/${dep.id}`, { method: "DELETE" });
      // reload for current agent
      if (deployAgentId) {
        await loadDeploymentsForAgent(deployAgentId);
      }
    } catch (err: any) {
      setDeploymentsError(err.message ?? String(err));
    }
  };


// ---------------------------------------------------------------------------
// Instance actions (Phase 3)
// ---------------------------------------------------------------------------

  const handleStartInstance = async (e: FormEvent) => {
    e.preventDefault();
    if (!instanceAgentId || !instanceLocationName) {
      setInstancesError("Select an agent and a location name.");
      return;
    }
  
    let initInputs: Record<string, any> = {};
    if (instanceInitJson.trim()) {
      try {
        initInputs = JSON.parse(instanceInitJson);
      } catch (err: any) {
        setInstancesError("Failed to parse init JSON.");
        return;
      }
    }
  
    try {
      setStartingInstance(true);
      setInstancesError(null);
  
      const resp = await fetchJSON<{
        instance_id: string;
        agent_id: string;
        status: string;
      }>(`/api/agents/${instanceAgentId}/instances`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location_name: instanceLocationName,
          init_inputs: initInputs,
        }),
      });
  
      setInstances((prev) => [
        {
          instance_id: resp.instance_id,
          agent_id: resp.agent_id,
          status: resp.status,
          location_name: instanceLocationName,
        },
        ...prev,
      ]);
    } catch (err: any) {
      setInstancesError(err.message ?? String(err));
    } finally {
      setStartingInstance(false);
    }
  };
  
  const handleCallInstance = async (inst: Instance) => {
    let payload: Record<string, any> = {};
    if (callPayloadJson.trim()) {
      try {
        payload = JSON.parse(callPayloadJson);
      } catch {
        setInstancesError("Failed to parse call payload JSON.");
        return;
      }
    }
  
    try {
      setCallingInstanceId(inst.instance_id);
      const resp = await fetchJSON<{ result: any }>(
        `/api/instances/${inst.instance_id}/call`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: callActionName,
            payload,
          }),
        }
      );
  
      setInstances((prev) =>
        prev.map((i) =>
          i.instance_id === inst.instance_id
            ? { ...i, lastResult: resp.result }
            : i
        )
      );
    } catch (err: any) {
      setInstancesError(err.message ?? String(err));
    } finally {
      setCallingInstanceId(null);
    }
  };
  
  const handleStopInstance = async (inst: Instance) => {
    try {
      await fetchJSON(`/api/instances/${inst.instance_id}/stop`, {
        method: "POST",
      });
  
      setInstances((prev) =>
        prev.map((i) =>
          i.instance_id === inst.instance_id ? { ...i, status: "stopped" } : i
        )
      );
    } catch (err: any) {
      setInstancesError(err.message ?? String(err));
    }
  };

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  const renderHealth = () => (
    <section
      style={{
        marginBottom: "1rem",
        padding: "0.75rem",
        borderRadius: "0.5rem",
        border: "1px solid #ddd",
      }}
    >
      <h2 style={{ marginTop: 0 }}>Backend health</h2>
      {healthError && <p style={{ color: "red" }}>Error: {healthError}</p>}
      {health && !healthError ? (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            fontSize: "0.9rem",
            color: "#155724",
            background: "#d4edda",
            border: "1px solid #c3e6cb",
            borderRadius: "0.5rem",
            padding: "0.3rem 0.6rem",
            marginTop: "0.25rem",
          }}
        >
          <span style={{ fontSize: "1.1rem" }}>✅</span>
          <span>Backend is healthy</span>
        </div>
      ) : !health && !healthError ? (
        <p>Checking health…</p>
      ) : null}
    </section>
  );

  const renderAgentsTab = () => (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 2.2fr) minmax(0, 2fr)", gap: "1rem" }}>
      {/* Left: create + list */}
      <div>
        {/* Register new agent */}
        <section
          style={{
            marginBottom: "1rem",
            padding: "0.75rem",
            borderRadius: "0.5rem",
            border: "1px solid #ddd",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Register new agent implementation</h2>
          <form onSubmit={handleRegisterAgent}>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Name{" "}
                <input
                  type="text"
                  value={newAgentName}
                  onChange={(e) => setNewAgentName(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  required
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Version{" "}
                <input
                  type="text"
                  value={newAgentVersion}
                  onChange={(e) => setNewAgentVersion(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Type{" "}
                <input
                  type="text"
                  value={newAgentType}
                  onChange={(e) => setNewAgentType(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  placeholder="task, workflow, planner…"
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Description
                <textarea
                  value={newAgentDescription}
                  onChange={(e) => setNewAgentDescription(e.target.value)}
                  rows={3}
                  style={{
                    width: "100%",
                    padding: "0.25rem",
                    fontFamily: "inherit",
                    fontSize: "0.85rem",
                  }}
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Owner{" "}
                <input
                  type="text"
                  value={newAgentOwner}
                  onChange={(e) => setNewAgentOwner(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  placeholder="team or user"
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Tags (comma-separated){" "}
                <input
                  type="text"
                  value={newAgentTags}
                  onChange={(e) => setNewAgentTags(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  placeholder="materials, screening, example"
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Git repo{" "}
                <input
                  type="text"
                  value={newAgentGitRepo}
                  onChange={(e) => setNewAgentGitRepo(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  placeholder="https://github.com/..."
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Git commit{" "}
                <input
                  type="text"
                  value={newAgentGitCommit}
                  onChange={(e) => setNewAgentGitCommit(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  placeholder="optional SHA"
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Entrypoint{" "}
                <input
                  type="text"
                  value={newAgentEntrypoint}
                  onChange={(e) => setNewAgentEntrypoint(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  placeholder="module.path:ClassName"
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={registerAgentBusy}
              style={{
                padding: "0.4rem 0.8rem",
                borderRadius: "0.4rem",
                border: "1px solid #444",
                background: registerAgentBusy ? "#eee" : "#fff",
                cursor: registerAgentBusy ? "default" : "pointer",
                fontSize: "0.9rem",
              }}
            >
              {registerAgentBusy ? "Registering…" : "Register agent"}
            </button>
            {agentsError && (
              <div style={{ color: "red", marginTop: "0.5rem" }}>{agentsError}</div>
            )}
          </form>
        </section>

        {/* Agent list */}
        <section
          style={{
            padding: "0.75rem",
            borderRadius: "0.5rem",
            border: "1px solid #ddd",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Registered agents</h2>
          {agentsLoading ? (
            <p>Loading agents…</p>
          ) : agents.length === 0 ? (
            <p>No agents registered yet.</p>
          ) : (
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "0.9rem",
              }}
            >
              <thead>
                <tr>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Name
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Version
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Type
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Owner
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Validation
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {agents.map((a) => {
                  const isSelected = selectedAgent && selectedAgent.id === a.id;
                  const vs = a.validation_status ?? "unvalidated";
                  return (
                    <tr
                      key={a.id}
                      onClick={() => handleSelectAgent(a)}
                      style={{
                        cursor: "pointer",
                        background: isSelected ? "#eef5ff" : "transparent",
                      }}
                    >
                      <td
                        style={{
                          borderBottom: "1px solid #eee",
                          padding: "0.25rem 0.2rem",
                        }}
                      >
                        {a.name}
                      </td>
                      <td
                        style={{
                          borderBottom: "1px solid #eee",
                          padding: "0.25rem 0.2rem",
                        }}
                      >
                        {a.version}
                      </td>
                      <td
                        style={{
                          borderBottom: "1px solid #eee",
                          padding: "0.25rem 0.2rem",
                        }}
                      >
                        {a.agent_type ?? "—"}
                      </td>
                      <td
                        style={{
                          borderBottom: "1px solid #eee",
                          padding: "0.25rem 0.2rem",
                        }}
                      >
                        {a.owner ?? "—"}
                      </td>
                      <td
                        style={{
                          borderBottom: "1px solid #eee",
                          padding: "0.25rem 0.2rem",
                        }}
                      >
                        <span
                          style={{
                            padding: "0.1rem 0.45rem",
                            borderRadius: "0.75rem",
                            border: "1px solid #ccc",
                            fontSize: "0.75rem",
                            background:
                              vs === "validated"
                                ? "#e6ffed"
                                : vs === "failed"
                                ? "#ffe5e5"
                                : "#fff4e5",
                            color:
                              vs === "validated"
                                ? "#155724"
                                : vs === "failed"
                                ? "#a00"
                                : "#8a6d3b",
                          }}
                        >
                          {vs}
                        </span>
                      </td>
                      <td
                        style={{
                          borderBottom: "1px solid #eee",
                          padding: "0.25rem 0.2rem",
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          onClick={() => handleValidateAgent(a)}
                          style={{
                            padding: "0.2rem 0.5rem",
                            borderRadius: "0.4rem",
                            border: "1px solid #444",
                            background: "#fff",
                            cursor: "pointer",
                            fontSize: "0.8rem",
                            marginRight: "0.3rem",
                          }}
                        >
                          Validate
                        </button>
                        <button
                          type="button"
                          onClick={() => handleUnregisterAgent(a)}
                          style={{
                            padding: "0.2rem 0.5rem",
                            borderRadius: "0.4rem",
                            border: "1px solid #a00",
                            background: "#fff",
                            cursor: "pointer",
                            fontSize: "0.8rem",
                            color: "#a00",
                          }}
                        >
                          Unregister
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>
      </div>

      {/* Right: selected agent details */}
      <div>
        <section
          style={{
            padding: "0.75rem",
            borderRadius: "0.5rem",
            border: "1px solid #ddd",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Agent details</h2>
          {selectedAgent ? (
            <>
              <p>
                <strong>Name:</strong> {selectedAgent.name}{" "}
                <span style={{ color: "#666" }}>v{selectedAgent.version}</span>
              </p>
              <p>
                <strong>ID:</strong> {selectedAgent.id}
              </p>
              <p>
                <strong>Type:</strong> {selectedAgent.agent_type ?? "—"}
              </p>
              <p>
                <strong>Owner:</strong> {selectedAgent.owner ?? "—"}
              </p>
              <p>
                <strong>Tags:</strong>{" "}
                {selectedAgent.tags && selectedAgent.tags.length > 0
                  ? selectedAgent.tags.join(", ")
                  : "—"}
              </p>
              <p>
                <strong>Validation:</strong>{" "}
                {selectedAgent.validation_status ?? "unvalidated"}
                {selectedAgent.last_validated_at && (
                  <>
                    {" "}
                    <span style={{ color: "#666" }}>
                      (last:{" "}
                      {new Date(
                        selectedAgent.last_validated_at
                      ).toLocaleString()}
                      )
                    </span>
                  </>
                )}
              </p>
              <p>
                <strong>Description:</strong>{" "}
                {selectedAgent.description ?? "(none)"}
              </p>
              <hr />
              <details>
                <summary style={{ cursor: "pointer" }}>Raw JSON</summary>
                <pre
                  style={{
                    background: "#f7f7f7",
                    padding: "0.5rem",
                    borderRadius: "0.25rem",
                    fontSize: "0.8rem",
                    marginTop: "0.25rem",
                    maxHeight: "16rem",
                    overflow: "auto",
                  }}
                >
                  {JSON.stringify(selectedAgent, null, 2)}
                </pre>
              </details>
            </>
          ) : (
            <p>Select an agent to see details.</p>
          )}
        </section>
      </div>
    </div>
  );

  const renderLocationsTab = () => (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 2fr) minmax(0, 2fr)", gap: "1rem" }}>
      <div>
        {/* Register new location */}
        <section
          style={{
            marginBottom: "1rem",
            padding: "0.75rem",
            borderRadius: "0.5rem",
            border: "1px solid #ddd",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Register new location</h2>
          <form onSubmit={handleRegisterLocation}>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Name{" "}
                <input
                  type="text"
                  value={newLocationName}
                  onChange={(e) => setNewLocationName(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                  required
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Type{" "}
                <select
                  value={newLocationType}
                  onChange={(e) => setNewLocationType(e.target.value)}
                  style={{ width: "100%", padding: "0.25rem" }}
                >
                  <option value="local">local</option>
                  <option value="hpc">hpc</option>
                  <option value="lab">lab</option>
                  <option value="cloud">cloud</option>
                  <option value="other">other</option>
                </select>
              </label>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label>
                Config (JSON)
                <textarea
                  value={newLocationConfig}
                  onChange={(e) => setNewLocationConfig(e.target.value)}
                  rows={4}
                  style={{
                    width: "100%",
                    padding: "0.25rem",
                    fontFamily: "monospace",
                    fontSize: "0.8rem",
                  }}
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={registerLocationBusy}
              style={{
                padding: "0.4rem 0.8rem",
                borderRadius: "0.4rem",
                border: "1px solid #444",
                background: registerLocationBusy ? "#eee" : "#fff",
                cursor: registerLocationBusy ? "default" : "pointer",
                fontSize: "0.9rem",
              }}
            >
              {registerLocationBusy ? "Registering…" : "Register location"}
            </button>
            {locationsError && (
              <div style={{ color: "red", marginTop: "0.5rem" }}>{locationsError}</div>
            )}
          </form>
        </section>

        {/* Locations list */}
        <section
          style={{
            padding: "0.75rem",
            borderRadius: "0.5rem",
            border: "1px solid #ddd",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Registered locations</h2>
          {locationsLoading ? (
            <p>Loading locations…</p>
          ) : locations.length === 0 ? (
            <p>No locations registered yet.</p>
          ) : (
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "0.9rem",
              }}
            >
              <thead>
                <tr>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Name
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Type
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Active
                  </th>
                  <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {locations.map((loc) => (
                  <tr key={loc.id}>
                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "0.25rem 0.2rem",
                      }}
                    >
                      {loc.name}
                    </td>
                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "0.25rem 0.2rem",
                      }}
                    >
                      {loc.location_type}
                    </td>
                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "0.25rem 0.2rem",
                      }}
                    >
                      {loc.is_active ? "yes" : "no"}
                    </td>
                    <td
                      style={{
                        borderBottom: "1px solid #eee",
                        padding: "0.25rem 0.2rem",
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => handleUnregisterLocation(loc)}
                        style={{
                          padding: "0.2rem 0.5rem",
                          borderRadius: "0.4rem",
                          border: "1px solid #a00",
                          background: "#fff",
                          cursor: "pointer",
                          fontSize: "0.8rem",
                          color: "#a00",
                        }}
                      >
                        Unregister
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      {/* Right: placeholder for location details */}
      <div>
        <section
          style={{
            padding: "0.75rem",
            borderRadius: "0.5rem",
            border: "1px solid #ddd",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Location details</h2>
          <p>Select a location from the list to inspect its config in future phases.</p>
        </section>
      </div>
    </div>
  );

  const renderInstancesTab = () => {
    // Only locations where this agent has a READY deployment
    const readyInstanceLocations = deployments
      .filter((d) => d.agent_id === instanceAgentId && d.status === "ready")
      .map((d) => {
        const loc = locations.find((l) => l.id === d.location_id);
        const a = agents.find((x) => x.id === d.agent_id);
        return {
          locationName: loc ? loc.name : d.location_id,
        label: `${a ? a.name : d.agent_id} (v${a?.version ?? "?"}) @ ${
          loc ? loc.name : d.location_id
        }`,
      };
    });

  return (
    <section
      style={{
        marginTop: "1rem",
        padding: "1rem",
        borderRadius: "0.5rem",
        border: "1px solid #ddd",
      }}
    >
      <h2>Instances</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 2fr) minmax(0, 3fr)",
          gap: "1rem",
        }}
      >
        {/* Left: start instance form */}
        <div>
          <h3>Start a new instance</h3>
          <form onSubmit={handleStartInstance}>
            <label>
              Agent
              <select
                value={instanceAgentId}
                onChange={(e) => {
                  const id = e.target.value;
                  setInstanceAgentId(id);
                  setInstancesError(null);
                  if (id) {
                    // reuse your existing loader to fetch deployments for this agent
                    loadDeploymentsForAgent(id);
                  } else {
                    setDeployments([]);
                  }
                }}
                style={{ width: "100%", marginTop: "0.25rem" }}
              >
                <option value="">Select agent</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.version})
                  </option>
                ))}
              </select>
            </label>

            <label style={{ display: "block", marginTop: "0.75rem" }}>
              Location (with ready deployment)
              <select
                value={instanceLocationName}
                onChange={(e) => setInstanceLocationName(e.target.value)}
                style={{ width: "100%", marginTop: "0.25rem" }}
              >
                <option value="">
                  {instanceAgentId
                    ? "Select location"
                    : "Select an agent first"}
                </option>
                {readyInstanceLocations.map((t) => (
                  <option key={t.locationName} value={t.locationName}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>

            <label style={{ display: "block", marginTop: "0.75rem" }}>
              Init inputs (JSON)
              <textarea
                value={instanceInitJson}
                onChange={(e) => setInstanceInitJson(e.target.value)}
                rows={3}
                style={{
                  width: "100%",
                  marginTop: "0.25rem",
                  fontFamily: "monospace",
                  fontSize: "0.8rem",
                }}
              />
            </label>

            <button
              type="submit"
              disabled={startingInstance}
              style={{ marginTop: "0.75rem" }}
            >
              {startingInstance ? "Starting..." : "Start instance"}
            </button>

            {instancesError && (
              <p style={{ color: "red", marginTop: "0.5rem" }}>
                {instancesError}
              </p>
            )}
          </form>
        </div>

        {/* Right: running instances */}
        <div>
          <h3>Running instances (this session)</h3>
          {instances.length === 0 ? (
            <p>No instances started yet.</p>
          ) : (
            <>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.9rem",
                }}
              >
                <thead>
                  <tr>
                    <th>Instance ID</th>
                    <th>Agent</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {instances.map((inst) => {
                    const a = agents.find((x) => x.id === inst.agent_id);
                    return (
                      <tr key={inst.instance_id}>
                        <td>{inst.instance_id}</td>
                        <td>{a ? a.name : inst.agent_id}</td>
                        <td>{inst.location_name ?? "?"}</td>
                        <td>{inst.status}</td>
                        <td>
                          <button
                            onClick={() => handleCallInstance(inst)}
                            disabled={callingInstanceId === inst.instance_id}
                          >
                            {callingInstanceId === inst.instance_id
                              ? "Calling..."
                              : "Call"}
                          </button>
                          <button
                            onClick={() => handleStopInstance(inst)}
                            style={{ marginLeft: "0.5rem" }}
                          >
                            Stop
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Call config + last results */}
              <div
                style={{
                  marginTop: "1rem",
                  padding: "0.75rem",
                  borderRadius: "0.5rem",
                  border: "1px solid #eee",
                }}
              >
                <h4>Call configuration</h4>
                <label>
                  Action name
                  <input
                    type="text"
                    value={callActionName}
                    onChange={(e) => setCallActionName(e.target.value)}
                    style={{ width: "100%", marginTop: "0.25rem" }}
                  />
                </label>
                <label style={{ display: "block", marginTop: "0.75rem" }}>
                  Payload (JSON)
                  <textarea
                    value={callPayloadJson}
                    onChange={(e) => setCallPayloadJson(e.target.value)}
                    rows={3}
                    style={{
                      width: "100%",
                      marginTop: "0.25rem",
                      fontFamily: "monospace",
                      fontSize: "0.8rem",
                    }}
                  />
                </label>

                {instances.some((i) => i.lastResult !== undefined) && (
                  <div style={{ marginTop: "0.75rem" }}>
                    <h5>Last results</h5>
                    {instances.map(
                      (i) =>
                        i.lastResult !== undefined && (
                          <div
                            key={i.instance_id}
                            style={{
                              marginBottom: "0.5rem",
                              padding: "0.5rem",
                              borderRadius: "0.5rem",
                              border: "1px solid #ddd",
                              background: "#fafafa",
                            }}
                          >
                            <div
                              style={{
                                fontSize: "0.8rem",
                                color: "#555",
                                marginBottom: "0.25rem",
                              }}
                            >
                              Instance <code>{i.instance_id}</code>
                            </div>
                            <pre
                              style={{
                                margin: 0,
                                fontSize: "0.8rem",
                                whiteSpace: "pre-wrap",
                              }}
                            >
                              {JSON.stringify(i.lastResult, null, 2)}
                            </pre>
                          </div>
                        )
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
};

  const renderDeploymentsTab = () => {
    const selectedDeployAgent = agents.find((a) => a.id === deployAgentId) || null;

    return (
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 2.5fr) minmax(0, 2fr)", gap: "1rem" }}>
        {/* Left: deploy form + deployments list */}
        <div>
          {/* Deploy form */}
          <section
            style={{
              marginBottom: "1rem",
              padding: "0.75rem",
              borderRadius: "0.5rem",
              border: "1px solid #ddd",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Deploy registered implementation</h2>
            <form onSubmit={handleDeploy}>
              <div style={{ marginBottom: "0.5rem" }}>
                <label>
                  Agent{" "}
                  <select
                    value={deployAgentId}
                    onChange={(e) => {
                      setDeployAgentId(e.target.value);
                      setDeploymentsError(null);
                    }}
                    style={{ width: "100%", padding: "0.25rem" }}
                  >
                    <option value="">(select agent)</option>
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name} v{a.version}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div style={{ marginBottom: "0.5rem" }}>
                <label>
                  Location{" "}
                  <select
                    value={deployLocationId}
                    onChange={(e) => {
                      setDeployLocationId(e.target.value);
                      setDeploymentsError(null);
                    }}
                    style={{ width: "100%", padding: "0.25rem" }}
                  >
                    <option value="">(select location)</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} ({loc.location_type})
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <button
                type="submit"
                disabled={deployBusy}
                style={{
                  padding: "0.4rem 0.8rem",
                  borderRadius: "0.4rem",
                  border: "1px solid #444",
                  background: deployBusy ? "#eee" : "#fff",
                  cursor: deployBusy ? "default" : "pointer",
                  fontSize: "0.9rem",
                }}
              >
                {deployBusy ? "Deploying…" : "Deploy"}
              </button>
              {deploymentsError && (
                <div style={{ color: "red", marginTop: "0.5rem" }}>
                  {deploymentsError}
                </div>
              )}
            </form>
          </section>

          {/* Deployments list */}
          <section
            style={{
              padding: "0.75rem",
              borderRadius: "0.5rem",
              border: "1px solid #ddd",
            }}
          >
            <h2 style={{ marginTop: 0 }}>
              Deployments{selectedDeployAgent ? ` for ${selectedDeployAgent.name}` : ""}
            </h2>
            {deploymentsLoading ? (
              <p>Loading deployments…</p>
            ) : !deployAgentId ? (
              <p>Select an agent above to view its deployments.</p>
            ) : deployments.length === 0 ? (
              <p>No deployments for this agent yet.</p>
            ) : (
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.9rem",
                }}
              >
                <thead>
                  <tr>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                      Location
                    </th>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                      Status
                    </th>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                      Created
                    </th>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {deployments.map((d) => {
                    const loc = locations.find((l) => l.id === d.location_id);
                    return (
                      <tr key={d.id}>
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {loc ? `${loc.name} (${loc.location_type})` : d.location_id}
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {d.status}
                          {d.last_error && (
                            <span style={{ color: "#a00", marginLeft: "0.5rem" }}>
                              (error)
                            </span>
                          )}
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {d.created_at
                            ? new Date(d.created_at).toLocaleString()
                            : "—"}
                        </td>
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          <button
                            type="button"
                            onClick={() => handleDeleteDeployment(d)}
                            style={{
                              padding: "0.2rem 0.5rem",
                              borderRadius: "0.4rem",
                              border: "1px solid #a00",
                              background: "#fff",
                              cursor: "pointer",
                              fontSize: "0.8rem",
                              color: "#a00",
                            }}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </section>
        </div>

        {/* Right: summary/info */}
        <div>
          <section
            style={{
              padding: "0.75rem",
              borderRadius: "0.5rem",
              border: "1px solid #ddd",
            }}
          >
            <h2 style={{ marginTop: 0 }}>About deployments</h2>
            <p style={{ fontSize: "0.9rem", color: "#444" }}>
              Use this tab to deploy registered agents to registered locations.
              Deployments represent staged code and environment for a given
              agent / location pair.
            </p>
            <ul style={{ fontSize: "0.9rem", color: "#444" }}>
              <li>
                <strong>Deploy</strong> creates a new deployment record and, in the
                backend, stages code (e.g., clones from GitHub).
              </li>
              <li>
                <strong>Status</strong> indicates whether staging succeeded (e.g.,
                <code>ready</code>, <code>failed</code>).
              </li>
              <li>
                <strong>Delete</strong> removes a deployment record (and, later,
                can trigger cleanup on the location).
              </li>
            </ul>
          </section>
        </div>
      </div>
    );
  };

  // ---------------------------------------------------------------------------
  // Main render
  // ---------------------------------------------------------------------------

  return (
    <div
      style={{
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        padding: "1.5rem",
        maxWidth: "1200px",
        margin: "0 auto",
      }}
    >
      <h1>Academy Agent Repository</h1>
      <p style={{ color: "#555", marginBottom: "1rem" }}>
        Phases 1–2: Manage agent implementations, locations, and deployments.
      </p>

      {renderHealth()}

      {/* Tabs */}
      <div style={{ marginBottom: "1rem" }}>
        {(["agents", "locations", "deployments", "instances"] as Tab[]).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "0.5rem 0.5rem 0 0",
              borderBottom:
                activeTab === tab ? "2px solid #444" : "1px solid #ddd",
              borderLeft: "1px solid #ddd",
              borderRight: "1px solid #ddd",
              borderTop: "1px solid #ddd",
              background: activeTab === tab ? "#fff" : "#f5f5f5",
              cursor: "pointer",
              marginRight: "0.5rem",
            }}
          >
            {tab === "agents"
              ? "Agents"
              : tab === "locations"
              ? "Locations"
              : "Deployments"}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "agents"
        ? renderAgentsTab()
        : activeTab === "locations"
        ? renderLocationsTab()
        : activeTab === "deployments"
        ? renderDeploymentsTab()
        : renderInstancesTab()}
    </div>
  );
};

export default App;
