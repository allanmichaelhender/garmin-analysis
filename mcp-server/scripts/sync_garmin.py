#!/usr/bin/env python3
"""Sync Garmin activities to database (periodic sync)."""
import sys
sys.path.insert(0, '/app')

from app.database import Database
from app.clients.garmin import garmin_client
from datetime import datetime, timedelta

def main():
    print("Starting Garmin sync...")
    
    # Initialize clients
    db = Database()
    garmin = garmin_client
    
    # Test connections
    if not garmin.test_connection():
        print("❌ Failed to connect to Garmin Connect")
        return False
    
    if not db.test_connection():
        print("❌ Failed to connect to database")
        return False
    
    print("✅ Connections successful")
    
    # Get activities from last 30 days
    print("📥 Fetching recent activities from Garmin Connect...")
    since_date = datetime.utcnow() - timedelta(days=30)
    activities = garmin.get_activities_since(since_date)
    
    if not activities:
        print("⚠️  No recent activities found")
        return True
    
    print(f"📊 Found {len(activities)} activities in last 30 days")
    
    # Process each activity
    stored_count = 0
    hr_stored_count = 0
    skipped_count = 0
    
    for i, activity in enumerate(activities, 1):
        activity_id = str(activity.get("activityId", ""))
        activity_type = activity.get("activityType", {}).get("typeKey", "unknown")
        
        print(f"🏃 Processing {i}/{len(activities)}: {activity_id} ({activity_type})")
        
        # Check if already exists
        existing = db.get_activity_by_id(activity_id)
        if existing:
            skipped_count += 1
            print(f"  ⏭️  Skipping (already exists)")
            continue
        
        # Store activity
        try:
            db.store_activity(
                activity_id=activity_id,
                activity_data=activity,
                source="garmin",
                modality=activity_type
            )
            stored_count += 1
            print(f"  ✅ Stored activity")
        except Exception as e:
            print(f"  ❌ Error storing activity: {e}")
            continue
        
        # Store HR data if available
        if activity.get("heartRateData"):
            try:
                hr_data = garmin.get_activity_hr_data(activity_id)
                if hr_data:
                    success = db.store_hr_data(activity_id, hr_data)
                    if success:
                        hr_stored_count += 1
                        print(f"  ❤️  Stored {len(hr_data)} HR data points")
                    else:
                        print(f"  ⚠️  Failed to store HR data")
                else:
                    print(f"  ⚠️  No HR data available")
            except Exception as e:
                print(f"  ❌ Error fetching HR data: {e}")
    
    print(f"\n📈 Sync Summary:")
    print(f"  Activities processed: {len(activities)}")
    print(f"  New activities stored: {stored_count}")
    print(f"  Activities skipped (already exist): {skipped_count}")
    print(f"  HR datasets stored: {hr_stored_count}")
    print(f"  ✅ Sync complete!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
