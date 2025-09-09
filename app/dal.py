"""Data Access Layer (DAL) for sensor data operations.
Provides functions to create and query sensor data records in the database.
"""

from sqlalchemy.orm import Session
from app import models, schemas


def create_sensor_data(session: Session, data: schemas.SensorDataIn) -> models.SensorData:
    obj = models.SensorData(
        sensor_id=data.sensor_id,
        metric=data.metric,
        value=data.value,
    )
    if data.timestamp:
        setattr(obj, "timestamp", data.timestamp)
    
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def get_sensor_rows_by_ids(session: Session, row_ids: list[str]) -> list[models.SensorData]:
    return (
        session.query(models.SensorData)
        .filter(models.SensorData.id.in_(row_ids))
        .all()
    )

# api/v1/sensors/list
def list_sensor_data(
    session: Session, sensor_ids=None, metrics=None, date_from=None, date_to=None
) -> list[models.SensorData]:
    q = session.query(models.SensorData)
    if sensor_ids:
        q = q.filter(models.SensorData.sensor_id.in_(sensor_ids))
    if metrics:
        q = q.filter(models.SensorData.metric.in_(metrics))
    if date_from and date_to:
        q = q.filter(models.SensorData.timestamp.between(date_from, date_to))
    elif date_from:
        q = q.filter(models.SensorData.timestamp >= date_from)
    elif date_to:
        q = q.filter(models.SensorData.timestamp <= date_to)

    q.limit(1000)  # Limit to 1000 results to protect server resources.
    return q.all()
