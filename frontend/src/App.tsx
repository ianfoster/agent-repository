import React, { useEffect, useState } from "react";
import type { Agent, HealthResponse } from "./api";
import { fetchHealth, fetchAgents, createSampleAgent } from "./api";

const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentsError, setAgentsError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => setHealthError(err.message));

    fetchAgents()
      .then(setAgents)
      .catch((err) => setAgentsError(err.message));
  }, []);

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

  return (
    <div
      style={{
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        padding: "1.5rem",
        maxWidth: "960px",
        margin: "0 auto"
      }}
    >
      <h1>Academy Agent Repository</h1>
      <p style={{ color: "#555" }}>
        Minimal GUI for browsing and creating agents (with A2A Agent Card
        metadata).
      </p>

      <section
        style={{
          marginTop: "1.5rem",
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
              borderRadius: "0.25rem"
            }}
          >
            {JSON.stringify(health, null, 2)}
          </pre>
        ) : !healthError ? (
          <p>Checking health…</p>
        ) : null}
      </section>

      <section
        style={{
          marginTop: "1.5rem",
          padding: "1rem",
          borderRadius: "0.5rem",
          border: "1px solid #ddd"
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <h2>Agents</h2>
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

        {agentsError && <p style={{ color: "red" }}>Error: {agentsError}</p>}

        {agents.length === 0 && !agentsError ? (
          <p>No agents found yet.</p>
        ) : (
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              marginTop: "0.75rem",
              fontSize: "0.9rem"
            }}
          >
            <thead>
              <tr>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Name</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Version</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Type</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>Owner</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>A2A URL</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id}>
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
                    {agent.a2a_card?.url ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

export default App;

