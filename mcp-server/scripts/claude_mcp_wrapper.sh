#!/bin/bash
# Wrapper script for Claude Desktop to connect to Docker MCP server
docker-compose exec -T mcp-server python -c "
import sys
import json
from app.mcp_server import mcp

# Read JSON-RPC requests from stdin
for line in sys.stdin:
    try:
        request = json.loads(line)

        if request.get('method') == 'tools/list':
            tools = []
            for tool_name, tool_func in mcp.tools.items():
                tools.append({
                    'name': tool_name,
                    'description': tool_func.__doc__ or 'No description available'
                })
            response = {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': {'tools': tools}
            }
        elif request.get('method') == 'tools/call':
            params = request.get('params', {})
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            # Get the tool function
            tool_func = mcp.tools.get(tool_name)
            if tool_func:
                try:
                    result = tool_func(**arguments)
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
