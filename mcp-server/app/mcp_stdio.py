#!/usr/bin/env python3
"""
Garmin MCP Server - stdio transport for Claude Desktop
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.config import settings
from app.database import db
from app.clients.garmin import garmin_client


# Create MCP server
server = Server("garmin-mcp-server")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_recent_activities",
            description="Get recent Garmin activities",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of activities to return",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_activity_details",
            description="Get detailed information for a specific activity",
            inputSchema={
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "string",
                        "description": "Garmin activity ID"
                    }
                },
                "required": ["activity_id"]
            }
        ),
        Tool(
            name="get_heart_rate_data",
            description="Get heart rate data for activities",
            inputSchema={
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "string",
                        "description": "Garmin activity ID (optional, gets recent if not provided)"
                    }
                }
            }
        ),
        Tool(
            name="analyze_activity",
            description="Perform analysis on activity data",
            inputSchema={
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "string",
                        "description": "Garmin activity ID"
                    }
                },
                "required": ["activity_id"]
            }
        ),
        Tool(
            name="get_activity_summary",
            description="Get summary statistics for activities",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to summarize",
                        "default": 30
                    }
                }
            }
        ),
        Tool(
            name="get_personal_records",
            description="Get personal records from Garmin data",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_training_metrics",
            description="Get training metrics and trends",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period (week, month, year)",
                        "default": "month"
                    }
                }
            }
        ),
        Tool(
            name="search_activities",
            description="Search activities by criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "activity_type": {
                        "type": "string",
                        "description": "Type of activity (running, cycling, etc.)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_recent_activities":
            limit = arguments.get("limit", 10)
            activities = await garmin_client.get_recent_activities(limit)
            return [TextContent(type="text", text=json.dumps(activities, indent=2))]
        
        elif name == "get_activity_details":
            activity_id = arguments["activity_id"]
            details = await garmin_client.get_activity_details(activity_id)
            return [TextContent(type="text", text=json.dumps(details, indent=2))]
        
        elif name == "get_heart_rate_data":
            activity_id = arguments.get("activity_id")
            hr_data = await garmin_client.get_heart_rate_data(activity_id)
            return [TextContent(type="text", text=json.dumps(hr_data, indent=2))]
        
        elif name == "analyze_activity":
            activity_id = arguments["activity_id"]
            analysis = await garmin_client.analyze_activity(activity_id)
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
        
        elif name == "get_activity_summary":
            days = arguments.get("days", 30)
            summary = await garmin_client.get_activity_summary(days)
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        
        elif name == "get_personal_records":
            records = await garmin_client.get_personal_records()
            return [TextContent(type="text", text=json.dumps(records, indent=2))]
        
        elif name == "get_training_metrics":
            period = arguments.get("period", "month")
            metrics = await garmin_client.get_training_metrics(period)
            return [TextContent(type="text", text=json.dumps(metrics, indent=2))]
        
        elif name == "search_activities":
            activity_type = arguments.get("activity_type")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            results = await garmin_client.search_activities(activity_type, start_date, end_date)
            return [TextContent(type="text", text=json.dumps(results, indent=2))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
