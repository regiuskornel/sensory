"""Test module for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import schemas
from datetime import datetime
from app.api.endpoints import get_llm_agent

client = TestClient(app)


def test_create_sensor_data(monkeypatch):
    """Test sensor data creation endpoint."""

    def mock_create_sensor_data(session, data):
        return schemas.SensorDataOut(
            id="acff4f6d-6e51-4b20-be91-35571be93e0a",
            sensor_id="sensor1",
            metric=schemas.MetricEnum.TEMPERATURE,
            value=25.5,
            timestamp=datetime(2025, 1, 1),
        )

    monkeypatch.setattr("app.dal.create_sensor_data", mock_create_sensor_data)
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


def test_list_sensor_data(monkeypatch):
    """Test sensor data listing endpoint."""

    def mock_list_sensor_data(session, sensor_ids, metrics, date_from, date_to):
        return [
            schemas.SensorDataOut(
                id="acff4f6d-6e51-4b20-be91-35571be93e0a",
                sensor_id="sensor1",
                metric=schemas.MetricEnum.TEMPERATURE,
                value=25.5,
                timestamp=datetime(2025, 1, 1),
            )
        ]

    monkeypatch.setattr("app.dal.list_sensor_data", mock_list_sensor_data)

    response = client.get("/api/v1/sensors/list", params={"sensor_id": "sensor1"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "acff4f6d-6e51-4b20-be91-35571be93e0a"
    assert data[0]["sensor_id"] == "sensor1"
    assert data[0]["metric"] == "temperature"
    assert data[0]["value"] == 25.5
    assert data[0]["timestamp"] == "2025-01-01T00:00:00"


def test_batch_get_sensor_data(monkeypatch):
    """Test batch sensor data retrieval endpoint."""

    def mock_get_sensor_rows_by_ids(session, sensor_ids):
        return [
            schemas.SensorDataOut(
                id="acff4f6d-6e51-4b20-be91-35571be93e0a",
                sensor_id="sensor1",
                metric=schemas.MetricEnum.TEMPERATURE,
                value=25.5,
                timestamp=datetime(2025, 1, 1),
            ),
            schemas.SensorDataOut(
                id="abcdabcd-6e51-4b20-be91-35571be93e0a",
                sensor_id="sensor1",
                metric=schemas.MetricEnum.HUMIDITY,
                value=29.5,
                timestamp=datetime(2025, 1, 1),
            )
        ]

    monkeypatch.setattr("app.dal.get_sensor_rows_by_ids", mock_get_sensor_rows_by_ids)
    payload = {"sensor_ids": ["sensor1"]}

    response = client.post("/api/v1/sensors/batch_get", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["sensor_id"] == "sensor1"


def test_ask_sensor_data(monkeypatch):
    """Test natural language query endpoint w/o actual LLM API call."""

    def mock_invoke(args):
        return {"output" : "{\"answer\":\"The average temperature is 23.93 degrees.\",\"followup_question\":\"What is the maximum temperature recorded?\",\"id_list\":null,\"aggregation\":\"23.93\"}"}
    
   
    def mock_get_sensor_rows_by_ids(session, id_list):
        pytest.fail("should be not called in this test")
        return []
    monkeypatch.setattr("app.dal.get_sensor_rows_by_ids", mock_get_sensor_rows_by_ids)

    class MockAgent:
        def invoke(self, args):
            return mock_invoke(args)
    
    # Use FastAPI's dependency override mechanism
    # Mock the get_llm_agent dependency function
    def mock_get_llm_agent():
        return MockAgent()
    app.dependency_overrides[get_llm_agent] = mock_get_llm_agent
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

