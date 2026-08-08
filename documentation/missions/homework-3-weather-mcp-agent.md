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

## Delivery record — 2026-08-08

- Deployed `homework-3/mcp_server` in place to `ai-support-app` from commit `2b43a96`.
- Deployment `01f19359d3fd10439da49abc1590e4e8` reached `SUCCEEDED`; the App is running.
- The deployed `/mcp` endpoint completed an authenticated MCP handshake, discovered all four
  tools, and returned live Open-Meteo results for forecast, recommendation, and comparison calls.
- Rollback remains `homework-2` at commit `4e5803cc7aae11f49a3343ddca26995914a8b8e7`.
- Agent Bricks attachment is blocked in this Free Edition workspace: direct App discovery only
  lists immutable App names beginning with `mcp-`, while external registration requires a Unity
  Catalog location and durable credential. The authorized plan forbids deleting/recreating
  `ai-support-app`; no persistent credential was left behind. Screenshots of both UI constraints
  are preserved in `submissions/homework-3/screenshots/`.
