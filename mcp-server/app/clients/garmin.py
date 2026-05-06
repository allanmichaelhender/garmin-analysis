from typing import Dict, List, Optional
from datetime import datetime
from garminconnect import Garmin

from app.config import settings


class GarminClient:
    """Client for interacting with Garmin Connect API."""

    def __init__(self):
        self.garmin = None
        self._authenticated = False

    def _authenticate(self) -> bool:
        """Authenticate with Garmin Connect."""
        if self._authenticated and self.garmin:
            return True

        try:
            self.garmin = Garmin(settings.garmin_email, settings.garmin_password)
            self.garmin.login()
            self._authenticated = True
            return True
        except Exception as e:
            print(f"Garmin authentication failed: {e}")
            return False

    def get_activities(self, limit: int = 20) -> List[Dict]:
        """Get recent activities from Garmin Connect."""
        if not self._authenticate():
            return []

        try:
            activities = self.garmin.get_activities(0, limit)
            return activities
        except Exception as e:
            print(f"Error fetching activities: {e}")
            return []

    def get_activity_details(self, activity_id: str) -> Optional[Dict]:
        """Get detailed information for a specific activity."""
        if not self._authenticate():
            return None

        try:
            details = self.garmin.get_activity_details(activity_id)
            return details
        except Exception as e:
            print(f"Error fetching activity details for {activity_id}: {e}")
            return None

    def get_activity_hr_data(self, activity_id: str) -> List[Dict]:
        """Get heart rate data for a specific activity."""
        if not self._authenticate():
            return []

        try:
            # Get activity details first
            details = self.get_activity_details(activity_id)
            if not details:
                return []

            # Extract heart rate data
            hr_data = []
            hr_samples = details.get("heartRateData", [])

            for sample in hr_samples:
                hr_point = {
                    "timestamp": sample.get("timestamp"),
                    "heartRate": sample.get("heartRate"),
                }
                hr_data.append(hr_point)

            return hr_data
        except Exception as e:
            print(f"Error fetching HR data for {activity_id}: {e}")
            return []

    def get_activities_since(self, since_date: datetime) -> List[Dict]:
        """Get activities since a specific date."""
        if not self._authenticate():
            return []

        try:
            # Get all activities (limit to reasonable number)
            activities = self.garmin.get_activities(0, 100)

            # Filter by date
            filtered_activities = []
            for activity in activities:
                activity_date = self._parse_activity_date(activity)
                if activity_date and activity_date >= since_date:
                    filtered_activities.append(activity)

            return filtered_activities
        except Exception as e:
            print(f"Error fetching activities since {since_date}: {e}")
            return []

    def get_user_profile(self) -> Optional[Dict]:
        """Get user profile information."""
        if not self._authenticate():
            return None

        try:
            profile = self.garmin.get_user_profile()
            return profile
        except Exception as e:
            print(f"Error fetching user profile: {e}")
            return None

    def get_daily_summary(self, date: datetime) -> Optional[Dict]:
        """Get daily summary for a specific date."""
        if not self._authenticate():
            return None

        try:
            summary = self.garmin.get_daily_summary(date.year, date.month, date.day)
            return summary
        except Exception as e:
            print(f"Error fetching daily summary for {date}: {e}")
            return None

    def _parse_activity_date(self, activity: Dict) -> Optional[datetime]:
        """Parse activity start time from activity data."""
        try:
            start_time = activity.get("startTime")
            if start_time:
                # Handle various datetime formats
                if isinstance(start_time, str):
                    # Try ISO format first
                    try:
                        return datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    except ValueError:
                        # Try other formats
                        formats = [
                            "%Y-%m-%dT%H:%M:%S.%fZ",
                            "%Y-%m-%dT%H:%M:%SZ",
                            "%Y-%m-%d %H:%M:%S",
                        ]
                        for fmt in formats:
                            try:
                                return datetime.strptime(start_time, fmt)
                            except ValueError:
                                continue
            return None
        except Exception as e:
            print(f"Error parsing activity date: {e}")
            return None

    def test_connection(self) -> bool:
        """Test connection to Garmin Connect."""
        return self._authenticate()


# Global Garmin client instance
garmin_client = GarminClient()
