import React, { useEffect, useState, FormEvent } from "react";
import type { Agent, AgentFilters, HealthResponse } from "./api";
import { fetchHealth, fetchAgents, fetchAgent, createSampleAgent } from "./api";

const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentsError, setAgentsError] = useState<string | null>(null);
  const [agentsLoading, setAgentsLoading] = useState(false);

  const [creating, setCreating] = useState(false);

  const [filters, setFilters] = useState<AgentFilters>({
    name: "",
    agent_type: "",
    tag: "",
    owner: ""
  });

  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedAgentError, setSelectedAgentError] = useState<string | null>(null);
  const [selectedLoading, setSelectedLoading] = useState(false);

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
  ) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFilterSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const nonEmptyFilters: AgentFilters = {};
    if (filters.name) nonEmptyFilters.name = filters.name;
    if (filters.agent_type) nonEmptyFilters.agent_type = filters.agent_type;
    if (filters.tag) nonEmptyFilters.tag = filters.tag;
    if (filters.owner) nonEmptyFilters.owner = filters.owner;
    await loadAgents(nonEmptyFilters);
    // Clear selection when filters change
    setSelectedAgentId(null);
    setSelectedAgent(null);
    setSelectedAgentError(null);
  };

  const handleClearFilters = async () => {
    setFilters({
      name: "",
      agent_type: "",
      tag: "",
      owner: ""
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
    } catch (err: any) {
      setSelectedAgentError(err.message ?? String(err));
    } finally {
      setSelectedLoading(false);
    }
  };

  return (
    <div
      style={{
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        padding: "1.5rem",
        maxWidth: "1200px",
        margin: "0 auto"
      }}
    >
      <h1>Academy Agent Repository</h1>
      <p style={{ color: "#555", marginBottom: "1rem" }}>
        Browse, search, and inspect agents (including A2A Agent Card and GitHub/container metadata).
      </p>

      {/* Health section */}
      <section
        style={{
          marginTop: "0.5rem",
          padding: "1rem",
          borderRadius: "0.5rem",
          border: "1px solid #ddd"
        }}
      >
        <h2>Backend health</h2>
        {healthError && <p style={{ color: "red" }}>Error: {healthError}</p>}
        {health ? (
          <pre
            style={{
              background: "#f7f7f7",
              padding: "0.5rem",
              borderRadius: "0.25rem",
              fontSize: "0.85rem"
            }}
          >
            {JSON.stringify(health, null, 2)}
          </pre>
        ) : !healthError ? (
          <p>Checking health…</p>
        ) : null}
      </section>

      {/* Agents list + filters + detail */}
      <section
        style={{
          marginTop: "1.5rem",
          padding: "1rem",
          borderRadius: "0.5rem",
          border: "1px solid #ddd"
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: "1rem",
            alignItems: "center",
            marginBottom: "0.75rem"
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
              cursor: creating ? "default" : "pointer"
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
            marginBottom: "0.75rem"
          }}
        >
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "#555" }}>
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
            <label style={{ display: "block", fontSize: "0.8rem", color: "#555" }}>
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
            <label style={{ display: "block", fontSize: "0.8rem", color: "#555" }}>
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
            <label style={{ display: "block", fontSize: "0.8rem", color: "#555" }}>
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
                fontSize: "0.85rem"
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
                fontSize: "0.85rem"
              }}
            >
              Clear
            </button>
          </div>
        </form>

        {agentsError && (
          <p style={{ color: "red", marginBottom: "0.5rem" }}>Error: {agentsError}</p>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 2fr) minmax(0, 3fr)",
            gap: "1rem"
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
                  fontSize: "0.9rem"
                }}
              >
                <thead>
                  <tr>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Name</th>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Version</th>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Type</th>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Owner</th>
                    <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Tags</th>
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
                          background: isSelected ? "#eef5ff" : "transparent"
                        }}
                      >
                        <td style={{ borderBottom: "1px solid #eee", padding: "0.25rem 0.2rem" }}>
                          {agent.name}
                        </td>
                        <td style={{ borderBottom: "1px solid #eee", padding: "0.25rem 0.2rem" }}>
                          {agent.version}
                        </td>
                        <td style={{ borderBottom: "1px solid #eee", padding: "0.25rem 0.2rem" }}>
                          {agent.agent_type}
                        </td>
                        <td style={{ borderBottom: "1px solid #eee", padding: "0.25rem 0.2rem" }}>
                          {agent.owner ?? "—"}
                        </td>
                        <td style={{ borderBottom: "1px solid #eee", padding: "0.25rem 0.2rem" }}>
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
              minHeight: "6rem"
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
                  overflow: "auto"
                }}
              >
                <h4 style={{ margin: "0 0 0.25rem 0" }}>
                  {selectedAgent.name} <span style={{ color: "#666" }}>v{selectedAgent.version}</span>
                </h4>
                <p style={{ margin: "0 0 0.5rem 0", color: "#444" }}>
                  {selectedAgent.description}
                </p>

                <div style={{ marginBottom: "0.5rem" }}>
                  <strong>Type:</strong> {selectedAgent.agent_type}{" "}
                  <strong style={{ marginLeft: "0.75rem" }}>Owner:</strong>{" "}
                  {selectedAgent.owner ?? "—"}{" "}
                  <strong style={{ marginLeft: "0.75rem" }}>Created:</strong>{" "}
                  {new Date(selectedAgent.created_at).toLocaleString()}
                </div>

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
                    <a href={selectedAgent.git_repo} target="_blank" rel="noreferrer">
                      {selectedAgent.git_repo}
                    </a>
                  ) : (
                    "—"
                  )}
                  <br />
                  <strong>Commit:</strong>{" "}
                  {selectedAgent.git_commit ?? "—"}
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
                        <strong>Name:</strong> {selectedAgent.a2a_card.name}
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
                        <strong>Version:</strong> {selectedAgent.a2a_card.version}
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
                      marginTop: "0.25rem"
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

