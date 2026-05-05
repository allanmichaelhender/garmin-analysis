# MCP Server Implementation Plan

## Overview

Implementation plan for building a Model Context Protocol (MCP) server that exposes Garmin/Strava fitness data as tools for conversational querying.

**Reference:** Complete specification available in `mcp-server-spec.md` (2507 lines with full code implementations)

**Related Guides:**

- `mcp-server-quickstart.md` - Step-by-step setup instructions
- `mcp-server-testing-guide.md` - Claude Desktop and ZeroClaw testing procedures
- `mcp-server-data-ingestion.md` - Data ingestion workflows

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Create Project Structure

- [ ] Create root directory `mcp-server/`
- [ ] Create directory structure:
  ```
  mcp-server/
  ├── app/
  │   ├── clients/
  │   ├── tools/
  │   └── models/
  ├── alembic/
  │   └── versions/
  └── scripts/
  ```

### 1.2 Create Configuration Files

- [ ] Create `docker-compose.yml` (complete version from spec section 5)
- [ ] Create `Dockerfile` (complete version from spec section 6)
- [ ] Create `requirements.txt` (complete version from spec section 7)
- [ ] Create `.env.example` (complete version from spec section 8)
- [ ] Create `.gitignore` (from spec section 9)

### 1.3 Create Python Package Files

- [ ] Create `app/__init__.py`
- [ ] Create `app/clients/__init__.py`
- [ ] Create `app/tools/__init__.py`
- [ ] Create `app/models/__init__.py`
- [ ] Create `app/config.py`

### 1.4 Initialize Database

- [ ] Create `app/database.py` with complete SQLAlchemy models (spec section 3)
- [ ] Set up Alembic configuration (spec section 10)
- [ ] Create initial migration `alembic/versions/001_initial_schema.py`
- [ ] Test database connectivity

---

## Phase 2: API Client Integration

### 2.1 Garmin Client

- [ ] Create `app/clients/garmin.py` (complete code from spec section 1)
- [ ] Test authentication with Garmin Connect
- [ ] Test `get_activities()` method
- [ ] Test `get_activity_details()` method
- [ ] Test `extract_hr_time_series()` method

### 2.2 Strava Client

- [ ] Create `app/clients/strava.py` (complete code from spec section 2)
- [ ] Test OAuth authentication
- [ ] Test token refresh mechanism
- [ ] Test `get_latest_activity()` method
- [ ] Test `get_activities_since()` method

---

## Phase 3: MCP Protocol Implementation

### 3.1 FastAPI Server

- [ ] Create `app/mcp_server.py` (complete code from spec section 4)
- [ ] Implement 8 MCP tools with handlers:
  - get_recent_activities
  - get_activity_details
  - get_activity_by_date_range
  - get_activity_hr_data
  - compare_activities
  - get_training_load
  - get_user_feedback
  - get_llm_summary
- [ ] Implement FastAPI endpoints:
  - GET `/` - Root endpoint
  - GET `/health` - Health check
  - POST `/tools/list` - List tools
  - POST `/tools/call` - Execute tool

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
- [ ] Verify tables created in PostgreSQL
- [ ] Access pgAdmin at http://localhost:5050
- [ ] Test database connection

### 4.3 MCP Server Verification

- [ ] Test health check: `curl http://localhost:8000/health`
- [ ] Test tools list: `curl -X POST http://localhost:8000/tools/list`
- [ ] Test tool call: `curl -X POST http://localhost:8000/tools/call`
- [ ] Check logs: `docker-compose logs -f mcp-server`

---

## Phase 5: Data Ingestion

### 5.1 Create Ingestion Scripts

- [ ] Create `scripts/ingest_garmin.py` (spec section Phase 5)
- [ ] Create `scripts/sync_garmin.py` for periodic sync
- [ ] Test Garmin data ingestion
- [ ] Verify HR data is stored correctly

### 5.2 Populate Database

- [ ] Run initial Garmin ingestion (50 activities)
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

## Phase 7: Client Integration Testing

### 7.1 Claude Desktop Setup

- [ ] Create `scripts/claude_mcp_wrapper.sh` (spec section Testing with Claude Desktop)
- [ ] Configure Claude Desktop config file
- [ ] Test stdio transport connection
- [ ] Test tool calls through Claude
- [ ] Test conversational queries
- [ ] Test multi-step tool chaining

### 7.2 ZeroClaw Setup

- [ ] Install ZeroClaw
- [ ] Configure ZeroClaw MCP connection (HTTP transport)
- [ ] Test tool calls through ZeroClaw
- [ ] Test WhatsApp channel integration
- [ ] Test conversational queries

---

## Phase 8: Comparison & Evaluation

### 8.1 Claude Desktop Evaluation

- [ ] Document setup difficulty
- [ ] Evaluate user experience
- [ ] Test feature completeness
- [ ] Note limitations and bugs

### 8.2 ZeroClaw Evaluation

- [ ] Document setup difficulty
- [ ] Evaluate user experience
- [ ] Test feature completeness
- [ ] Note limitations and bugs

### 8.3 Final Report

- [ ] Compare both approaches
- [ ] Document pros/cons
- [ ] Compare privacy models
- [ ] Compare deployment models
- [ ] Make recommendation

---

## Dependencies & Prerequisites

### Required Software

- Docker Desktop
- Python 3.11+
- Claude Desktop App (for testing)
- ZeroClaw (for testing)

### Required Accounts

- Garmin Connect account
- Strava account (optional, with API access)
- Anthropic Claude account (for Claude Desktop)

### Environment Variables

- `DB_PASSWORD` - PostgreSQL password
- `PGADMIN_EMAIL` - pgAdmin login email
- `PGADMIN_PASSWORD` - pgAdmin password
- `GARMIN_EMAIL` - Garmin login email
- `GARMIN_PASSWORD` - Garmin login password

---

## Success Criteria Checklist

### Infrastructure

- [ ] All Docker containers start successfully
- [ ] PostgreSQL database initialized with correct schema
- [ ] pgAdmin accessible at http://localhost:5050
- [ ] MCP server accessible at http://localhost:8000

### MCP Server

- [ ] Tools list endpoint returns 8 valid tool definitions
- [ ] Tool call endpoint executes functions correctly
- [ ] Garmin data retrieval works
- [ ] Strava data retrieval works (if configured)
- [ ] PostgreSQL queries work
- [ ] Error handling works properly
- [ ] HR data aggregation works

### Data Ingestion

- [ ] Garmin activities successfully ingested
- [ ] HR time series data stored correctly
- [ ] Database queries return expected results

### Claude Desktop Integration

- [ ] MCP server connects via stdio wrapper
- [ ] Claude can call tools successfully
- [ ] Conversational queries work (e.g., "Compare my last 5 runs")
- [ ] Multi-step chaining works

### ZeroClaw Integration

- [ ] MCP server connects via HTTP
- [ ] ZeroClaw can call tools successfully
- [ ] WhatsApp integration works (if configured)
- [ ] Conversational queries work

---

## Notes

- All code implementations are provided in `mcp-server-spec.md`
- The spec is self-contained - no need to reference parent project
- Prioritize getting Claude Desktop working first (simpler setup)
- Hot reload is enabled in docker-compose for development
- Use pgAdmin for database inspection and queries
- All environment variables must be set in `.env` file
- Never commit `.env` file to version control
