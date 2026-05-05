# MCP Server Quick Start Guide

This guide provides step-by-step instructions to get the MCP server up and running quickly. For detailed specifications and complete code implementations, refer to `mcp-server-spec.md`.

---

## Prerequisites

- Docker Desktop installed and running
- Garmin Connect account with credentials
- (Optional) Strava account with API credentials
- Text editor or IDE

---

## Phase 1: Initial Setup

### 1. Create Project Directory

```bash
mkdir mcp-server
cd mcp-server
```

### 2. Create Directory Structure

```bash
mkdir -p app/clients app/tools app/models alembic/versions scripts
```

### 3. Create Configuration Files

Create the following files using the complete versions from `mcp-server-spec.md`:

- `docker-compose.yml` (spec section 5)
- `Dockerfile` (spec section 6)
- `requirements.txt` (spec section 7)
- `.env.example` (spec section 8)
- `.gitignore` (spec section 9)

### 4. Create Python Package Files

Create these files with the content from spec section 9:

**`app/__init__.py`:**
```python
"""Sports Analytics MCP Server."""
__version__ = "1.0.0"
```

**`app/clients/__init__.py`:**
```python
"""API clients for Garmin and Strava."""
from .garmin import GarminClient
from .strava import StravaClient

__all__ = ["GarminClient", "StravaClient"]
```

**`app/tools/__init__.py`:**
```python
"""MCP tool implementations."""
```

**`app/models/__init__.py`:**
```python
"""Pydantic models for request/response validation."""
```

**`app/config.py`:**
```python
"""Configuration from environment variables."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql://admin:password@localhost:5432/sports_analytics"

    # Garmin
    garmin_email: str = ""
    garmin_password: str = ""

    # Strava
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_refresh_token: str = ""
    strava_access_token: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## Phase 2: Create Core Application Files

### 1. Garmin Client

Create `app/clients/garmin.py` using the complete code from spec section 1.

### 2. Strava Client

Create `app/clients/strava.py` using the complete code from spec section 2.

### 3. Database

Create `app/database.py` using the complete code from spec section 3.

### 4. MCP Server

Create `app/mcp_server.py` using the complete code from spec section 4.

---

## Phase 3: Database Setup

### 1. Initialize Alembic

```bash
docker-compose exec mcp-server alembic init alembic
```

### 2. Configure Alembic

Create `alembic/env.py` using the code from spec section 10.

### 3. Create Initial Migration

Create `alembic/versions/001_initial_schema.py` using the code from spec section 10.

---

## Phase 4: Configure Environment

### 1. Create .env File

```bash
cp .env.example .env
```

### 2. Edit .env with Your Credentials

```bash
nano .env  # or use your preferred editor
```

**Required variables:**
- `DB_PASSWORD` - Set a strong password for PostgreSQL
- `PGADMIN_EMAIL` - Any valid email format
- `PGADMIN_PASSWORD` - Set a password for pgAdmin
- `GARMIN_EMAIL` - Your Garmin Connect email
- `GARMIN_PASSWORD` - Your Garmin Connect password

**Optional variables (for Strava):**
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REFRESH_TOKEN`
- `STRAVA_ACCESS_TOKEN`

---

## Phase 5: Build and Start Services

### 1. Build and Start Docker Containers

```bash
docker-compose up -d --build
```

This will:
- Build the MCP server Docker image
- Start PostgreSQL database
- Start pgAdmin
- Start the MCP server
- Wait for PostgreSQL to be healthy before starting MCP server

### 2. Verify Services are Running

```bash
docker-compose ps
```

You should see all three services with "Up" status.

### 3. Check MCP Server Logs

```bash
docker-compose logs -f mcp-server
```

Press Ctrl+C to stop following logs.

---

## Phase 6: Database Setup

### 1. Run Database Migrations

```bash
docker-compose exec mcp-server alembic upgrade head
```

This will create all tables in PostgreSQL.

### 2. Verify Database Tables

```bash
docker-compose exec mcp-server python -c "
from app.database import db
from sqlalchemy import inspect
inspector = inspect(db.engine)
tables = inspector.get_table_names()
print('Tables:', tables)
"
```

Expected output:
```
Tables: ['activities', 'hr_data', 'user_feedback', 'llm_summaries', 'alembic_version']
```

### 3. Access pgAdmin (Optional)

- Open http://localhost:5050 in browser
- Login with PGADMIN_EMAIL and PGADMIN_PASSWORD from .env
- Add new server:
  - Host: postgres
  - Port: 5432
  - Database: sports_analytics
  - Username: admin
  - Password: DB_PASSWORD from .env

---

## Phase 7: Test MCP Server

### 1. Test Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{ "status": "healthy", "database": "connected" }
```

### 2. Test Tools List

```bash
curl -X POST http://localhost:8000/tools/list \
  -H "Content-Type: application/json"
```

Expected response: JSON with all 8 tools defined.

### 3. Test Tool Call

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_training_load",
    "arguments": {
      "days": 7,
      "activity_type": "all"
    }
  }'
```

Expected response (with empty database):
```json
{
  "result": {
    "days": 7,
    "activity_count": 0,
    "total_duration_seconds": 0,
    "total_distance_meters": 0,
    "avg_duration_seconds": 0,
    "avg_distance_meters": 0,
    "activities_per_day": 0
  },
  "error": null
}
```

---

## Phase 8: Data Ingestion

### 1. Create Ingestion Script

Create `scripts/ingest_garmin.py` using the code from spec section Phase 5.

### 2. Run Ingestion

```bash
docker-compose exec mcp-server python scripts/ingest_garmin.py
```

This will:
- Fetch up to 50 activities from Garmin Connect
- Store them in PostgreSQL
- Fetch HR time series data for each activity
- Store HR data in the database

### 3. Verify Data

Test with real data:

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_recent_activities",
    "arguments": {
      "limit": 5,
      "activity_type": "running"
    }
  }'
```

---

## Phase 9: Test with Real Queries

### 1. Get Recent Activities

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_recent_activities",
    "arguments": {
      "limit": 5
    }
  }'
```

### 2. Get Activity Details

Replace `YOUR_ACTIVITY_ID` with an actual activity ID from the previous step.

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_activity_details",
    "arguments": {
      "activity_id": "YOUR_ACTIVITY_ID",
      "include_hr": true
    }
  }'
```

### 3. Compare Activities

Replace activity IDs with actual IDs from your database.

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "compare_activities",
    "arguments": {
      "activity_ids": ["ACTIVITY_ID_1", "ACTIVITY_ID_2"],
      "metrics": ["duration", "distance", "avg_hr"]
    }
  }'
```

---

## Troubleshooting

### Database Connection Fails

- Check PostgreSQL is healthy: `docker-compose ps`
- Check DATABASE_URL in .env
- Verify DB_PASSWORD matches between .env and docker-compose.yml

### Garmin Authentication Fails

- Verify GARMIN_EMAIL and GARMIN_PASSWORD are correct
- Garmin may require MFA - if so, you may need to handle 2FA

### Docker Volume Permission Errors

```bash
docker-compose down
docker-compose down -v
docker-compose up -d
```

### MCP Server Not Accessible

- Check port 8000 is not in use
- Check container logs: `docker-compose logs mcp-server`

---

## Next Steps

After completing the quick start:

1. Set up Claude Desktop integration (see `mcp-server-testing-guide.md`)
2. Set up ZeroClaw integration (see `mcp-server-testing-guide.md`)
3. Configure periodic data sync (see `mcp-server-data-ingestion.md`)
4. Customize tools for your specific needs

---

## Development Tips

**Hot Reload:** The docker-compose.yml includes `--reload` flag for uvicorn, so code changes in `app/` directory will automatically reload the server.

**Database Queries:** Use pgAdmin at http://localhost:5050 to inspect database state and run queries.

**Logging:** View real-time logs:
```bash
docker-compose logs -f mcp-server
```

**Rebuilding:** After major changes, rebuild the image:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
