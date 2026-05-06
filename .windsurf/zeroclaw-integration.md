# ZeroClaw Integration Guide

## Overview

This guide covers integrating the Garmin MCP Server with ZeroClaw, a self-hosted AI agent runtime that provides advanced agent controls, multiple channel support, and privacy-first execution.

## What is ZeroClaw?

ZeroClaw is a Rust-based AI agent runtime that:

- **Acts as an MCP Client**: Connects to external MCP servers via HTTP transport
- **Supports 30+ Channels**: Discord, Telegram, Matrix, email, CLI, webhooks, etc.
- **Provider-Agnostic**: Works with Anthropic, OpenAI, Ollama, and 20+ other LLM providers
- **Security-First**: Sandbox execution, approval gates, tool receipts
- **Privacy-First**: 100% local execution when using Ollama
- **Advanced Controls**: SOP engine, cron jobs, hardware support

## Prerequisites

- Garmin MCP Server running
- LLM provider account (Anthropic, OpenAI, or Ollama for local)

## Installation Options

### Option 1: Docker (Recommended)

The easiest way to run ZeroClaw is with Docker, which includes the Garmin MCP server in the same stack.

```bash
cd zeroclaw
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d --build
```

This will start both ZeroClaw and the Garmin MCP server together.

### Option 2: Native Installation

```bash
curl -fsSL https://raw.githubusercontent.com/zeroclaw-labs/zeroclaw/master/install.sh | bash
```

Or clone and install:

```bash
git clone https://github.com/zeroclaw-labs/zeroclaw.git
cd zeroclaw
./install.sh
```

### Initialize ZeroClaw (Native Only)

```bash
zeroclaw onboard
```

This wizard will guide you through:

- Selecting an LLM provider
- Configuring API keys
- Setting up initial channels

## Configuration

### Docker Configuration

With Docker, configuration is handled via `zeroclaw/config.toml` and environment variables:

**Edit `zeroclaw/config.toml`:**

```toml
[mcp_servers.garmin]
transport = "http"
url = "http://mcp-server:8000/mcp"
```

**Edit `zeroclaw/.env`:**

```bash
ANTHROPIC_API_KEY=your_key_here
# or OPENAI_API_KEY=your_key_here
```

### Native Configuration

Edit `~/.zeroclaw/config.toml` to add the Garmin MCP server:

```toml
[mcp_servers.garmin]
transport = "http"
url = "http://localhost:8000/mcp"
```

### LLM Provider Configuration

Choose your provider in the config file:

**Anthropic:**

```toml
[providers.models.anthropic]
provider = "anthropic"
model = "claude-sonnet-4-20250514"
api_key = "${ANTHROPIC_API_KEY}"
```

**OpenAI:**

```toml
[providers.models.openai]
provider = "openai"
model = "gpt-4-turbo"
api_key = "${OPENAI_API_KEY}"
```

**Ollama (Local):**

```toml
[providers.models.ollama]
provider = "ollama"
model = "llama3:70b"
base_url = "http://host.docker.internal:11434"
```

### Channel Configuration

Configure your preferred channels in the config file:

**CLI Channel:**

```toml
[channels.cli]
enabled = true
```

**Discord Channel:**

```toml
[channels.discord]
enabled = true
token = "${DISCORD_BOT_TOKEN}"
```

**Telegram Channel:**

```toml
[channels.telegram]
enabled = true
token = "${TELEGRAM_BOT_TOKEN}"
```

## Testing

### Docker Testing

```bash
# Start ZeroClaw and MCP server
cd zeroclaw
docker-compose up -d

# View logs
docker-compose logs -f zeroclaw

# Access ZeroClaw CLI
docker-compose exec zeroclaw zeroclaw agent
```

### Native Testing

```bash
# Start ZeroClaw
zeroclaw agent
```

This starts the interactive CLI channel.

### Test MCP Connection

In the ZeroClaw CLI, try:

```
List my recent activities
```

ZeroClaw should:

1. Recognize the intent
2. Call the `get_recent_activities` MCP tool
3. Display the results

### Test Other Tools

```
Show me details for activity 12345
What's my heart rate data for my last run?
Compare my last 5 runs
```

## Advanced Features

### SOP Engine

Create Standard Operating Procedures (SOPs) in `~/.zeroclaw/config.toml`:

```toml
[sops.daily_analysis]
trigger = "cron"
schedule = "0 8 * * *"  # 8 AM daily
steps = [
    {tool = "get_recent_activities", args = {limit = 10, activity_type = "running"}},
    {tool = "get_training_load", args = {days = 7}}
]
approval = "medium"
```

### Approval Gates

Configure approval levels in `~/.zeroclaw/config.toml`:

```toml
[security]
autonomy = "supervised"
approval_medium = true  # Require approval for medium-risk ops
approval_high = true   # Block high-risk ops
```

### Tool Receipts

Enable cryptographic receipts for audit trails:

```toml
[security]
tool_receipts = true
```

### YOLO Mode (Development Only)

Disable all safety checks for trusted environments:

```bash
zeroclaw agent --yolo
```

## Channel-Specific Setup

### Discord

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot user
3. Invite the bot to your server
4. Copy the bot token
5. Configure in `~/.zeroclaw/config.toml`

### Telegram

1. Create a bot via @BotFather on Telegram
2. Copy the API token
3. Configure in `~/.zeroclaw/config.toml`

### CLI

The CLI channel is enabled by default after installation.

## Privacy Considerations

**With Ollama (Local LLM):**

- 100% local execution
- No data leaves your machine
- Maximum privacy

**With Cloud LLMs (Anthropic/OpenAI):**

- Tool calls and responses sent to LLM provider
- Garmin data processed locally before sending summaries
- Check provider privacy policies

## Troubleshooting

### MCP Connection Fails

1. Verify MCP server is running: `curl http://localhost:8000/health`
2. Check ZeroClaw config: `~/.zeroclaw/config.toml`
3. Check ZeroClaw logs: `zeroclaw logs`

### Tools Not Discovered

1. Verify MCP endpoint: `curl http://localhost:8000/mcp`
2. Check MCP server logs: `docker-compose logs mcp-server`
3. Restart ZeroClaw: `zeroclaw service restart`

### LLM Provider Issues

1. Verify API key in config
2. Check provider status
3. Test with CLI: `zeroclaw agent --provider ollama`

## Next Steps

- Configure additional channels (Discord, Telegram)
- Set up SOPs for automated tasks
- Configure approval gates for safety
- Explore hardware integration (GPIO, I2C, SPI)
- Set up ZeroClaw as a background service

## Resources

- [ZeroClaw GitHub](https://github.com/zeroclaw-labs/zeroclaw)
- [ZeroClaw Documentation](https://github.com/zeroclaw-labs/zeroclaw/blob/master/docs/book/src/README.md)
- [ZeroClaw Discord](https://discord.com/invite/wDshRVqRjx)
