import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import schemas
from datetime import datetime, timedelta

client = TestClient(app)

def test_create_sensor_data(monkeypatch):
    # Mock DAL
    def mock_create_sensor_data(session, data):
        return schemas.SensorDataOut(
            id="sensor1-temperature-2023-01-01T00:00:00",
            sensor_id="sensor1",
            metric=schemas.MetricEnum.temperature,
            value=25.5,
            timestamp=datetime(2023, 1, 1)
        )
    monkeypatch.setattr("app.dal.create_sensor_data", mock_create_sensor_data)
    payload = {
        "sensor_id": "sensor1",
        "metric": "temperature",
        "value": 25.5,
        "timestamp": "2023-01-01T00:00:00"
    }
    response = client.post("/api/v1/sensors/data", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == "sensor1"
    assert data["metric"] == "temperature"
    assert data["value"] == 25.5

def test_list_sensor_data(monkeypatch):
    def mock_list_sensor_data(session, sensor_ids, metrics, date_from, date_to):
        return [
            schemas.SensorDataOut(
                id="sensor1-temperature-2023-01-01T00:00:00",
                sensor_id="sensor1",
                metric=schemas.MetricEnum.temperature,
                value=25.5,
                timestamp=datetime(2023, 1, 1)
            )
        ]
    monkeypatch.setattr("app.dal.list_sensor_data", mock_list_sensor_data)
    response = client.get("/api/v1/sensors/list", params={"sensor_id": "sensor1"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["sensor_id"] == "sensor1"

def test_batch_get_sensor_data(monkeypatch):
    def mock_get_sensor_rows_by_ids(session, sensor_ids):
        return [
            schemas.SensorDataOut(
                id="sensor1-temperature-2023-01-01T00:00:00",
                sensor_id="sensor1",
                metric=schemas.MetricEnum.temperature,
                value=25.5,
                timestamp=datetime(2023, 1, 1)
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
    class MockParsed:
        answer = "The average temperature is 25.5."
        id_list = ["sensor1-temperature-2023-01-01T00:00:00"]
        aggregation = None
    def mock_get_prompt():
        class Dummy:
            def substitute(self, userquestion):
                return userquestion
        return Dummy()
    def mock_invoke(args):
        return {"output": "mocked output"}
    def mock_parse_response(answer):
        return MockParsed()
    def mock_get_sensor_rows_by_ids(session, id_list):
        return [
            schemas.SensorDataOut(
                id="sensor1-temperature-2023-01-01T00:00:00",
                sensor_id="sensor1",
                metric=schemas.MetricEnum.temperature,
                value=25.5,
                timestamp=datetime(2023, 1, 1)
            )
        ]
    monkeypatch.setattr("app.llm_sql.get_prompt", mock_get_prompt)
    monkeypatch.setattr("app.llm_sql.load_sql_agent", lambda: type("Dummy", (), {"invoke": staticmethod(mock_invoke)})())
    monkeypatch.setattr("app.llm_sql.parse_response", mock_parse_response)
    monkeypatch.setattr("app.dal.get_sensor_rows_by_ids", mock_get_sensor_rows_by_ids)
    response = client.get("/api/v1/sensors/ask", params={"q": "What is the average temperature?"})
    assert response.status_code == 200
    data = response.json()
    assert "llm_highlights" in data
    assert data["llm_highlights"] == "The average temperature is 25.5."
    assert "sensors" in data
    assert isinstance(data["sensors"], list)
