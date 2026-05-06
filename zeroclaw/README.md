# ZeroClaw Docker Setup

This directory contains the Docker configuration for running ZeroClaw with the Garmin MCP backend.

## Quick Start

The ZeroClaw service is managed from the root docker-compose.yml. This directory contains the ZeroClaw-specific configuration.

```bash
# From project root
cp .env.example .env
# Edit .env with your API keys

# Start all services (backend + zeroclaw)
docker-compose up -d --build

# View logs
docker-compose logs -f zeroclaw
```

## Architecture

ZeroClaw connects to the backend service via Docker network:

- **backend**: Garmin MCP server (FastAPI + FastMCP) at port 8000
- **zeroclaw**: ZeroClaw agent runtime connecting to backend via HTTP

## Configuration

### Environment Variables (root .env)

- `ANTHROPIC_API_KEY`: Anthropic API key for Claude
- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `DISCORD_BOT_TOKEN`: Discord bot token (optional)
- `TELEGRAM_BOT_TOKEN`: Telegram bot token (optional)

### ZeroClaw Config (config.toml)

Edit `config.toml` to:

- Change LLM provider
- Configure channels
- Adjust security settings
- Add SOPs

The MCP server is configured as `http://backend:8000/mcp` via Docker network.

## Usage

### CLI Channel

```bash
docker-compose exec zeroclaw zeroclaw agent
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f zeroclaw
docker-compose logs -f backend
```

### Stop Services

```bash
docker-compose down
```

## Network

Both services run on the `garmin-network` bridge network, allowing ZeroClaw to reach the backend at `http://backend:8000/mcp`.

## Data Persistence

ZeroClaw data is persisted in a Docker volume `zeroclaw-data` for configuration and state.

## Troubleshooting

**ZeroClaw can't reach backend:**

- Check both services are running: `docker-compose ps`
- Verify network connectivity: `docker-compose exec zeroclaw ping backend`

**LLM provider errors:**

- Verify API keys in root .env
- Check provider status
- Try switching to a different provider
