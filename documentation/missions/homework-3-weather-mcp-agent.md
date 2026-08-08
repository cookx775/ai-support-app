# Mission: Build a Weather-Prediction MCP Server and Agent

## Why

Be able to expose dependable third-party data through a small MCP interface and constrain an AI
agent to use that interface instead of hallucinating current facts.

## Success looks like

- Deploy a FastMCP streamable-HTTP server as the existing `ai-support-app`.
- Resolve global locations and return normalized, labeled Open-Meteo conditions and forecasts.
- Make transparent rule-based planning recommendations from forecast measurements.
- Register the server as an external MCP and demonstrate Agent Bricks calling all relevant tools.
- Preserve local protocol tests, tool traces, deployment evidence, and a credential-free archive.

## Constraints

- All three Databricks App slots are occupied, so HW3 temporarily replaces the source deployed
  to `ai-support-app`; prior source remains versioned and restorable.
- Open-Meteo is the only backend and uses no secret or API key.
- MCP tools stay thin; HTTP and parsing behavior belongs to the adapter.
- Weather claims must come from tool results, and hazardous-weather decisions require official
  local guidance.

## Out of scope

- A separate dashboard App.
- NWS alert integration, historical weather, persistence, and scheduled collection.
- Treating deterministic clothing/umbrella thresholds as a trained prediction model.
