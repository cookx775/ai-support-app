# Agent Bricks Configuration

- **Agent type:** Custom LLM agent
- **External MCP:** The deployed `ai-support-app` endpoint at `<APP_URL>/mcp`
- **Enabled tools:** `get_current_weather`, `get_forecast`,
  `get_weather_recommendation`, `compare_weather`
- **System prompt:** [`system-prompt.md`](system-prompt.md)

## Required demonstration prompts

1. `Will it rain in Chicago tomorrow?`
2. `Should I bring a jacket to Austin this weekend?`
3. `Compare the weather in Chicago and Austin this Saturday. Which is warmer and which has the lower rain risk?`

For each demonstration, capture both the tool call/arguments and the final answer. Replace
relative dates with the concrete dates shown in the trace when documenting evidence.
