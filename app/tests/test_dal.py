"""Test module for Data Access Layer (DAL) functions."""

import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from app import models
from app.dal import create_sensor_data, get_sensor_rows_by_ids, list_sensor_data

# Setup in-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Context manager for creating a temporary database session for testing"""
    models.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=engine)


def test_create_sensor_data(db_session: Session):
    """Row creation test"""
    now = datetime.now()
    data = models.SensorData(
        id=uuid.uuid4(),
        sensor_id="sensor1",
        metric=models.MetricEnum.TEMPERATURE,
        value=25.5,
        timestamp=now,
    )

    obj = create_sensor_data(db_session, data)

    assert getattr(obj, "id") == data.id
    assert getattr(obj, "sensor_id") == "sensor1"
    assert getattr(obj, "metric") == models.MetricEnum.TEMPERATURE
    assert getattr(obj, "value") == 25.5
    assert getattr(obj, "timestamp") == now


def test_get_sensor_rows_by_ids(db_session: Session):
    """Fetch rows by IDs test"""
    now = datetime.now()
    data1 = models.SensorData(
        id=uuid.uuid4(),
        sensor_id="sensor1",
        metric=models.MetricEnum.TEMPERATURE,
        value=20,
        timestamp=now,
    )
    data2 = models.SensorData(
        id=uuid.uuid4(),
        sensor_id="sensor2",
        metric=models.MetricEnum.HUMIDITY,
        value=50,
        timestamp=now,
    )
    obj1 = create_sensor_data(db_session, data1)
    id1 = str(obj1.id)
    create_sensor_data(db_session, data2)

    results = get_sensor_rows_by_ids(db_session, [id1])

    assert len(results) == 1
    assert getattr(results[0], "sensor_id") == "sensor1"


def test_list_sensor_data(db_session: Session):
    """List and filter rows test"""
    now = datetime.now()
    data1 = models.SensorData(
        id=uuid.uuid4(),
        sensor_id="sensor1",
        metric=models.MetricEnum.TEMPERATURE,
        value=20,
        timestamp=now - timedelta(days=2),
    )
    data2 = models.SensorData(
        id=uuid.uuid4(),
        sensor_id="sensor1",
        metric=models.MetricEnum.HUMIDITY,
        value=50,
        timestamp=now,
    )
    data3 = models.SensorData(
        id=uuid.uuid4(),
        sensor_id="sensor2",
        metric=models.MetricEnum.TEMPERATURE,
        value=22,
        timestamp=now,
    )
    create_sensor_data(db_session, data1)
    create_sensor_data(db_session, data2)
    create_sensor_data(db_session, data3)

    # Test filter by sensor_id
    results = list_sensor_data(db_session, sensor_ids=[str(data1.id)])
    assert all(getattr(r, "sensor_id") == "sensor1" for r in results)

    # Test filter by metric
    results = list_sensor_data(db_session, metrics=[models.MetricEnum.TEMPERATURE])
    assert len(results) == 2
    assert all(getattr(r, "metric") == models.MetricEnum.TEMPERATURE for r in results)

    # Test filter by date range
    results = list_sensor_data(
        db_session, date_from=now - timedelta(days=1), date_to=now + timedelta(days=1)
    )
    assert len(results) == 2
