"""Test module for API endpoints."""

import uuid
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import SensorData, MetricEnum
from app.main import app
from app import schemas
from app.api.endpoints import get_llm_agent
from app.dal import get_sensor_data_dal, SensorDataDAL

client = TestClient(app)


def test_create_sensor_data():
    """Test sensor data creation endpoint."""

    # Create a mock DAL class
    class MockSensorDataDAL:
        def create_sensor_data(self, data):
            return schemas.SensorDataOut(
                id="acff4f6d-6e51-4b20-be91-35571be93e0a",
                sensor_id="sensor1",
                metric=schemas.MetricEnum.TEMPERATURE,
                value=25.5,
                timestamp=datetime(2025, 1, 1),
            )

    def mock_get_sensor_data_dal():
        return MockSensorDataDAL()

    # Use FastAPI's dependency override mechanism
    app.dependency_overrides[get_sensor_data_dal] = mock_get_sensor_data_dal

    try:
        payload = {
            "sensor_id": "sensor1",
            "metric": "temperature",
            "value": 25.5,
            "timestamp": "2025-01-01T00:00:00",
        }

        response = client.post("/api/v1/sensors/data", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "acff4f6d-6e51-4b20-be91-35571be93e0a"
        assert data["sensor_id"] == "sensor1"
        assert data["metric"] == "temperature"
        assert data["value"] == 25.5
        assert data["timestamp"] == "2025-01-01T00:00:00"
    finally:
        # Clean up the dependency override
        app.dependency_overrides.clear()


def test_list_sensor_data():
    """Test sensor data listing endpoint."""

    # Create a mock DAL class
    class MockSensorDataDAL:
        def list_sensor_data(self, sensor_ids, metrics, date_from, date_to):
            return [
                schemas.SensorDataOut(
                    id="acff4f6d-6e51-4b20-be91-35571be93e0a",
                    sensor_id="sensor1",
                    metric=schemas.MetricEnum.TEMPERATURE,
                    value=25.5,
                    timestamp=datetime(2025, 1, 1),
                )
            ]

    def mock_get_sensor_data_dal():
        return MockSensorDataDAL()

    # Use FastAPI's dependency override mechanism
    app.dependency_overrides[get_sensor_data_dal] = mock_get_sensor_data_dal

    try:
        response = client.get("/api/v1/sensors/list", params={"sensor_id": "sensor1"})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == "acff4f6d-6e51-4b20-be91-35571be93e0a"
        assert data[0]["sensor_id"] == "sensor1"
        assert data[0]["metric"] == "temperature"
        assert data[0]["value"] == 25.5
        assert data[0]["timestamp"] == "2025-01-01T00:00:00"
    finally:
        # Clean up the dependency override
        app.dependency_overrides.clear()


def test_batch_get_sensor_data():
    """Test batch sensor data retrieval endpoint."""

    # Create a mock DAL class
    class MockSensorDataDAL:
        def get_sensor_rows_by_ids(self, sensor_ids):
            return [
                schemas.SensorDataOut(
                    id="acff4f6d-6e51-4b20-be91-35571be93e0a",
                    sensor_id="sensor1",
                    metric=schemas.MetricEnum.TEMPERATURE,
                    value=25.5,
                    timestamp=datetime(2025, 1, 1),
                )
            ]

    def mock_get_sensor_data_dal():
        return MockSensorDataDAL()

    app.dependency_overrides[get_sensor_data_dal] = mock_get_sensor_data_dal

    try:
        payload = {"sensor_ids": ["sensor1"]}

        response = client.post("/api/v1/sensors/batch_get", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["sensor_id"] == "sensor1"
    finally:
        # Clean up the dependency override
        app.dependency_overrides.clear()


def test_batch_get_sensor_data_integration():
    """Integration test for batch sensor data retrieval with underlying database."""

    # Create SQLite in-memory database with thread-safe settings
    engine = create_engine(
        "sqlite:///:memory:",
        echo=True,  # Enable to see SQL statements
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    sensor_data_1 = SensorData(
        id=uuid.uuid4(),
        sensor_id="test_sensor_1",
        metric=MetricEnum.TEMPERATURE,
        value=23.5,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
    )

    sensor_data_2 = SensorData(
        id=uuid.uuid4(),
        sensor_id="test_sensor_2",
        metric=MetricEnum.HUMIDITY,
        value=65.0,
        timestamp=datetime(2025, 1, 1, 12, 5, 0),
    )

    # Add another record that shouldn't be returned
    sensor_data_3 = SensorData(
        id=uuid.uuid4(),
        sensor_id="test_sensor_3",
        metric=MetricEnum.PRESSURE,
        value=1013.25,
        timestamp=datetime(2025, 1, 1, 12, 10, 0),
    )

    # Create a session and populate test data
    session_local = sessionmaker(bind=engine)
    session = session_local()
    try:
        session.add_all([sensor_data_1, sensor_data_2, sensor_data_3])
        session.commit()

        def mock_get_sensor_data_dal():
            return SensorDataDAL(session)

        from app.main import app  # Re-import the FastAPI app
        app.dependency_overrides[get_sensor_data_dal] = mock_get_sensor_data_dal

        # Test the endpoint
        payload = {"sensor_ids": [str(sensor_data_1.id), str(sensor_data_2.id)]}
        response = client.post("/api/v1/sensors/batch_get", json=payload)

        # API endpoint assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Check the returned data from API
        ids_returned_api = [item["id"] for item in data]
        assert str(sensor_data_1.id) in ids_returned_api
        assert str(sensor_data_2.id) in ids_returned_api

        # Verify specific data for first record from API
        record_1_api = next(
            item for item in data if item["id"] == str(sensor_data_1.id)
        )
        assert record_1_api["sensor_id"] == "test_sensor_1"
        assert record_1_api["metric"] == "temperature"  # Should be lowercase value
        assert record_1_api["value"] == 23.5

        # Verify specific data for second record from API
        record_2_api = next(
            item for item in data if item["id"] == str(sensor_data_2.id)
        )
        assert record_2_api["sensor_id"] == "test_sensor_2"
        assert record_2_api["metric"] == "humidity"  # Should be lowercase value
        assert record_2_api["value"] == 65.0
    finally:
        try:
            session.close()
        except:
            pass  # Ignore any cleanup errors
        from app.main import app  # Re-import the FastAPI app

        app.dependency_overrides.clear()


def test_ask_sensor_data():
    """Test natural language query endpoint w/o actual LLM API call."""

    def mock_invoke(args):
        return {
            "output": '{"answer":"The average temperature is 23.93 degrees.","followup_question":"What is the maximum temperature recorded?","id_list":null,"aggregation":"23.93"}'
        }

    # Create a mock object with an invoke method
    class MockAgent:
        def invoke(self, args):
            return mock_invoke(args)

    # Mock the get_llm_agent dependency function
    def mock_get_llm_agent():
        return MockAgent()

    # Aggregation anwer must not contain any sensor rows IDs.
    class MockSensorDataDAL:
        def get_sensor_rows_by_ids(self, sensor_ids):
            pytest.fail(
                "get_sensor_rows_by_ids should not be called in this aggregation test"
            )

    def mock_get_sensor_data_dal():
        return MockSensorDataDAL()

    # Use FastAPI's dependency override mechanism
    app.dependency_overrides[get_llm_agent] = mock_get_llm_agent
    app.dependency_overrides[get_sensor_data_dal] = mock_get_sensor_data_dal

    try:
        response = client.get(
            "/api/v1/sensors/ask", params={"q": "What is the average temperature?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "llm_highlights" in data
        assert data["llm_highlights"] == "The average temperature is 23.93 degrees."
        assert "aggregation" in data
        assert data["aggregation"] == "23.93"
        assert "followup_question" in data
        assert data["followup_question"] == "What is the maximum temperature recorded?"
    finally:
        # Clean up the dependency override
        app.dependency_overrides.clear()
