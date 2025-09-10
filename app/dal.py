"""Data Access Layer (DAL) for sensor data operations"""

import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends
from app import models
from app.database import get_db_session

class SensorDataDAL:
    """Data Access Layer for sensor data operations."""

    def __init__(self, session: Session):
        """
        Initialize the DAL with a database session.
        
        Args:
            session (Session): The SQLAlchemy session used for database operations.
        """
        self.session = session

    def create_sensor_data(self, data: models.SensorData) -> models.SensorData:
        """
        Creates a new SensorData record in the database.
        
        Args:
            data (models.SensorData): The SensorData object to create.
            
        Returns:
            models.SensorData: The newly created SensorData object. (MVP only, won't need in production)
        """
        self.session.add(data)
        self.session.commit()
        # Only for MVP. Should not return the object in production. See Command and query responsibility segregation (CQRS).
        self.session.refresh(data)
        return data

    def get_sensor_rows_by_ids(self, row_ids: List[str]) -> List[models.SensorData]:
        """
        Retrieves SensorData records from the database by their IDs.
        
        Args:
            row_ids (List[str]): List of SensorData record IDs to retrieve.
        
        Returns:
            List[models.SensorData]: List of SensorData objects matching the provided IDs.
        """
        ids = [uuid.UUID(rid) for rid in row_ids]
        return (
            self.session.query(models.SensorData)
            .filter(models.SensorData.id.in_(ids))
            .all()
        )

    def list_sensor_data(
        self,
        sensor_ids: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[models.SensorData]:
        """
        Lists SensorData records filtered by sensor IDs, metrics, and date range.
        
        Args:
            sensor_ids (Optional[List[str]]): List of sensor IDs to filter by.
            metrics (Optional[List[str]]): List of metric names to filter by.
            date_from (Optional[str]): Start of the date range (ISO format string).
            date_to (Optional[str]): End of the date range (ISO format string).
            
        Returns:
            List[models.SensorData]: List of SensorData objects matching the filters or all if no filters provided.
        """
        
        q = self.session.query(models.SensorData)
        if sensor_ids:
            q = q.filter(models.SensorData.sensor_id.in_(sensor_ids))
        if metrics:
            q = q.filter(models.SensorData.metric.in_(metrics))
        
        # Convert string dates to datetime objects if provided
        if date_from and date_to:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            q = q.filter(models.SensorData.timestamp.between(date_from_dt, date_to_dt))
        elif date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            q = q.filter(models.SensorData.timestamp >= date_from_dt)
        elif date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            q = q.filter(models.SensorData.timestamp <= date_to_dt)

        q = q.limit(1000)  # Hard limit to 1000 results to protect server resources.
        return q.all()


def get_sensor_data_dal(session: Session = Depends(get_db_session)) -> SensorDataDAL:
    """
    Creates and returns a SensorDataDAL instance with injected session.
    
    Args:
        session (Session): The database session dependency.
        
    Returns:
        SensorDataDAL: A DAL instance for sensor data operations.
    """
    return SensorDataDAL(session)
