import React, { useEffect, useState, FormEvent } from "react";
import type { Agent, AgentFilters, HealthResponse, Deployment, RunResult } from "./api";
import {
  fetchHealth,
  fetchAgents,
  fetchAgent,
  createSampleAgent,
  validateAgent,
  deployAgent,
  fetchDeployments,
} from "./api";

const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [lastRunOutputs, setLastRunOutputs] = useState<any | null>(null);

  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentsError, setAgentsError] = useState<string | null>(null);
  const [agentsLoading, setAgentsLoading] = useState(false);

  const [creating, setCreating] = useState(false);
  const [validating, setValidating] = useState(false);

  const [filters, setFilters] = useState<AgentFilters>({
    name: "",
    agent_type: "",
    tag: "",
    owner: "",
  });

  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedAgentError, setSelectedAgentError] = useState<string | null>(
    null
  );
  const [selectedLoading, setSelectedLoading] = useState(false);

  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [deploymentsError, setDeploymentsError] = useState<string | null>(null);
  const [deploymentsLoading, setDeploymentsLoading] = useState(false);
  const [deployTarget, setDeployTarget] = useState<string>("dev");
  const [deploying, setDeploying] = useState(false);


  const [copyIdStatus, setCopyIdStatus] = useState<
    "idle" | "copied" | "error"
  >("idle");

  // Initial load
  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => setHealthError(err.message));

    loadAgents(); // no filters initially
  }, []);

  const loadAgents = async (opts?: AgentFilters) => {
    try {
      setAgentsLoading(true);
      const data = await fetchAgents(opts);
      setAgents(data);
      setAgentsError(null);
    } catch (err: any) {
      setAgentsError(err.message ?? String(err));
    } finally {
      setAgentsLoading(false);
    }
  };

  const handleFilterChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ): void => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFilterSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const nonEmpty: AgentFilters = {};
    if (filters.name) nonEmpty.name = filters.name;
    if (filters.agent_type) nonEmpty.agent_type = filters.agent_type;
    if (filters.tag) nonEmpty.tag = filters.tag;
    if (filters.owner) nonEmpty.owner = filters.owner;
    await loadAgents(nonEmpty);
    setSelectedAgentId(null);
    setDeployments([]);
    setDeploymentsError(null);
    setSelectedAgent(null);
    setSelectedAgentError(null);
  };

  const handleClearFilters = async () => {
    setFilters({
      name: "",
      agent_type: "",
      tag: "",
      owner: "",
    });
    await loadAgents();
    setSelectedAgentId(null);
    setSelectedAgent(null);
    setSelectedAgentError(null);
  };

  const handleCreateSample = async () => {
    try {
      setCreating(true);
      const created = await createSampleAgent();
      setAgents((prev) => [created, ...prev]);
      setAgentsError(null);
    } catch (err: any) {
      setAgentsError(err.message ?? String(err));
    } finally {
      setCreating(false);
    }
  };

  const handleSelectAgent = async (agent: Agent) => {
    setSelectedAgentId(agent.id);
    setSelectedAgent(null);
    setSelectedAgentError(null);

    try {
      setSelectedLoading(true);
      const detail = await fetchAgent(agent.id);
      setSelectedAgent(detail);
      // Load deployments for this agent
      try {
        setDeploymentsLoading(true);
        const deps = await fetchDeployments(agent.id);
        setDeployments(deps);
        setDeploymentsError(null);
      } catch (err: any) {
        setDeploymentsError(err.message ?? String(err));
      } finally {
        setDeploymentsLoading(false);
      }

    } catch (err: any) {
      setSelectedAgentError(err.message ?? String(err));
    } finally {
      setSelectedLoading(false);
    }
  };

  const handleDeploySelected = async () => {
    if (!selectedAgentId) return;
    try {
      setDeploying(true);
      // For now, we don't have a UI for inputs, so send an empty object.
      const result = await runAgent(selectedAgentId, deployTarget || "local-ui", {});
      // Save outputs from the agent run
      setLastRunOutputs(result.outputs);

      // If a deployment was recorded, update the deployments list
      if (result.deployment) {
        setDeployments((prev) => [result.deployment!, ...prev]);
      }

      setDeploymentsError(null);
    } catch (err: any) {
      setDeploymentsError(err.message ?? String(err));
    } finally {
      setDeploying(false);
    }
  };

  const handleValidateSelected = async () => {
    if (!selectedAgentId) return;
    try {
      setValidating(true);
      const updated = await validateAgent(selectedAgentId);
      setSelectedAgent(updated);
      setAgents((prev) =>
        prev.map((a) => (a.id === updated.id ? { ...a, ...updated } : a))
      );
      setSelectedAgentError(null);
    } catch (err: any) {
      setSelectedAgentError(err.message ?? String(err));
    } finally {
      setValidating(false);
    }
  };

  const handleCopyId = async () => {
    if (!selectedAgent) return;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(selectedAgent.id);
        setCopyIdStatus("copied");
        setTimeout(() => setCopyIdStatus("idle"), 1500);
      } else {
        setCopyIdStatus("error");
        setTimeout(() => setCopyIdStatus("idle"), 1500);
      }
    } catch {
      setCopyIdStatus("error");
      setTimeout(() => setCopyIdStatus("idle"), 1500);
    }
  };

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
        Browse, search, and inspect agents (including A2A Agent Card and
        GitHub/container metadata).
      </p>

      {/* Health section */}
      <section
        style={{
          marginTop: "0.5rem",
          padding: "1rem",
          borderRadius: "0.5rem",
          border: "1px solid #ddd",
        }}
      >
        <h2>Backend health</h2>
        {healthError && (
          <p style={{ color: "red" }}>Error: {healthError}</p>
        )}

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

      {/* Agents list + filters + detail */}
      <section
        style={{
          marginTop: "1.5rem",
          padding: "1rem",
          borderRadius: "0.5rem",
          border: "1px solid #ddd",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: "1rem",
            alignItems: "center",
            marginBottom: "0.75rem",
          }}
        >
          <h2 style={{ margin: 0 }}>Agents</h2>
          <button
            onClick={handleCreateSample}
            disabled={creating}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "0.4rem",
              border: "1px solid #444",
              background: creating ? "#eee" : "#fff",
              cursor: creating ? "default" : "pointer",
            }}
          >
            {creating ? "Creating…" : "Create sample agent"}
          </button>
        </div>

        {/* Filters */}
        <form
          onSubmit={handleFilterSubmit}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr)) auto",
            gap: "0.5rem",
            alignItems: "end",
            marginBottom: "0.75rem",
          }}
        >
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.8rem",
                color: "#555",
              }}
            >
              Name
            </label>
            <input
              type="text"
              name="name"
              value={filters.name ?? ""}
              onChange={handleFilterChange}
              placeholder="exact name"
              style={{ width: "100%", padding: "0.25rem" }}
            />
          </div>
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.8rem",
                color: "#555",
              }}
            >
              Type
            </label>
            <input
              type="text"
              name="agent_type"
              value={filters.agent_type ?? ""}
              onChange={handleFilterChange}
              placeholder="task, domain, planner…"
              style={{ width: "100%", padding: "0.25rem" }}
            />
          </div>
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.8rem",
                color: "#555",
              }}
            >
              Tag
            </label>
            <input
              type="text"
              name="tag"
              value={filters.tag ?? ""}
              onChange={handleFilterChange}
              placeholder="materials, sim, sample…"
              style={{ width: "100%", padding: "0.25rem" }}
            />
          </div>
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.8rem",
                color: "#555",
              }}
            >
              Owner
            </label>
            <input
              type="text"
              name="owner"
              value={filters.owner ?? ""}
              onChange={handleFilterChange}
              placeholder="team name or user"
              style={{ width: "100%", padding: "0.25rem" }}
            />
          </div>
          <div style={{ display: "flex", gap: "0.4rem" }}>
            <button
              type="submit"
              style={{
                padding: "0.35rem 0.7rem",
                borderRadius: "0.4rem",
                border: "1px solid #444",
                background: "#f5f5f5",
                cursor: "pointer",
                fontSize: "0.85rem",
              }}
            >
              Apply
            </button>
            <button
              type="button"
              onClick={handleClearFilters}
              style={{
                padding: "0.35rem 0.7rem",
                borderRadius: "0.4rem",
                border: "1px solid #ccc",
                background: "#fff",
                cursor: "pointer",
                fontSize: "0.85rem",
              }}
            >
              Clear
            </button>
          </div>
        </form>

        {agentsError && (
          <p style={{ color: "red", marginBottom: "0.5rem" }}>
            Error: {agentsError}
          </p>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 2fr) minmax(0, 3fr)",
            gap: "1rem",
          }}
        >
          {/* Agents list */}
          <div>
            {agentsLoading ? (
              <p>Loading agents…</p>
            ) : agents.length === 0 && !agentsError ? (
              <p>No agents found.</p>
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
                    <th
                      style={{
                        borderBottom: "1px solid #ccc",
                        textAlign: "left",
                      }}
                    >
                      Name
                    </th>
                    <th
                      style={{
                        borderBottom: "1px solid #ccc",
                        textAlign: "left",
                      }}
                    >
                      Version
                    </th>
                    <th
                      style={{
                        borderBottom: "1px solid #ccc",
                        textAlign: "left",
                      }}
                    >
                      Type
                    </th>
                    <th
                      style={{
                        borderBottom: "1px solid #ccc",
                        textAlign: "left",
                      }}
                    >
                      Owner
                    </th>
                    <th
                      style={{
                        borderBottom: "1px solid #ccc",
                        textAlign: "left",
                      }}
                    >
                      Status
                    </th>
                    <th
                      style={{
                        borderBottom: "1px solid #ccc",
                        textAlign: "left",
                      }}
                    >
                      Links
                    </th>
                    <th
                      style={{
                        borderBottom: "1px solid #ccc",
                        textAlign: "left",
                      }}
                    >
                      Tags
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {agents.map((agent) => {
                    const isSelected = agent.id === selectedAgentId;
                    return (
                      <tr
                        key={agent.id}
                        onClick={() => handleSelectAgent(agent)}
                        style={{
                          cursor: "pointer",
                          background: isSelected ? "#eef5ff" : "transparent",
                        }}
                      >
                        {/* Name */}
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {agent.name}
                        </td>

                        {/* Version */}
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {agent.version}
                        </td>

                        {/* Type */}
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {agent.agent_type}
                        </td>

                        {/* Owner */}
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {agent.owner ?? "—"}
                        </td>

                        {/* Validation status */}
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          <span
                            style={{
                              padding: "0.1rem 0.4rem",
                              borderRadius: "0.75rem",
                              border: "1px solid #ccc",
                              fontSize: "0.75rem",
                              background:
                                agent.validation_status === "validated"
                                  ? "#e6ffed"
                                  : agent.validation_status === "failed"
                                  ? "#ffe5e5"
                                  : "#fff4e5",
                            }}
                          >
                            {agent.validation_status}
                          </span>
                        </td>

                        {/* Links */}
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {agent.git_repo && (
                            <a
                              href={agent.git_repo}
                              title="GitHub repo"
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              style={{
                                marginRight: "0.4rem",
                                fontSize: "0.8rem",
                              }}
                            >
                              GH
                            </a>
                          )}
                          {agent.container_image && (
                            <span
                              title={agent.container_image}
                              style={{ fontSize: "0.8rem", color: "#555" }}
                              onClick={(e) => e.stopPropagation()}
                            >
                              🐳
                            </span>
                          )}
                          {!agent.git_repo && !agent.container_image && "—"}
                        </td>

                        {/* Tags */}
                        <td
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "0.25rem 0.2rem",
                          }}
                        >
                          {agent.tags?.join(", ") || "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Agent detail */}
          <div
            style={{
              borderLeft: "1px solid #eee",
              paddingLeft: "1rem",
              minHeight: "6rem",
            }}
          >
            <h3 style={{ marginTop: 0 }}>Agent detail</h3>
            {selectedAgentError && (
              <p style={{ color: "red" }}>Error loading agent: {selectedAgentError}</p>
            )}
            {selectedLoading && <p>Loading agent…</p>}
            {!selectedLoading && !selectedAgent && !selectedAgentError && (
              <p>Select an agent from the table to see details.</p>
            )}
            {selectedAgent && !selectedLoading && (
              <div
                style={{
                  fontSize: "0.9rem",
                  lineHeight: 1.4,
                  maxHeight: "28rem",
                  overflow: "auto",
                }}
              >
                <h4 style={{ margin: "0 0 0.25rem 0" }}>
                  {selectedAgent.name}{" "}
                  <span style={{ color: "#666" }}>v{selectedAgent.version}</span>
                </h4>

                {/* ID + copy button */}
                <div
                  style={{
                    fontSize: "0.8rem",
                    color: "#666",
                    marginBottom: "0.35rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  <span>
                    <strong>ID:</strong> {selectedAgent.id}
                  </span>
                  <button
                    type="button"
                    onClick={handleCopyId}
                    style={{
                      padding: "0.15rem 0.5rem",
                      borderRadius: "0.4rem",
                      border: "1px solid #ccc",
                      background: "#f8f8f8",
                      fontSize: "0.75rem",
                      cursor: "pointer",
                    }}
                  >
                    {copyIdStatus === "copied"
                      ? "Copied!"
                      : copyIdStatus === "error"
                      ? "Copy failed"
                      : "Copy ID"}
                  </button>
                </div>

                <p style={{ margin: "0 0 0.5rem 0", color: "#444" }}>
                  {selectedAgent.description}
                </p>

                {/* Basic info + validation badge */}
                <div style={{ marginBottom: "0.5rem" }}>
                  <strong>Type:</strong> {selectedAgent.agent_type}{" "}
                  <strong style={{ marginLeft: "0.75rem" }}>Owner:</strong>{" "}
                  {selectedAgent.owner ?? "—"}{" "}
                  <strong style={{ marginLeft: "0.75rem" }}>Created:</strong>{" "}
                  {new Date(selectedAgent.created_at).toLocaleString()}
                  <br />
                  <strong>Validation:</strong>{" "}
                  <span
                    style={{
                      padding: "0.1rem 0.4rem",
                      borderRadius: "0.75rem",
                      border: "1px solid #ccc",
                      fontSize: "0.8rem",
                      background:
                        selectedAgent.validation_status === "validated"
                          ? "#e6ffed"
                          : "#fff4e5",
                    }}
                  >
                    {selectedAgent.validation_status}
                  </span>
                  {selectedAgent.last_validated_at && (
                    <>
                      {" "}
                      <span style={{ color: "#666", marginLeft: "0.5rem" }}>
                        (last:{" "}
                        {new Date(
                          selectedAgent.last_validated_at
                        ).toLocaleString()}
                        )
                      </span>
                    </>
                  )}
                </div>

                {/* Validation score + button */}
                <div style={{ marginBottom: "0.5rem" }}>
                  <strong>Validation score:</strong>{" "}
                  {typeof selectedAgent.validation_score === "number"
                    ? selectedAgent.validation_score.toFixed(3)
                    : "—"}
                  {"  "}
                  <button
                    type="button"
                    onClick={handleValidateSelected}
                    disabled={validating}
                    style={{
                      marginLeft: "0.75rem",
                      padding: "0.2rem 0.6rem",
                      borderRadius: "0.4rem",
                      border: "1px solid #444",
                      background: validating ? "#eee" : "#fff",
                      cursor: validating ? "default" : "pointer",
                      fontSize: "0.8rem",
                    }}
                  >
                    {validating ? "Validating…" : "Mark as validated"}
                  </button>
                </div>

                {/* Deploy section */}
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>Deploy:</strong>{" "}
                  <input
                    type="text"
                    value={deployTarget}
                    onChange={(e) => setDeployTarget(e.target.value)}
                    placeholder="target (e.g. dev, hpc, lab-node-1)"
                    style={{
                      marginLeft: "0.5rem",
                      padding: "0.15rem 0.4rem",
                      fontSize: "0.8rem",
                    }}
                  />
                  <button
                    type="button"
                    onClick={handleDeploySelected}
                    disabled={deploying}
                    style={{
                      marginLeft: "0.5rem",
                      padding: "0.2rem 0.6rem",
                      borderRadius: "0.4rem",
                      border: "1px solid #444",
                      background: deploying ? "#eee" : "#fff",
                      cursor: deploying ? "default" : "pointer",
                      fontSize: "0.8rem",
                    }}
                  >
                    {deploying ? "Deploying…" : "Create deployment"}
                  </button>
                  {deploymentsError && (
                    <div style={{ color: "red", marginTop: "0.25rem" }}>
                      {deploymentsError}
                    </div>
                  )}
                </div>

                {/* Deployment history */}
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>Deployments:</strong>
                  {deploymentsLoading ? (
                    <p>Loading deployments…</p>
                  ) : deployments.length === 0 ? (
                    <p style={{ margin: "0.25rem 0" }}>No deployments recorded.</p>
                  ) : (
                    <table
                      style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        fontSize: "0.8rem",
                        marginTop: "0.25rem",
                      }}
                    >
                      <thead>
                        <tr>
                          <th
                            style={{
                              borderBottom: "1px solid #ccc",
                              textAlign: "left",
                            }}
                          >
                            Target
                          </th>
                          <th
                            style={{
                              borderBottom: "1px solid #ccc",
                              textAlign: "left",
                            }}
                          >
                            Status
                          </th>
                          <th
                            style={{
                              borderBottom: "1px solid #ccc",
                              textAlign: "left",
                            }}
                          >
                            Time
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {deployments.map((d) => (
                          <tr key={d.id}>
                            <td
                              style={{
                                borderBottom: "1px solid #eee",
                                padding: "0.2rem 0.2rem",
                              }}
                            >
                              {d.target}
                            </td>
                            <td
                              style={{
                                borderBottom: "1px solid #eee",
                                padding: "0.2rem 0.2rem",
                              }}
                            >
                              {d.status}
                            </td>
                            <td
                              style={{
                                borderBottom: "1px solid #eee",
                                padding: "0.2rem 0.2rem",
                              }}
                            >
                              {new Date(d.created_at).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                {/* Last run outputs */}
                <div style={{ marginBottom: "0.75rem" }}>
                  <strong>Last run outputs:</strong>
                  {lastRunOutputs ? (
                    <pre
                      style={{
                        background: "#f7f7f7",
                        padding: "0.5rem",
                        borderRadius: "0.25rem",
                        fontSize: "0.8rem",
                        marginTop: "0.25rem",
                        maxHeight: "12rem",
                        overflow: "auto"
                      }}
                    >
                      {JSON.stringify(lastRunOutputs, null, 2)}
                    </pre>
                  ) : (
                    <p style={{ margin: "0.25rem 0" }}>No runs recorded in this session.</p>
                  )}
                </div>

                {/* Tags */}
                <div style={{ marginBottom: "0.5rem" }}>
                  <strong>Tags:</strong>{" "}
                  {selectedAgent.tags && selectedAgent.tags.length > 0
                    ? selectedAgent.tags.join(", ")
                    : "—"}
                </div>

                {/* GitHub / container metadata */}
                <div style={{ marginBottom: "0.5rem" }}>
                  <strong>Git repo:</strong>{" "}
                  {selectedAgent.git_repo ? (
                    <a
                      href={selectedAgent.git_repo}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {selectedAgent.git_repo}
                    </a>
                  ) : (
                    "—"
                  )}
                  <br />
                  <strong>Commit:</strong> {selectedAgent.git_commit ?? "—"}
                  <br />
                  <strong>Container image:</strong>{" "}
                  {selectedAgent.container_image ?? "—"}
                  <br />
                  <strong>Entrypoint:</strong>{" "}
                  {selectedAgent.entrypoint ?? "—"}
                </div>

                {/* A2A Agent Card summary */}
                <div style={{ marginBottom: "0.5rem" }}>
                  <strong>A2A Agent Card:</strong>{" "}
                  {selectedAgent.a2a_card ? (
                    <>
                      <div>
                        <strong>Name:</strong>{" "}
                        {selectedAgent.a2a_card.name}
                      </div>
                      <div>
                        <strong>URL:</strong>{" "}
                        <a
                          href={selectedAgent.a2a_card.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {selectedAgent.a2a_card.url}
                        </a>
                      </div>
                      <div>
                        <strong>Version:</strong>{" "}
                        {selectedAgent.a2a_card.version}
                      </div>
                      <div>
                        <strong>Default I/O:</strong>{" "}
                        {selectedAgent.a2a_card.defaultInputModes.join(", ") ||
                          "—"}{" "}
                        →{" "}
                        {selectedAgent.a2a_card.defaultOutputModes.join(", ") ||
                          "—"}
                      </div>
                      {selectedAgent.a2a_card.description && (
                        <div style={{ marginTop: "0.25rem" }}>
                          <em>{selectedAgent.a2a_card.description}</em>
                        </div>
                      )}
                    </>
                  ) : (
                    "—"
                  )}
                </div>

                {/* Raw JSON */}
                <details>
                  <summary style={{ cursor: "pointer" }}>Raw JSON</summary>
                  <pre
                    style={{
                      background: "#f7f7f7",
                      padding: "0.5rem",
                      borderRadius: "0.25rem",
                      fontSize: "0.8rem",
                      marginTop: "0.25rem",
                    }}
                  >
                    {JSON.stringify(selectedAgent, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default App;

