# MCP Server Testing Guide

This guide covers testing procedures for both Claude Desktop and ZeroClaw client integrations with the MCP server.

---

## Prerequisites

- MCP server running (see `mcp-server-quickstart.md`)
- Database populated with Garmin activities
- Claude Desktop App installed
- (Optional) ZeroClaw installed

---

## Part 1: Claude Desktop Integration

### Overview

Claude Desktop connects to MCP servers via stdio (standard input/output). Since our MCP server runs in Docker, we need a wrapper script to bridge the connection.

### 1. Create Claude MCP Wrapper Script

Create `scripts/claude_mcp_wrapper.sh`:

```bash
#!/bin/bash
# Wrapper script for Claude Desktop to connect to Docker MCP server
docker-compose exec -T mcp-server python -c "
import sys
import json
from app.mcp_server import TOOLS, TOOL_HANDLERS

# Read JSON-RPC requests from stdin
for line in sys.stdin:
    try:
        request = json.loads(line)

        if request.get('method') == 'tools/list':
            response = {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': {'tools': TOOLS}
            }
        elif request.get('method') == 'tools/call':
            params = request.get('params', {})
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            handler = TOOL_HANDLERS.get(tool_name)
            if handler:
                try:
                    result = handler(**arguments)
                    response = {
                        'jsonrpc': '2.0',
                        'id': request.get('id'),
                        'result': {'result': result}
                    }
                except Exception as e:
                    response = {
                        'jsonrpc': '2.0',
                        'id': request.get('id'),
                        'error': {'message': str(e)}
                    }
            else:
                response = {
                    'jsonrpc': '2.0',
                    'id': request.get('id'),
                    'error': {'message': f'Tool not found: {tool_name}'}
                }
        else:
            response = {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {'message': 'Unknown method'}
            }

        print(json.dumps(response))
        sys.stdout.flush()
    except Exception as e:
        print(json.dumps({
            'jsonrpc': '2.0',
            'id': request.get('id') if 'request' in locals() else None,
            'error': {'message': str(e)}
        }))
        sys.stdout.flush()
"
```

Make it executable:

```bash
chmod +x scripts/claude_mcp_wrapper.sh
```

### 2. Configure Claude Desktop

**On macOS:**
Configuration file: `~/Library/Application Support/Claude/claude_desktop_config.json`

**On Windows:**
Configuration file: `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "sports-analytics": {
      "command": "/absolute/path/to/mcp-server/scripts/claude_mcp_wrapper.sh"
    }
  }
}
```

**Important:** Replace `/absolute/path/to/mcp-server/` with the actual absolute path to your mcp-server directory.

**On Windows example:**
```json
{
  "mcpServers": {
    "sports-analytics": {
      "command": "C:\\Users\\yourname\\Documents\\GitHub\\garmin-analysis\\mcp-server\\scripts\\claude_mcp_wrapper.sh"
    }
  }
}
```

### 3. Restart Claude Desktop

Quit Claude Desktop completely and restart it.

### 4. Test Claude Desktop Integration

Open Claude Desktop and try these queries:

**Test 1: Check available tools**
```
What tools are available?
```

Expected: Claude should list all 8 MCP tools.

**Test 2: Get recent activities**
```
Show me my recent running activities
```

Expected: Claude should call `get_recent_activities` with activity_type="running" and display results.

**Test 3: Get activity details**
```
Show me details for my most recent activity including heart rate data
```

Expected: Claude should call `get_activity_details` with include_hr=true.

**Test 4: Compare activities**
```
Compare my last 3 runs by distance and duration
```

Expected: Claude should call `compare_activities` with multiple activity IDs and metrics.

**Test 5: Training load**
```
What's my training load for the last 30 days?
```

Expected: Claude should call `get_training_load` with days=30.

**Test 6: Multi-step query**
```
How has my running pace changed over my last 5 runs?
```

Expected: Claude should:
1. Call `get_recent_activities` to get last 5 runs
2. Call `compare_activities` to analyze pace
3. Provide a summary

### 5. Troubleshooting Claude Desktop

**Wrapper script not found:**
- Verify the absolute path in claude_desktop_config.json
- On Windows, use double backslashes or forward slashes
- Make sure the script is executable (chmod +x on Unix)

**Docker not accessible:**
- Ensure Docker Desktop is running
- Ensure mcp-server container is running: `docker-compose ps`
- Test wrapper script manually:
  ```bash
  ./scripts/claude_mcp_wrapper.sh <<< '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
  ```

**Tools not appearing in Claude:**
- Check Claude Desktop logs (Help → View Logs)
- Verify wrapper script outputs valid JSON
- Test wrapper script manually as above

**Tool calls failing:**
- Check MCP server logs: `docker-compose logs -f mcp-server`
- Verify database has data
- Test tool calls via HTTP curl commands first

---

## Part 2: ZeroClaw Integration

### Overview

ZeroClaw is a self-hosted agent runtime that can connect to MCP servers via HTTP transport. This approach is simpler than Claude Desktop's stdio approach since we can use the existing HTTP endpoints.

### 1. Install ZeroClaw

Follow ZeroClaw installation instructions from their repository. Typical installation:

```bash
# Via cargo (if using Rust)
cargo install zeroclaw

# Or download pre-built binary
# Check ZeroClaw repository for latest instructions
```

### 2. Configure ZeroClaw MCP Connection

Create a ZeroClaw configuration file `zeroclaw-config.yaml`:

```yaml
# zeroclaw-config.yaml
mcp_servers:
  sports-analytics:
    url: http://localhost:8000
    transport: http
    tools:
      - get_recent_activities
      - get_activity_details
      - get_activity_by_date_range
      - get_activity_hr_data
      - compare_activities
      - get_training_load
      - get_user_feedback
      - get_llm_summary

channels:
  whatsapp:
    enabled: true
    # Configure WhatsApp credentials per ZeroClaw documentation
```

### 3. Start ZeroClaw

```bash
zeroclaw --config zeroclaw-config.yaml
```

### 4. Test ZeroClaw Integration

**Test 1: Via CLI (if available)**
```bash
zeroclaw query "What is my training load for the last 30 days?"
```

**Test 2: Via WhatsApp (if configured)**
- Send a message to the configured WhatsApp number
- Try: "Show my recent activities"
- Try: "Compare my last 5 runs"
- Try: "What's my average heart rate for recent activities?"

### 5. Troubleshooting ZeroClaw

**Connection refused:**
- Ensure MCP server is running: `curl http://localhost:8000/health`
- Check ZeroClaw can reach localhost:8000
- Verify ZeroClaw configuration syntax

**Tools not available:**
- Check ZeroClaw logs
- Test MCP server HTTP endpoints directly with curl
- Verify tool names match exactly with MCP server definitions

**WhatsApp not working:**
- Follow ZeroClaw WhatsApp setup documentation
- Verify Twilio credentials if using Twilio
- Check WhatsApp webhook configuration

---

## Part 3: Comparison Testing

### Test Matrix

Create a comparison document to evaluate both approaches:

| Feature | Claude Desktop | ZeroClaw |
|---------|---------------|----------|
| Setup Difficulty | | |
| UI Quality | | |
| Tool Discovery | | |
| Tool Execution Speed | | |
| Multi-step Chaining | | |
| Error Handling | | |
| Documentation | | |
| Community Support | | |
| Privacy Model | | |
| Deployment Model | | |
| Cost | | |
| Customization | | |

### Test Scenarios

Run these scenarios on both platforms and document results:

1. **Simple Query:** "Show my last 5 activities"
2. **Filtered Query:** "Show my cycling activities from this week"
3. **Complex Query:** "Compare my running pace over the last month"
4. **Multi-step Query:** "Which activity had the highest heart rate this week?"
5. **Error Case:** Query with invalid activity ID
6. **Empty Result:** Query with date range with no activities

### Evaluation Criteria

**Setup Difficulty:**
- Time to complete initial setup
- Number of configuration steps
- Documentation quality
- Error messages clarity

**User Experience:**
- Interface intuitiveness
- Response time
- Error recovery
- Tool discovery ease

**Features:**
- Multi-step chaining
- Context awareness
- Tool combination
- Customization options

**Privacy & Deployment:**
- Data location
- Cloud vs local
- API usage
- Authentication

---

## Part 4: Automated Testing

### HTTP Endpoint Tests

Create a test script `scripts/test_mcp_endpoints.sh`:

```bash
#!/bin/bash

echo "Testing MCP Server Endpoints..."

# Test health check
echo "1. Health check..."
curl -s http://localhost:8000/health | jq '.'

# Test tools list
echo "2. Tools list..."
curl -s -X POST http://localhost:8000/tools/list \
  -H "Content-Type: application/json" | jq '.'

# Test get_training_load
echo "3. get_training_load..."
curl -s -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"get_training_load","arguments":{"days":7}}' | jq '.'

# Test get_recent_activities
echo "4. get_recent_activities..."
curl -s -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"get_recent_activities","arguments":{"limit":5}}' | jq '.'

echo "Tests complete!"
```

Run tests:
```bash
chmod +x scripts/test_mcp_endpoints.sh
./scripts/test_mcp_endpoints.sh
```

### Tool Function Tests

Create `scripts/test_tools.py`:

```python
#!/usr/bin/env python3
"""Test MCP tool functions directly."""
import sys
sys.path.insert(0, '/app')

from app.database import Database
from app.mcp_server import TOOL_HANDLERS

db = Database()

# Test get_training_load
print("Testing get_training_load...")
result = TOOL_HANDLERS['get_training_load'](days=7)
print(f"Result: {result}")

# Test get_recent_activities
print("\nTesting get_recent_activities...")
result = TOOL_HANDLERS['get_recent_activities'](limit=5)
print(f"Found {len(result)} activities")

# Test compare_activities
print("\nTesting compare_activities...")
activities = db.get_activities(limit=2)
if len(activities) >= 2:
    result = TOOL_HANDLERS['compare_activities'](
        activity_ids=[activities[0]['id'], activities[1]['id']],
        metrics=['duration', 'distance']
    )
    print(f"Comparison: {result}")
else:
    print("Need at least 2 activities to test comparison")

print("\nTests complete!")
```

Run tests:
```bash
docker-compose exec mcp-server python scripts/test_tools.py
```

---

## Part 5: Performance Testing

### Response Time Testing

```bash
# Test average response time
for i in {1..10}; do
  time curl -s -X POST http://localhost:8000/tools/call \
    -H "Content-Type: application/json" \
    -d '{"name":"get_recent_activities","arguments":{"limit":5}}' > /dev/null
done
```

### Load Testing

Using Apache Bench (ab):

```bash
# Install ab if needed
# Ubuntu/Debian: sudo apt-get install apache2-utils
# macOS: included with Xcode command line tools

# Test 100 requests with 10 concurrent
ab -n 100 -c 10 -p test_payload.json -T application/json \
  http://localhost:8000/tools/call
```

Create `test_payload.json`:
```json
{
  "name": "get_recent_activities",
  "arguments": {
    "limit": 5
  }
}
```

---

## Success Criteria

### Claude Desktop
- [ ] Wrapper script executes without errors
- [ ] Claude Desktop discovers all 8 tools
- [ ] Simple queries work correctly
- [ ] Multi-step chaining works
- [ ] Error handling is graceful

### ZeroClaw
- [ ] ZeroClaw connects to MCP server via HTTP
- [ ] All 8 tools are available
- [ ] Simple queries work correctly
- [ ] WhatsApp integration works (if configured)
- [ ] Error handling is graceful

### Comparison
- [ ] Test matrix completed
- [ ] All test scenarios run on both platforms
- [ ] Performance metrics collected
- [ ] Pros/cons documented
- [ ] Recommendation made

---

## Next Steps

After completing testing:

1. Document findings in a comparison report
2. Create screenshots or recordings of each platform
3. Note any bugs or limitations discovered
4. Make final recommendation based on testing results
5. Consider writing a blog post or internal documentation

---

## Notes

- Claude Desktop requires stdio wrapper script for Docker-based MCP servers
- ZeroClaw can use HTTP transport directly
- Both platforms support the same MCP protocol
- Performance may vary based on network conditions
- Consider testing on different operating systems
