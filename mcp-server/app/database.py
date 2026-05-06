from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.config import settings

# Create engine
engine = create_engine(settings.database_url, echo=settings.debug)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Activity(Base):
    """Activity table for storing Garmin activity data."""

    __tablename__ = "activities"

    id = Column(String, primary_key=True)  # Garmin activity ID
    source = Column(String, nullable=False, default="garmin")
    activity_data = Column(JSON, nullable=False)
    modality = Column(String, nullable=False)  # running, cycling, etc.
    start_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    distance_meters = Column(Float, nullable=True)
    has_hr_data = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HeartRateData(Base):
    """Heart rate time series data for activities."""

    __tablename__ = "hr_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(String, nullable=False)  # Foreign key to activities.id
    timestamp = Column(DateTime, nullable=False)
    heart_rate = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserFeedback(Base):
    """User feedback on activities."""

    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(String, nullable=False)  # Foreign key to activities.id
    feedback_type = Column(String, nullable=False)  # rating, comment, etc.
    feedback_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LLMSummary(Base):
    """LLM-generated summaries for activities."""

    __tablename__ = "llm_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(String, nullable=False)  # Foreign key to activities.id
    summary_type = Column(String, nullable=False)  # overview, analysis, etc.
    summary_text = Column(Text, nullable=False)
    model_used = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    """Database operations class."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def store_activity(
        self, activity_id: str, activity_data: Dict, source: str, modality: str
    ) -> Activity:
        """Store an activity in the database."""
        session = self.get_session()
        try:
            # Check if activity already exists
            existing = (
                session.query(Activity).filter(Activity.id == activity_id).first()
            )
            if existing:
                return existing

            # Create new activity
            activity = Activity(
                id=activity_id,
                source=source,
                activity_data=activity_data,
                modality=modality,
                start_time=self._parse_datetime(activity_data.get("startTime")),
                duration_seconds=activity_data.get("duration", 0),
                distance_meters=activity_data.get("distance"),
                has_hr_data=bool(activity_data.get("heartRateData")),
            )

            session.add(activity)
            session.commit()
            session.refresh(activity)
            return activity
        finally:
            session.close()

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Get an activity by ID."""
        session = self.get_session()
        try:
            return session.query(Activity).filter(Activity.id == activity_id).first()
        finally:
            session.close()

    def get_activities(
        self, limit: int = 20, activity_type: str = None, source: str = None
    ) -> List[Activity]:
        """Get recent activities with optional filters."""
        session = self.get_session()
        try:
            query = session.query(Activity)

            if activity_type:
                query = query.filter(Activity.modality.ilike(f"%{activity_type}%"))

            if source:
                query = query.filter(Activity.source == source)

            return query.order_by(Activity.start_time.desc()).limit(limit).all()
        finally:
            session.close()

    def get_activities_by_date_range(
        self, start_date: datetime, end_date: datetime, activity_type: str = None
    ) -> List[Activity]:
        """Get activities within a date range."""
        session = self.get_session()
        try:
            query = session.query(Activity).filter(
                Activity.start_time >= start_date, Activity.start_time <= end_date
            )

            if activity_type:
                query = query.filter(Activity.modality.ilike(f"%{activity_type}%"))

            return query.order_by(Activity.start_time.desc()).all()
        finally:
            session.close()

    def store_hr_data(self, activity_id: str, hr_data: List[Dict]) -> bool:
        """Store heart rate data for an activity."""
        session = self.get_session()
        try:
            # Clear existing HR data for this activity
            session.query(HeartRateData).filter(
                HeartRateData.activity_id == activity_id
            ).delete()

            # Insert new HR data
            for hr_point in hr_data:
                hr_record = HeartRateData(
                    activity_id=activity_id,
                    timestamp=self._parse_datetime(hr_point.get("timestamp")),
                    heart_rate=hr_point.get("heartRate"),
                )
                session.add(hr_record)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error storing HR data: {e}")
            return False
        finally:
            session.close()

    def get_hr_data(self, activity_id: str) -> List[HeartRateData]:
        """Get heart rate data for an activity."""
        session = self.get_session()
        try:
            return (
                session.query(HeartRateData)
                .filter(HeartRateData.activity_id == activity_id)
                .order_by(HeartRateData.timestamp)
                .all()
            )
        finally:
            session.close()

    def store_user_feedback(
        self, activity_id: str, feedback_type: str, feedback_data: Dict
    ) -> bool:
        """Store user feedback for an activity."""
        session = self.get_session()
        try:
            feedback = UserFeedback(
                activity_id=activity_id,
                feedback_type=feedback_type,
                feedback_data=feedback_data,
            )
            session.add(feedback)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error storing user feedback: {e}")
            return False
        finally:
            session.close()

    def store_llm_summary(
        self, activity_id: str, summary_type: str, summary_text: str, model_used: str
    ) -> bool:
        """Store LLM summary for an activity."""
        session = self.get_session()
        try:
            summary = LLMSummary(
                activity_id=activity_id,
                summary_type=summary_type,
                summary_text=summary_text,
                model_used=model_used,
            )
            session.add(summary)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error storing LLM summary: {e}")
            return False
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            session = self.get_session()
            session.execute("SELECT 1")
            session.close()
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    def _parse_datetime(self, dt_str: Any) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None

        if isinstance(dt_str, datetime):
            return dt_str

        try:
            # Handle various datetime formats from Garmin API
            if isinstance(dt_str, str):
                # Try ISO format first
                try:
                    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except ValueError:
                    # Try other common formats
                    formats = [
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%S",
                    ]
                    for fmt in formats:
                        try:
                            return datetime.strptime(dt_str, fmt)
                        except ValueError:
                            continue

            return None
        except Exception as e:
            print(f"Error parsing datetime {dt_str}: {e}")
            return None


# Global database instance
db = Database()
