import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Float, DateTime, Enum as SAEnum, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from app import models, schemas
from app.dal import create_sensor_data, get_sensor_rows_by_ids, list_sensor_data

# Setup in-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        models.Base.metadata.drop_all(bind=engine)


def test_create_sensor_data(db: Session):
    data = schemas.SensorDataIn(
        sensor_id="sensor1",
        metric=schemas.MetricEnum.temperature,
        value=25.5,
        timestamp=datetime.utcnow(),
    )
    obj = create_sensor_data(db, data)
    assert getattr(obj, "sensor_id") == "sensor1"
    assert getattr(obj, "metric") == schemas.MetricEnum.temperature
    assert getattr(obj, "value") == 25.5

def test_get_sensor_rows_by_ids(db: Session):
    now = datetime.utcnow()
    data1 = schemas.SensorDataIn(
        sensor_id="sensor1",
        metric=schemas.MetricEnum.temperature,
        value=20,
        timestamp=now,
    )
    data2 = schemas.SensorDataIn(
        sensor_id="sensor2", metric=schemas.MetricEnum.humidity, value=50, timestamp=now
    )
    obj1 = create_sensor_data(db, data1)
    obj2 = create_sensor_data(db, data2)
    # Convert UUID to string for the DAL function
    results = get_sensor_rows_by_ids(db, [str(obj1.id)])
    assert len(results) == 1
    assert getattr(results[0], "sensor_id") == "sensor1"


def test_list_sensor_data(db: Session):
    now = datetime.utcnow()
    data1 = schemas.SensorDataIn(
        sensor_id="sensor1",
        metric=schemas.MetricEnum.temperature,
        value=20,
        timestamp=now,
    )
    data2 = schemas.SensorDataIn(
        sensor_id="sensor1", metric=schemas.MetricEnum.humidity, value=50, timestamp=now
    )
    data3 = schemas.SensorDataIn(
        sensor_id="sensor2",
        metric=schemas.MetricEnum.temperature,
        value=22,
        timestamp=now,
    )
    create_sensor_data(db, data1)
    create_sensor_data(db, data2)
    create_sensor_data(db, data3)
    # Test filter by sensor_id
    results = list_sensor_data(db, sensor_ids=["sensor1"])
    assert all(getattr(r, "sensor_id") == "sensor1" for r in results)
    # Test filter by metric
    results = list_sensor_data(db, metrics=[schemas.MetricEnum.temperature])
    assert all(getattr(r, "metric") == schemas.MetricEnum.temperature for r in results)
    # Test filter by date range
    results = list_sensor_data(
        db, date_from=now - timedelta(days=1), date_to=now + timedelta(days=1)
    )
    assert len(results) == 3
