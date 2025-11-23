export async function fetchHealth() {
  const r = await fetch("/api/health");
  if (!r.ok) throw new Error("Failed");
  return r.json();
}
