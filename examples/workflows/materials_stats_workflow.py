from __future__ import annotations

from typing import Any, Dict, List

from academy_agents import AgentClient  # from your SDK


BACKEND_URL = "http://localhost:8000"
TARGET = "local-ui"  # match what you use in the UI


def ensure_deployed(client: AgentClient, agent_name: str, target: str) -> None:
    """Ensure an agent is deployed (staged) to the given target.

    NOTE: This just calls the /deploy endpoint unconditionally;
    your backend will handle "deploy again" gracefully.
    """
    agent = client.find_agent_by_name(agent_name)
    agent_id = agent["id"]
    print(f"[deploy] {agent_name} -> target={target}")
    client.deploy_agent(agent_id, target=target)


def run_materials_screening(
    client: AgentClient,
    materials: List[str],
) -> Dict[str, Any]:
    """Call materials-screening-agent and return its outputs."""
    print(f"[run] materials-screening-agent on {len(materials)} materials")
    agent = client.find_agent_by_name("materials-screening-agent")
    agent_id = agent["id"]
    result = client.run_agent(  # you may have a helper; otherwise use httpx like your frontend
        agent_id,
        target=TARGET,
        inputs={"materials": materials},
    )
    return result


def run_stats(
    client: AgentClient,
    values: List[float],
) -> Dict[str, Any]:
    """Call stats-demo-agent on a list of numerical values."""
    print(f"[run] stats-demo-agent on {len(values)} values")
    agent = client.find_agent_by_name("stats-demo-agent")
    agent_id = agent["id"]
    result = client.run_agent(
        agent_id,
        target=TARGET,
        inputs={"values": values},
    )
    return result


def main() -> None:
    client = AgentClient(base_url=BACKEND_URL)

    # 1. Ensure both agents are deployed to TARGET
    ensure_deployed(client, "materials-screening-agent", TARGET)
    ensure_deployed(client, "stats-demo-agent", TARGET)

    # 2. Define input materials
    materials = ["Fe2O3", "TiO2", "PbS", "Cu2O", "NiO", "Al2O3"]

    # 3. Run materials-screening-agent
    screening_out = run_materials_screening(client, materials)
    results = screening_out.get('outputs').get("results", [])

    # 4. Filter promising + borderline and collect scores
    filtered_scores: List[float] = []
    print("\n[results] Materials screening:")
    for entry in results:
        m = entry.get("material")
        score = float(entry.get("score", 0.0))
        label = entry.get("label", "unknown")
        print(f"  - {m}: score={score:.3f}, label={label}")
        if label in {"promising", "borderline"}:
            filtered_scores.append(score)

    if not filtered_scores:
        print("\n[workflow] No promising/borderline materials found → nothing to pass to stats agent.")
        return

    # 5. Run stats-demo-agent on filtered scores
    stats_out = run_stats(client, filtered_scores).get('outputs')

    print("\n[results] Stats on promising/borderline scores:")
    print(f"  count = {stats_out.get('count')}")
    print(f"  mean  = {stats_out.get('mean')}")
    print(f"  min   = {stats_out.get('min')}")
    print(f"  max   = {stats_out.get('max')}")


if __name__ == "__main__":
    main()
