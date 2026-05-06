from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
from pydantic import BaseModel

from app.config import settings
from app.database import db
from app.clients.garmin import garmin_client


# FastAPI app
app = FastAPI(title="Garmin MCP Server", version="1.0.0")

# FastMCP instance
mcp = FastMCP("garmin-mcp-server")


# Pydantic models for API
class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    result: Any
    error: Optional[str] = None


# Helper functions
def aggregate_hr_buckets(
    hr_data: List[Dict], bucket_size_minutes: int = 5
) -> List[Dict]:
    """Aggregate heart rate data into time buckets."""
    if not hr_data:
        return []

    buckets = []
    current_bucket = []
    bucket_start = None

    for hr_point in hr_data:
        timestamp = hr_point.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue

        if bucket_start is None:
            bucket_start = timestamp
            current_bucket = [hr_point]
        else:
            # Check if we need a new bucket
            if timestamp - bucket_start >= timedelta(minutes=bucket_size_minutes):
                # Calculate bucket stats
                if current_bucket:
                    avg_hr = sum(p.get("heartRate", 0) for p in current_bucket) / len(
                        current_bucket
                    )
                    buckets.append(
                        {
                            "start_time": bucket_start.isoformat(),
                            "end_time": timestamp.isoformat(),
                            "average_heart_rate": round(avg_hr, 1),
                            "sample_count": len(current_bucket),
                        }
                    )

                # Start new bucket
                bucket_start = timestamp
                current_bucket = [hr_point]
            else:
                current_bucket.append(hr_point)

    # Add last bucket
    if current_bucket and bucket_start:
        avg_hr = sum(p.get("heartRate", 0) for p in current_bucket) / len(
            current_bucket
        )
        buckets.append(
            {
                "start_time": bucket_start.isoformat(),
                "end_time": hr_data[-1].get("timestamp"),
                "average_heart_rate": round(avg_hr, 1),
                "sample_count": len(current_bucket),
            }
        )

    return buckets


def extract_metric(activity: Dict, metric_name: str) -> Optional[float]:
    """Extract a specific metric from activity data."""
    try:
        if metric_name == "duration":
            return float(activity.get("duration", 0))
        elif metric_name == "distance":
            return float(activity.get("distance", 0))
        elif metric_name == "avg_hr":
            hr_data = activity.get("heartRateData", [])
            if hr_data:
                return sum(p.get("heartRate", 0) for p in hr_data) / len(hr_data)
        elif metric_name == "max_hr":
            hr_data = activity.get("heartRateData", [])
            if hr_data:
                return max(p.get("heartRate", 0) for p in hr_data)
        elif metric_name == "calories":
            return float(activity.get("calories", 0))
        elif metric_name == "elevation_gain":
            return float(activity.get("elevationGain", 0))
        return None
    except Exception:
        return None


# MCP Tools
@mcp.tool()
def get_recent_activities(
    limit: int = 20, activity_type: str = None, source: str = "all"
) -> Dict[str, Any]:
    """Get recent activities with optional filters.

    Args:
        limit: Maximum number of activities to return (default: 20)
        activity_type: Filter by activity type (e.g., "running", "cycling")
        source: Filter by data source ("garmin", "strava", or "all")
    """
    try:
        activities = db.get_activities(
            limit=limit, activity_type=activity_type, source=source
        )

        result = []
        for activity in activities:
            result.append(
                {
                    "id": activity.id,
                    "source": activity.source,
                    "modality": activity.modality,
                    "start_time": activity.start_time.isoformat(),
                    "duration_seconds": activity.duration_seconds,
                    "distance_meters": activity.distance_meters,
                    "has_hr_data": activity.has_hr_data,
                    "activity_data": activity.activity_data,
                }
            )

        return {
            "activities": result,
            "total_count": len(result),
            "filters": {
                "limit": limit,
                "activity_type": activity_type,
                "source": source,
            },
        }
    except Exception as e:
        return {"error": f"Failed to get activities: {str(e)}"}


@mcp.tool()
def get_activity_details(activity_id: str, include_hr: bool = False) -> Dict[str, Any]:
    """Get detailed information for a specific activity.

    Args:
        activity_id: The ID of the activity to retrieve
        include_hr: Whether to include heart rate data (default: False)
    """
    try:
        activity = db.get_activity_by_id(activity_id)
        if not activity:
            return {"error": f"Activity {activity_id} not found"}

        result = {
            "id": activity.id,
            "source": activity.source,
            "modality": activity.modality,
            "start_time": activity.start_time.isoformat(),
            "duration_seconds": activity.duration_seconds,
            "distance_meters": activity.distance_meters,
            "has_hr_data": activity.has_hr_data,
            "activity_data": activity.activity_data,
        }

        if include_hr and activity.has_hr_data:
            hr_data = db.get_hr_data(activity_id)
            result["heart_rate_data"] = [
                {"timestamp": hr.timestamp.isoformat(), "heart_rate": hr.heart_rate}
                for hr in hr_data
            ]

        return result
    except Exception as e:
        return {"error": f"Failed to get activity details: {str(e)}"}


@mcp.tool()
def get_activity_by_date_range(
    start_date: str, end_date: str, activity_type: str = None
) -> Dict[str, Any]:
    """Get activities within a date range.

    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        activity_type: Filter by activity type (optional)
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)

        activities = db.get_activities_by_date_range(start_dt, end_dt, activity_type)

        result = []
        for activity in activities:
            result.append(
                {
                    "id": activity.id,
                    "source": activity.source,
                    "modality": activity.modality,
                    "start_time": activity.start_time.isoformat(),
                    "duration_seconds": activity.duration_seconds,
                    "distance_meters": activity.distance_meters,
                    "has_hr_data": activity.has_hr_data,
                }
            )

        return {
            "activities": result,
            "total_count": len(result),
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
                "activity_type": activity_type,
            },
        }
    except Exception as e:
        return {"error": f"Failed to get activities by date range: {str(e)}"}


@mcp.tool()
def get_activity_hr_data(
    activity_id: str, bucket_size_minutes: int = 5
) -> Dict[str, Any]:
    """Get heart rate data for an activity with optional bucketing.

    Args:
        activity_id: The ID of the activity
        bucket_size_minutes: Size of time buckets in minutes (default: 5)
    """
    try:
        hr_data = db.get_hr_data(activity_id)
        if not hr_data:
            return {"error": f"No heart rate data found for activity {activity_id}"}

        # Convert to list format
        raw_hr = [
            {"timestamp": hr.timestamp.isoformat(), "heart_rate": hr.heart_rate}
            for hr in hr_data
        ]

        result = {
            "activity_id": activity_id,
            "raw_data": raw_hr,
            "sample_count": len(raw_hr),
        }

        # Add bucketed data if requested
        if bucket_size_minutes > 0:
            buckets = aggregate_hr_buckets(raw_hr, bucket_size_minutes)
            result["bucketed_data"] = buckets
            result["bucket_size_minutes"] = bucket_size_minutes

        return result
    except Exception as e:
        return {"error": f"Failed to get heart rate data: {str(e)}"}


@mcp.tool()
def compare_activities(
    activity_ids: List[str], metrics: List[str] = None
) -> Dict[str, Any]:
    """Compare multiple activities across specified metrics.

    Args:
        activity_ids: List of activity IDs to compare
        metrics: List of metrics to compare (default: ["duration", "distance", "avg_hr"])
    """
    try:
        if not metrics:
            metrics = ["duration", "distance", "avg_hr"]

        comparison = {}
        for activity_id in activity_ids:
            activity = db.get_activity_by_id(activity_id)
            if not activity:
                comparison[activity_id] = {"error": "Activity not found"}
                continue

            activity_metrics = {}
            for metric in metrics:
                value = extract_metric(activity.activity_data, metric)
                activity_metrics[metric] = value

            comparison[activity_id] = {
                "modality": activity.modality,
                "start_time": activity.start_time.isoformat(),
                "metrics": activity_metrics,
            }

        # Calculate summary statistics
        summary = {}
        for metric in metrics:
            values = []
            for activity_data in comparison.values():
                if "metrics" in activity_data and metric in activity_data["metrics"]:
                    values.append(activity_data["metrics"][metric])

            if values:
                summary[metric] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                }

        return {
            "activities": comparison,
            "summary": summary,
            "metrics_compared": metrics,
        }
    except Exception as e:
        return {"error": f"Failed to compare activities: {str(e)}"}


@mcp.tool()
def get_training_load(days: int = 7, activity_type: str = "all") -> Dict[str, Any]:
    """Get training load analysis for recent activities.

    Args:
        days: Number of days to analyze (default: 7)
        activity_type: Filter by activity type (default: "all")
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        activities = db.get_activities_by_date_range(
            start_date, end_date, activity_type
        )

        total_duration = sum(a.duration_seconds for a in activities)
        total_distance = sum(a.distance_meters or 0 for a in activities)

        # Calculate daily averages
        avg_duration = total_duration / days
        avg_distance = total_distance / days

        return {
            "days": days,
            "activity_type": activity_type,
            "activity_count": len(activities),
            "total_duration_seconds": total_duration,
            "total_distance_meters": total_distance,
            "avg_duration_seconds": round(avg_duration, 1),
            "avg_distance_meters": round(avg_distance, 1),
            "activities_per_day": round(len(activities) / days, 1),
        }
    except Exception as e:
        return {"error": f"Failed to get training load: {str(e)}"}


@mcp.tool()
def get_user_feedback(
    activity_id: str = None, feedback_type: str = None
) -> Dict[str, Any]:
    """Get user feedback for activities.

    Args:
        activity_id: Specific activity ID (optional)
        feedback_type: Type of feedback to filter by (optional)
    """
    try:
        # This would query the user_feedback table
        # For now, return placeholder data
        return {
            "message": "User feedback feature not yet implemented",
            "activity_id": activity_id,
            "feedback_type": feedback_type,
        }
    except Exception as e:
        return {"error": f"Failed to get user feedback: {str(e)}"}


@mcp.tool()
def get_llm_summary(activity_id: str, summary_type: str = "overview") -> Dict[str, Any]:
    """Get LLM-generated summary for an activity.

    Args:
        activity_id: The ID of the activity
        summary_type: Type of summary ("overview", "analysis", "insights")
    """
    try:
        # This would query the llm_summaries table
        # For now, return placeholder data
        return {
            "message": "LLM summary feature not yet implemented",
            "activity_id": activity_id,
            "summary_type": summary_type,
        }
    except Exception as e:
        return {"error": f"Failed to get LLM summary: {str(e)}"}


# FastAPI endpoints
@app.get("/")
async def root():
    return {"message": "Garmin MCP Server", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_healthy = db.test_connection()
    garmin_healthy = garmin_client.test_connection()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "garmin": "connected" if garmin_healthy else "disconnected",
    }


@app.post("/tools/list")
async def list_tools():
    """List available MCP tools."""
    tools = []
    for tool_name, tool_func in mcp.tools.items():
        tools.append(
            {
                "name": tool_name,
                "description": tool_func.__doc__ or "No description available",
            }
        )

    return {"tools": tools}


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """Execute an MCP tool."""
    try:
        # Get the tool function
        tool_func = mcp.tools.get(request.name)
        if not tool_func:
            raise HTTPException(
                status_code=404, detail=f"Tool '{request.name}' not found"
            )

        # Execute the tool
        result = tool_func(**request.arguments)

        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


# Mount FastMCP server
mcp.mount(app, path="/mcp")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
