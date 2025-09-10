"""Test module for Data Access Layer (DAL) class."""

import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
from app.dal import SensorDataDAL

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


@pytest.fixture(scope="function")
def sensor_dal(db_session):
    """Fixture to create a SensorDataDAL instance for testing"""
    return SensorDataDAL(db_session)


def test_create_sensor_data(sensor_dal: SensorDataDAL):
    """Row creation test"""
    now = datetime.now()
    data = models.SensorData(
        id=uuid.uuid4(),
        sensor_id="sensor1",
        metric=models.MetricEnum.TEMPERATURE,
        value=25.5,
        timestamp=now,
    )

    obj = sensor_dal.create_sensor_data(data)

    assert getattr(obj, "id") == data.id
    assert getattr(obj, "sensor_id") == "sensor1"
    assert getattr(obj, "metric") == models.MetricEnum.TEMPERATURE
    assert getattr(obj, "value") == 25.5
    assert getattr(obj, "timestamp") == now


def test_get_sensor_rows_by_ids(sensor_dal: SensorDataDAL):
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
    obj1 = sensor_dal.create_sensor_data(data1)
    id1 = str(obj1.id)
    sensor_dal.create_sensor_data(data2)

    results = sensor_dal.get_sensor_rows_by_ids([id1])

    assert len(results) == 1
    assert getattr(results[0], "sensor_id") == "sensor1"


def test_list_sensor_data(sensor_dal: SensorDataDAL):
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
    sensor_dal.create_sensor_data(data1)
    sensor_dal.create_sensor_data(data2)
    sensor_dal.create_sensor_data(data3)

    # Test filter by sensor_id
    results = sensor_dal.list_sensor_data(sensor_ids=["sensor1"])
    assert all(getattr(r, "sensor_id") == "sensor1" for r in results)

    # Test filter by metric (convert enum to string)
    results = sensor_dal.list_sensor_data(metrics=["temperature"])
    assert len(results) == 2
    assert all(getattr(r, "metric") == models.MetricEnum.TEMPERATURE for r in results)

    # Test filter by date range (convert datetime to ISO string)
    date_from_str = (now - timedelta(days=1)).isoformat()
    date_to_str = (now + timedelta(days=1)).isoformat()
    results = sensor_dal.list_sensor_data(date_from=date_from_str, date_to=date_to_str)
    assert len(results) == 2
