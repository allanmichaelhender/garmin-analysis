# Garmin MCP Server

A Model Context Protocol (MCP) server that exposes Garmin Connect fitness data as tools for ZeroClaw agent integration.

## Features

- **8 MCP Tools**: Get activities, details, heart rate data, analysis, summaries, personal records, training metrics, search
- **FastAPI + FastMCP**: Modern Python web framework with MCP protocol support
- **PostgreSQL Database**: Stores activities, heart rate data, user feedback, LLM summaries
- **ZeroClaw Integration**: HTTP transport for agent runtime
- **Docker Deployment**: Containerized with PostgreSQL

## Architecture

```
garmin-analysis/
├── backend/          # MCP server (FastAPI + FastMCP)
│   ├── app/
│   │   ├── clients/  # Garmin Connect API client
│   │   ├── tools/    # MCP tool implementations
│   │   └── models/   # Pydantic models
│   ├── alembic/      # Database migrations
│   └── scripts/      # Data ingestion scripts
├── zeroclaw/         # ZeroClaw agent runtime
└── docker-compose.yml # Orchestrates both services
```

## MCP Tools

1. `get_recent_activities` - Get activities with filters
2. `get_activity_details` - Detailed activity information
3. `get_heart_rate_data` - Heart rate data for activities
4. `analyze_activity` - Activity performance analysis
5. `get_activity_summary` - Summary statistics
6. `get_personal_records` - Personal best records
7. `get_training_metrics` - Training trends
8. `search_activities` - Search activities by criteria

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your PostgreSQL and Garmin credentials, and ZeroClaw API keys
```

### 2. Start Services

```bash
docker-compose up -d --build
```

This starts both the backend (MCP server) and ZeroClaw.

### 3. Database Setup

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Test database connection
curl http://localhost:8000/health
```

### 4. Data Ingestion

```bash
# Ingest recent activities
docker-compose exec backend python scripts/ingest_garmin.py

# Sync last 30 days
docker-compose exec backend python scripts/sync_garmin.py
```

### 5. ZeroClaw Integration

ZeroClaw is automatically configured to connect to the backend. See `zeroclaw-integration.md` for detailed setup.

### 6. Test MCP Server

```bash
# Test health check
curl http://localhost:8000/health

# Test tools list
curl -X POST http://localhost:8000/tools/list \
  -H "Content-Type: application/json"

# Test tool call
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"get_recent_activities","arguments":{"limit":5}}'
```

### 7. Test ZeroClaw

```bash
# Access ZeroClaw CLI
docker-compose exec zeroclaw zeroclaw agent
```

## ZeroClaw Integration

ZeroClaw is configured in `zeroclaw/config.toml` to connect to the backend via HTTP transport:

```toml
[mcp_servers.garmin]
transport = "http"
url = "http://backend:8000/mcp"
```

See `zeroclaw-integration.md` for detailed setup instructions.

## Database Schema

- **activities**: Garmin activity data
- **heart_rate_data**: Heart rate time series
- **user_feedback**: User feedback (future)
- **llm_summaries**: AI-generated summaries (future)

## Development

```bash
# Local development
cd mcp-server
pip install -r requirements.txt
uvicorn app.mcp_server:app --reload

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Monitoring

```bash
# View container logs
docker-compose logs -f mcp-server

# Test server health
curl http://localhost:8000/health
```

## Environment Variables

- `DATABASE_URL`: Neon PostgreSQL connection string
- `GARMIN_EMAIL`: Garmin Connect email
- `GARMIN_PASSWORD`: Garmin Connect password
- `LOG_LEVEL`: Logging level (default INFO)

## Troubleshooting

1. **Database connection fails**: Check DATABASE_URL format
2. **Garmin auth fails**: Verify credentials in .env
3. **Docker issues**: Check `docker-compose logs mcp-server`
4. **No activities**: Run ingestion script first

## License

MIT
