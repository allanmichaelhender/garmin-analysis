# MCP Server Implementation Plan

Implementation plan for building a Model Context Protocol (MCP) server that exposes Garmin fitness data as tools for ZeroClaw agent integration.

**Related Guides:**

- `readme.md` - Project overview and quickstart
- `zeroclaw-integration.md` - ZeroClaw setup and configuration

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Create Project Structure

- [x] Create root directory `backend/`
- [x] Create directory structure:
  ```
  backend/
  ├── app/
  │   ├── clients/
  │   ├── tools/
  │   └── models/
  ├── alembic/
  │   └── versions/
  └── scripts/
  ```

### 1.2 Create Configuration Files

- [x] Create `docker-compose.yml` in root with backend and zeroclaw services
- [x] Create `backend/Dockerfile` for FastAPI application with FastMCP
- [x] Create `backend/requirements.txt` with all dependencies
- [x] Create `.env.example` with environment variable templates
- [ ] Create `.gitignore` for sensitive files

### 1.3 Create Python Package Files

- [x] Create `backend/app/__init__.py`
- [x] Create `backend/app/clients/__init__.py`
- [x] Create `backend/app/tools/__init__.py`
- [x] Create `backend/app/models/__init__.py`
- [x] Create `backend/app/config.py`

### 1.4 Initialize Database

- [ ] Create `app/database.py` with sync SQLAlchemy models for activities, hr_data, user_feedback, llm_summaries
- [ ] Set up Alembic for database migrations
- [ ] Create initial migration `alembic/versions/001_initial_schema.py`
- [ ] Test Neon PostgreSQL connectivity

---

## Phase 2: API Client Integration

### 2.1 Garmin Client

- [ ] Create `app/clients/garmin.py` using python-garminconnect library
- [ ] Implement authentication with email/password
- [ ] Implement `get_activities()` method
- [ ] Implement `get_activity_details()` method
- [ ] Implement `extract_hr_time_series()` method
- [ ] Test authentication with Garmin Connect

---

## Phase 3: MCP Protocol Implementation

### 3.1 FastAPI + FastMCP Server

- [ ] Create `app/mcp_server.py` with FastAPI base and FastMCP mounting
- [ ] Implement 8 MCP tools with @mcp.tool() decorators:
  - get_recent_activities
  - get_activity_details
  - get_activity_by_date_range
  - get_activity_hr_data
  - compare_activities
  - get_training_load
  - get_user_feedback
  - get_llm_summary
- [ ] Mount FastMCP server at `/mcp` endpoint for HTTP transport (ZeroClaw)
- [ ] Add FastAPI health check endpoint at `/health`
- [ ] Add FastAPI tool execution endpoint at `/tools/call` (for testing)

### 3.2 Tool Helper Functions

- [ ] Implement `aggregate_hr_buckets()` for HR data aggregation
- [ ] Implement `extract_metric()` for activity metric extraction
- [ ] Add input validation for all tools
- [ ] Add error handling for all tools

---

## Phase 4: Docker Setup & Deployment

### 4.1 Build and Start Services

- [ ] Configure `.env` with actual credentials
- [ ] Run `docker-compose up -d --build`
- [ ] Verify all containers start successfully
- [ ] Check `docker-compose ps` status

### 4.2 Database Setup

- [ ] Run `docker-compose exec mcp-server alembic upgrade head`
- [ ] Verify tables created in Neon PostgreSQL
- [ ] Test database connection

### 4.3 MCP Server Verification

- [ ] Test FastAPI health check: `curl http://localhost:8000/health`
- [ ] Test MCP endpoint: `curl http://localhost:8000/mcp`
- [ ] Verify tools are registered via logs
- [ ] Test tool execution via HTTP endpoint
- [ ] Check logs: `docker-compose logs -f mcp-server`

---

## Phase 5: Data Ingestion

### 5.1 Create Ingestion Scripts

- [ ] Create `scripts/ingest_garmin.py` for initial data import
- [ ] Create `scripts/sync_garmin.py` for periodic sync
- [ ] Test Garmin data ingestion
- [ ] Verify HR data is stored correctly

### 5.2 Populate Database

- [ ] Run initial Garmin ingestion (5 most recent activities)
- [ ] Verify activities in database
- [ ] Verify HR data for activities
- [ ] Test queries against populated database

---

## Phase 6: Testing with MCP Tools

### 6.1 Test Activity Tools

- [ ] Test `get_recent_activities` with filters
- [ ] Test `get_activity_details` with HR data
- [ ] Test `get_activity_by_date_range`

### 6.2 Test HR Data Tools

- [ ] Test `get_activity_hr_data` with bucketing
- [ ] Verify HR aggregation works correctly

### 6.3 Test Analysis Tools

- [ ] Test `compare_activities` with multiple activities
- [ ] Test `get_training_load` for various time periods

### 6.4 Test User Data Tools

- [ ] Test `get_user_feedback`
- [ ] Test `get_llm_summary`

---

## Phase 7: ZeroClaw Integration

### 7.1 ZeroClaw Setup

- [ ] Install ZeroClaw
- [ ] Configure ZeroClaw MCP connection (HTTP transport to localhost:8000/mcp)
- [ ] Set up LLM provider (Anthropic, OpenAI, or Ollama)
- [ ] Configure ZeroClaw channels (Discord, Telegram, CLI, etc.)
- [ ] Test tool calls through ZeroClaw
- [ ] Test conversational queries
- [ ] Test multi-step tool chaining

---

## Phase 8: Testing & Verification

### 8.1 ZeroClaw Testing

- [ ] Test all 8 Garmin MCP tools through ZeroClaw
- [ ] Test channel integrations (Discord, Telegram, CLI)
- [ ] Test SOP engine with Garmin tools
- [ ] Test approval gates for high-risk operations
- [ ] Test tool receipts and audit logging
- [ ] Verify privacy guarantees (local execution if using Ollama)

### 8.2 Performance Testing

- [ ] Test with large activity datasets
- [ ] Test concurrent tool calls
- [ ] Test memory usage under load
- [ ] Test response times

---

## Dependencies & Prerequisites

### Required Software

- Docker Desktop
- Python 3.12+
- ZeroClaw

### Required Accounts

- Garmin Connect account
- LLM provider account (Anthropic, OpenAI, or Ollama for local)

### Environment Variables

- `DATABASE_URL` - Neon PostgreSQL connection string
- `GARMIN_EMAIL` - Garmin login email
- `GARMIN_PASSWORD` - Garmin login password

---

## Success Criteria Checklist

### Infrastructure

- [ ] Docker container starts successfully
- [ ] Neon PostgreSQL database initialized with correct schema
- [ ] FastAPI server accessible at http://localhost:8000
- [ ] MCP endpoint accessible at http://localhost:8000/mcp

### MCP Server

- [ ] FastMCP server starts successfully
- [ ] FastMCP mounts at /mcp endpoint
- [ ] 8 tools are registered and discoverable
- [ ] Tool execution works correctly via HTTP endpoint
- [ ] Garmin data retrieval works
- [ ] PostgreSQL queries work
- [ ] Error handling works properly
- [ ] HR data aggregation works

### Data Ingestion

- [ ] Garmin activities successfully ingested
- [ ] HR time series data stored correctly
- [ ] Database queries return expected results

### ZeroClaw Integration

- [ ] FastMCP server connects via HTTP at /mcp endpoint
- [ ] ZeroClaw can call tools successfully
- [ ] Channel integrations work (Discord, Telegram, CLI)
- [ ] Conversational queries work
- [ ] Multi-step chaining works
- [ ] SOP engine works with Garmin tools
- [ ] Approval gates function correctly

---

## Notes

- ZeroClaw uses HTTP transport to connect to MCP server at localhost:8000/mcp
- Hot reload is enabled in docker-compose for development
- Use pgAdmin for database inspection and queries
- All environment variables must be set in `.env` file
- Never commit `.env` file to version control
- ZeroClaw supports 30+ channels - configure as needed
