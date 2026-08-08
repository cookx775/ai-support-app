# Weather Prediction MCP + Agent

A FastMCP server that gives a Databricks Agent Bricks agent current weather, multi-day
forecasts, deterministic planning recommendations, and same-day city comparisons. Open-Meteo
provides both global geocoding and forecast data without an API key.

## Architecture

```text
Agent Bricks
    -> registered external MCP (`<ai-support-app URL>/mcp`)
    -> FastMCP tools in weather_mcp_server.py
    -> OpenMeteoClient in open_meteo.py
    -> Open-Meteo Geocoding API + Forecast API
```

The MCP functions contain tool descriptions and error-envelope handling only. Location
resolution, HTTP retries, parsing, units, WMO weather-code translation, and derived rules live
in the adapter. Resolved locations are cached for the app process.

## Tools

| Tool | Inputs | Result |
|---|---|---|
| `get_current_weather` | `location` | Current temperature, apparent temperature, humidity, precipitation, conditions, and wind |
| `get_forecast` | `location`, `days=7` | 1–16 daily forecasts with highs/lows, precipitation, conditions, and wind |
| `get_weather_recommendation` | `location`, `date` | Explainable umbrella, jacket, heat, and wind guidance |
| `compare_weather` | `locations`, `date` | Forecasts and rankings for 2–5 places, retaining clean per-place failures |

All values use labeled US customary units: °F, mph, percent, and inches. Every success includes
the selected canonical location and local timezone so an agent can expose ambiguous geocoding.

## Recommendation rules

The recommendation tool is deterministic, not an ML model:

- umbrella when precipitation probability is at least 40% or precipitation is at least 0.05 inch;
- jacket when the low is below 55°F or the high is below 65°F;
- heat caution when the high is at least 90°F;
- wind caution when maximum wind is at least 25 mph.

The response includes the Boolean decisions, underlying forecast, and measurements that
triggered each rule. It is general planning guidance, not an alert or emergency service.

## Run and test locally

Python 3.10 or newer is required by FastMCP 3.

```bash
cd homework-3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=mcp_server pytest -q
ruff check .
python mcp_server/weather_mcp_server.py
```

The streamable-HTTP endpoint is `http://localhost:8000/mcp`. No environment secret is needed.
The tests stub only the Open-Meteo HTTP boundary and exercise normalization, retry/error paths,
all recommendation boundaries, partial comparisons, and all four tools through a FastMCP
client.

## Deploy in the existing App slot

All three Free Edition App slots are occupied, so this assignment intentionally redeploys the
existing `ai-support-app` rather than creating a fourth app.

1. Record the app's current source path and deployment details. The rollback source is
   `homework-2` (or repository root for the original Day 1 app).
2. Push this repository and sync the Git folder in Databricks.
3. Open `ai-support-app`, choose **Deploy**, and set **Source code path** to
   `homework-3/mcp_server` in the synced repository.
4. Deploy and verify startup logs. The command in `app.yaml` binds FastMCP to the
   Databricks-provided port.
5. Verify the MCP endpoint at `<APP_URL>/mcp` with MCP Inspector or Databricks tool discovery.

Repointing the live App does not delete HW1/HW2 code, data, or submission evidence. To roll
back, deploy the prior recorded source path again.

## Register and configure Agent Bricks

1. Register `<APP_URL>/mcp` as an external MCP in the Databricks workspace and grant the
   required access when prompted.
2. Confirm discovery lists exactly the four tools above.
3. Create a Custom LLM Agent Bricks agent, enable all four MCP tools, and paste
   [`agent/system-prompt.md`](agent/system-prompt.md) as its system prompt.
4. Run the three prompts in [`agent/agent-config.md`](agent/agent-config.md), preserving each
   tool trace and final response as submission evidence.

## Error behavior and limitations

- Invalid inputs and anticipated upstream failures return `{status: "error", error: ...}`;
  internal details and stack traces are never returned to the agent.
- A comparison returns `partial` if at least one location succeeds and another fails.
- Geocoding selects Open-Meteo's first match. The agent is instructed to repeat the canonical
  result and ask for clarification when it looks wrong.
- Forecasts are limited to Open-Meteo's next 16 days and can change between calls.
- This service does not provide severe-weather alerts or emergency guidance.
- In-memory location caching resets whenever the Databricks App process restarts.

## Data sources and attribution

Forecast data is provided by [Open-Meteo](https://open-meteo.com/en/docs). Location search uses
the [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api), whose location
data is based on GeoNames. No API key or paid account is used.
