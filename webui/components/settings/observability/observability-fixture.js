export function readObservabilityFixture(globalObj = globalThis) {
  const fixture = globalObj?.__OBSERVABILITY_TEST_DATA__;
  if (!fixture || typeof fixture !== "object") {
    return null;
  }

  const runs = Array.isArray(fixture.runs)
    ? fixture.runs
    : Array.isArray(fixture.workflowRuns)
      ? fixture.workflowRuns
      : [];
  const savedRuns = Array.isArray(fixture.saved_runs)
    ? fixture.saved_runs
    : Array.isArray(fixture.savedRuns)
      ? fixture.savedRuns
      : [];

  return {
    events: Array.isArray(fixture.events) ? fixture.events : [],
    stats: fixture.stats && typeof fixture.stats === "object" ? fixture.stats : {},
    runs,
    saved_runs: savedRuns,
    active_run_id: String(fixture.active_run_id || fixture.activeRunId || ""),
  };
}
