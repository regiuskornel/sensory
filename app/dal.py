"""Data Access Layer (DAL) for sensor data operations.
Provides functions to create and query sensor data records in the database.
"""

from sqlalchemy.orm import Session
from app import models, schemas


def create_sensor_data(
    session: Session, data: schemas.SensorDataIn
) -> models.SensorData:
    """
    Creates a new SensorData record in the database.
    Args:
        session (Session): The SQLAlchemy session used for database operations.
        data (schemas.SensorDataIn): The input data for the new sensor data record.
    Returns:
        models.SensorData: The newly created SensorData object, refreshed from the database.
    """
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


def get_sensor_rows_by_ids(
    session: Session, row_ids: list[str]
) -> list[models.SensorData]:
    """
    Retrieves SensorData records from the database by their IDs.
    Args:
        session (Session): The SQLAlchemy session used for database operations.
        row_ids (list[str]): List of SensorData record IDs to retrieve.
    Returns:
        list[models.SensorData]: List of SensorData objects matching the provided IDs.
    """
    return (
        session.query(models.SensorData).filter(models.SensorData.id.in_(row_ids)).all()
    )


# api/v1/sensors/list
def list_sensor_data(
    session: Session, sensor_ids=None, metrics=None, date_from=None, date_to=None
) -> list[models.SensorData]:
    """
    Lists SensorData records filtered by sensor IDs, metrics, and date range.
    Args:
        session (Session): The SQLAlchemy session used for database operations.
        sensor_ids (list, optional): List of sensor IDs to filter by.
        metrics (list, optional): List of metric names to filter by.
        date_from (datetime, optional): Start of the date range.
        date_to (datetime, optional): End of the date range.
    Returns:
        list[models.SensorData]: List of SensorData objects matching the filters or all if no filters provided.
    """
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

    q.limit(1000) # Limit to 1000 results to protect server resources.
    return q.all()
