# MCP Server Data Ingestion Guide

This guide covers workflows for ingesting Garmin and Strava activity data into the PostgreSQL database.

---

## Overview

The MCP server needs activity data to be useful. This guide covers:

- Initial data ingestion from Garmin Connect
- Periodic automated sync
- Manual data ingestion
- Data migration from SQLite (optional)
- Troubleshooting data issues

---

## Part 1: Initial Garmin Ingestion

### 1. Create Ingestion Script

Create `scripts/ingest_garmin.py`:

```python
#!/usr/bin/env python3
"""Ingest activities from Garmin Connect into PostgreSQL database."""
import sys
sys.path.insert(0, '/app')

from app.database import Database
from app.clients.garmin import GarminClient
from datetime import datetime

db = Database()
garmin = GarminClient()

print("Fetching activities from Garmin...")
activities = garmin.get_activities(limit=50)

print(f"Found {len(activities)} activities")
print("Storing in database...")

for activity in activities:
    activity_id = str(activity.get("activityId"))
    activity_type = activity.get("activityType", {}).get("typeKey", "unknown")

    # Check if already exists
    existing = db.get_activity_by_id(activity_id)
    if existing:
        print(f"  Skipping {activity_id} (already exists)")
        continue

    # Store activity
    try:
        db.store_activity(
            activity_id=activity_id,
            activity_data=activity,
            source="garmin",
            modality=activity_type
        )

        # Try to fetch HR data
        try:
            hr_data = garmin.extract_hr_time_series(int(activity_id))
            if hr_data:
                db.store_hr_data(activity_id, hr_data)
                print(f"  Stored {activity_id} with {len(hr_data)} HR points")
            else:
                print(f"  Stored {activity_id} (no HR data)")
        except Exception as e:
            print(f"  Stored {activity_id} (HR data error: {e})")

    except Exception as e:
        print(f"  Error storing {activity_id}: {e}")

print("Ingestion complete!")
```

### 2. Run Initial Ingestion

```bash
docker-compose exec mcp-server python scripts/ingest_garmin.py
```

This will:
- Fetch up to 50 activities from Garmin Connect
- Store them in PostgreSQL
- Fetch HR time series data for each activity
- Store HR data in the database
- Skip activities that already exist

### 3. Verify Ingestion

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

Or check via pgAdmin:
```sql
SELECT COUNT(*) FROM activities;
SELECT source, modality, COUNT(*) FROM activities GROUP BY source, modality;
SELECT COUNT(*) FROM hr_data;
```

---

## Part 2: Periodic Automated Sync

### 1. Create Sync Script

Create `scripts/sync_garmin.py`:

```python
#!/usr/bin/env python3
"""Sync Garmin activities to database."""
import sys
sys.path.insert(0, '/app')

from app.database import Database
from app.clients.garmin import GarminClient
from datetime import datetime, timedelta

db = Database()
garmin = GarminClient()

# Get last sync time from database or default to 30 days ago
# For simplicity, always fetch last 50 activities
activities = garmin.get_activities(limit=50)

for activity in activities:
    activity_id = str(activity.get("activityId"))
    activity_type = activity.get("activityType", {}).get("typeKey", "unknown")

    existing = db.get_activity_by_id(activity_id)
    if existing:
        # Check if HR data needs updating
        if not existing.get("has_hr_data"):
            try:
                hr_data = garmin.extract_hr_time_series(int(activity_id))
                if hr_data:
                    db.store_hr_data(activity_id, hr_data)
            except:
                pass
        continue

    # Store new activity
    db.store_activity(
        activity_id=activity_id,
        activity_data=activity,
        source="garmin",
        modality=activity_type
    )

    # Fetch HR data
    try:
        hr_data = garmin.extract_hr_time_series(int(activity_id))
        if hr_data:
            db.store_hr_data(activity_id, hr_data)
    except:
        pass

print("Sync complete")
```

### 2. Add Sync Service to Docker Compose

Update `docker-compose.yml` to add a periodic sync service:

```yaml
services:
  # ... existing services ...

  sync-garmin:
    build: .
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD}@postgres:5432/sports_analytics
      GARMIN_EMAIL: ${GARMIN_EMAIL}
      GARMIN_PASSWORD: ${GARMIN_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./scripts:/scripts
      - ./app:/app
    command: python /scripts/sync_garmin.py
    restart: "1h" # Run every hour
    networks:
      - mcp_network
```

### 3. Restart Docker Compose

```bash
docker-compose down
docker-compose up -d
```

The sync service will now run every hour automatically.

### 4. Manual Sync

To trigger a manual sync at any time:

```bash
docker-compose exec mcp-server python scripts/sync_garmin.py
```

---

## Part 3: Strava Ingestion (Optional)

### 1. Create Strava Ingestion Script

Create `scripts/ingest_strava.py`:

```python
#!/usr/bin/env python3
"""Ingest activities from Strava into PostgreSQL database."""
import sys
sys.path.insert(0, '/app')

from app.database import Database
from app.clients.strava import StravaClient
from datetime import datetime, timedelta

db = Database()
strava = StravaClient()

print("Fetching activities from Strava...")

# Get activities from last 30 days
since = datetime.utcnow() - timedelta(days=30)
activities = strava.get_activities_since(since)

print(f"Found {len(activities)} activities")
print("Storing in database...")

for activity in activities:
    activity_id = activity.get("id")
    activity_type = activity.get("type")

    # Check if already exists
    existing = db.get_activity_by_id(activity_id)
    if existing:
        print(f"  Skipping {activity_id} (already exists)")
        continue

    # Store activity
    try:
        db.store_activity(
            activity_id=activity_id,
            activity_data=activity,
            source="strava",
            modality=activity_type
        )
        print(f"  Stored {activity_id} - {activity.get('title')}")
    except Exception as e:
        print(f"  Error storing {activity_id}: {e}")

print("Ingestion complete!")
```

### 2. Run Strava Ingestion

```bash
docker-compose exec mcp-server python scripts/ingest_strava.py
```

### 3. Verify Strava Data

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_recent_activities",
    "arguments": {
      "limit": 5,
      "source": "strava"
    }
  }'
```

---

## Part 4: Manual Test Data (Optional)

For testing without Garmin/Strava credentials, insert test data directly:

```bash
docker-compose exec mcp-server python -c "
from app.database import Database
from datetime import datetime, timedelta
import random

db = Database()

# Insert test activities
for i in range(10):
    activity_id = f'test_{i:03d}'
    start_time = datetime.utcnow() - timedelta(days=i)
    
    db.store_activity(
        activity_id=activity_id,
        activity_data={
            'activityId': activity_id,
            'duration': random.randint(1800, 7200),
            'distance': random.randint(3000, 15000),
            'averageHR': random.randint(130, 160),
            'maxHR': random.randint(170, 190)
        },
        source='test',
        modality='running'
    )
    
    # Add HR data
    hr_data = []
    for j in range(100):
        hr_data.append({
            'timestamp': start_time + timedelta(seconds=j*30),
            'hr': random.randint(130, 170)
        })
    db.store_hr_data(activity_id, hr_data)

print('Test data inserted')
"
```

---

## Part 5: Data Migration from SQLite (Optional)

If you have existing data in the parent project's SQLite database:

### 1. Export SQLite Data

From the parent project directory:

```bash
sqlite3 activities.db ".dump activities" > activities_dump.sql
```

### 2. Convert to PostgreSQL Format

SQLite dump may need manual adjustments for PostgreSQL:

- Change `AUTOINCREMENT` to `SERIAL`
- Change `INTEGER PRIMARY KEY` to `SERIAL PRIMARY KEY`
- Change `TEXT` to `TEXT` or `VARCHAR`
- Adjust boolean values (0/1 to true/false)
- Remove SQLite-specific pragmas

### 3. Import to PostgreSQL

Via pgAdmin:
1. Open pgAdmin
2. Connect to the database
3. Open Query Tool
4. Paste the converted SQL
5. Execute

Or via psql:
```bash
psql -h localhost -U admin -d sports_analytics -f activities_dump.sql
```

### 4. Update Activity IDs

Garmin activity IDs are integers in SQLite but strings in PostgreSQL. You may need to convert:

```sql
UPDATE activities SET id = CAST(id AS TEXT);
```

---

## Part 6: Data Management

### View Data Statistics

```bash
docker-compose exec mcp-server python -c "
from app.database import Database

db = Database()

# Get activity counts
activities = db.get_activities(limit=1000)
print(f'Total activities: {len(activities)}')

# Count by source
by_source = {}
for a in activities:
    source = a.get('source', 'unknown')
    by_source[source] = by_source.get(source, 0) + 1
print(f'By source: {by_source}')

# Count by modality
by_modality = {}
for a in activities:
    modality = a.get('modality', 'unknown')
    by_modality[modality] = by_modality.get(modality, 0) + 1
print(f'By modality: {by_modality}')

# Count HR data
hr_count = sum(1 for a in activities if a.get('has_hr_data'))
print(f'Activities with HR data: {hr_count}')
"
```

### Delete Old Activities

```bash
docker-compose exec mcp-server python -c "
from app.database import Database
from datetime import datetime, timedelta

db = Database()

# Delete activities older than 1 year
cutoff = datetime.utcnow() - timedelta(days=365)

# This requires adding a delete method to Database class
# Or use SQL directly via pgAdmin
"
```

Via pgAdmin:
```sql
DELETE FROM hr_data 
WHERE activity_id IN (
    SELECT id FROM activities 
    WHERE start_time < NOW() - INTERVAL '1 year'
);

DELETE FROM activities 
WHERE start_time < NOW() - INTERVAL '1 year';
```

### Backup Database

```bash
# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U admin sports_analytics > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U admin sports_analytics < backup.sql
```

---

## Part 7: Troubleshooting

### Garmin Authentication Fails

**Issue:** Authentication errors when fetching Garmin data

**Solutions:**
- Verify GARMIN_EMAIL and GARMIN_PASSWORD in .env
- Garmin may require MFA - check if 2FA is enabled
- Try logging in to Garmin Connect in a browser to verify credentials
- Garmin may have rate limits - wait and retry

### HR Data Not Fetched

**Issue:** Activities stored but no HR data

**Solutions:**
- Some activities may not have HR data (e.g., walking without HR monitor)
- Check if `has_hr_data` flag is set correctly
- Manually re-fetch HR data for specific activities:
  ```python
  from app.database import Database
  from app.clients.garmin import GarminClient
  
  db = Database()
  garmin = GarminClient()
  
  activity_id = "YOUR_ACTIVITY_ID"
  hr_data = garmin.extract_hr_time_series(int(activity_id))
  if hr_data:
      db.store_hr_data(activity_id, hr_data)
  ```

### Duplicate Activities

**Issue:** Same activity appearing multiple times

**Solutions:**
- The ingestion script checks for existing activities by ID
- If duplicates exist, manually remove them via pgAdmin:
  ```sql
  DELETE FROM activities WHERE id IN (
    SELECT id FROM activities 
    GROUP BY id 
    HAVING COUNT(*) > 1
  );
  ```

### Strava Token Expired

**Issue:** Strava authentication errors

**Solutions:**
- The StravaClient includes automatic token refresh
- If refresh fails, manually re-authenticate to get new tokens
- Update STRAVA_REFRESH_TOKEN and STRAVA_ACCESS_TOKEN in .env

### Database Connection Errors

**Issue:** Cannot connect to database during ingestion

**Solutions:**
- Verify PostgreSQL container is running: `docker-compose ps`
- Check DATABASE_URL in .env
- Test database connection: `curl http://localhost:8000/health`
- Check database logs: `docker-compose logs postgres`

### Slow Ingestion

**Issue:** Ingestion taking too long

**Solutions:**
- Reduce the number of activities fetched (change `limit=50` to lower value)
- HR data fetching is slow - consider doing it in batches
- Add rate limiting to avoid Garmin API limits
- Run ingestion during off-peak hours

---

## Part 8: Best Practices

### Ingestion Schedule

- **Initial:** Fetch 50-100 activities to get started
- **Ongoing:** Sync every hour via Docker service
- **Manual:** Run sync after new activities are recorded

### Rate Limiting

Garmin and Strava may have rate limits. Consider adding delays:

```python
import time

for activity in activities:
    # ... process activity ...
    time.sleep(0.5)  # 500ms delay between requests
```

### Error Handling

Always wrap API calls in try-except blocks:

```python
try:
    activities = garmin.get_activities(limit=50)
except Exception as e:
    print(f"Error fetching activities: {e}")
    # Continue with next step or exit gracefully
```

### Data Validation

Validate data before storing:

```python
if not activity.get("activityId"):
    print(f"Skipping activity with no ID")
    continue

if activity.get("duration", 0) <= 0:
    print(f"Skipping activity with invalid duration")
    continue
```

### Logging

Add detailed logging for debugging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Processing activity {activity_id}")
logger.debug(f"Activity data: {activity}")
logger.error(f"Error storing activity: {e}")
```

---

## Success Criteria

- [ ] Initial Garmin ingestion completes successfully
- [ ] Activities appear in database
- [ ] HR data is stored correctly
- [ ] MCP tools return data from database
- [ ] Periodic sync service runs automatically
- [ ] Strava ingestion works (if configured)
- [ ] Data can be queried via MCP tools
- [ ] No duplicate activities
- [ ] Database performance is acceptable

---

## Next Steps

After setting up data ingestion:

1. Configure automated sync schedule
2. Set up database backups
3. Monitor disk space usage
4. Set up alerts for ingestion failures
5. Consider data retention policies
