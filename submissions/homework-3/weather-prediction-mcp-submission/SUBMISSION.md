# Homework 3 Submission — Weather Prediction MCP + Agent

## Delivered

- Source: `homework-3/` at Git commit `2b43a96`
- App: `ai-support-app`
- Endpoint: `https://ai-support-app-7474657586545240.aws.databricksapps.com/mcp`
- Deployment: `01f19359d3fd10439da49abc1590e4e8` (`SUCCEEDED`)
- Deployed source: `homework-3/mcp_server`
- Rollback source: `homework-2` at commit `4e5803cc7aae11f49a3343ddca26995914a8b8e7`

The FastMCP server exposes exactly four tools: `get_current_weather`, `get_forecast`,
`get_weather_recommendation`, and `compare_weather`. It uses Open-Meteo geocoding and forecast
APIs with retries, process-local resolution caching, normalized US customary units, WMO weather
descriptions, explainable rules, and consistent `success` / `partial` / `error` envelopes.

## Verification

- Full repository test suite: **58 passed**
- Ruff: **all checks passed**
- Local FastMCP HTTP smoke: handshake, four-tool discovery, and live call passed
- Deployed FastMCP HTTP smoke: authenticated handshake and four-tool discovery passed
- Deployed live calls passed:
  - Chicago two-day forecast: tomorrow had 43% precipitation probability
  - Austin recommendation for 2026-08-15: heat caution true
  - Chicago/Austin comparison for 2026-08-15: Austin ranked warmer and lower rain risk

The machine-readable deployed call evidence is in `evidence/deployed-protocol-smoke.json`.

## Agent Bricks limitation

The agent prompt and demonstration prompts are complete in `agent/`. Agent Bricks configuration
could not be persisted in this Free Edition workspace. Direct App selection only lists Apps whose
immutable names begin with `mcp-`, but the assignment requires reusing `ai-support-app`. The
external MCP registration screen requires a Unity Catalog location and durable authentication;
the default `main` catalog does not exist in this workspace. Deleting/recreating the App would
violate the approved in-place deployment plan.

A one-day token created during diagnosis was exposed by the UI accessibility snapshot, then
immediately revoked and its temporary file deleted. It is not usable and is not present here.
No persistent credential was created or retained.

## Evidence

- `screenshots/deployed-app.png` — running App, source commit, and successful startup
- `evidence/deployed-protocol-smoke.json` — sanitized discovery and live tool-call results
- `agent/system-prompt.md` — exact guardrails for the intended Agent Bricks agent
- `agent/agent-config.md` — the three required demonstration prompts

## Archive hygiene

The archive excludes `.git`, virtual environments, Python caches, pytest caches, macOS resource
forks, local configuration, tokens, and environment files. Open-Meteo requires no API key.
