"""API schemas using Pydantic models"""

from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class MetricEnum(str, Enum):
    """Enumeration of supported sensor metric types."""

    TEMPERATURE = "temperature"  # Sensor measures temperature. Any scale.
    HUMIDITY = "humidity"  # Sensor measures humidity. 0-100%
    PRESSURE = "pressure"  # Sensor measures pressure. Any scale.
    SPEED = "speed"  # Sensor measures speed, velocity, wind speed. Beloww the speed of light.
    AMBIENT = "ambient"  # Sensor measures ambient conditions like brightness.
    LEVEL = "level"  # Sensor measures level. E.g. water level.
    FREQUENCY = "frequency"  # Sensor measures frequency (ticks per second).
    TICKS = "ticks"  # Sensor measures number of ticks, pulses, events.
    BINARY = "binary"  #: Sensor measures binary state, e.g. open/closed, on/off represented as 1.0/0.0.

class SensorDataIn(BaseModel):
    """Input schema for creating a new sensor data record."""

    sensor_id: str = Field(title="Sensor ID", min_length=1, max_length=300)
    metric: MetricEnum = Field(title="Metric category")
    value: float = Field(title="Measured value")
    timestamp: Optional[datetime] = Field(title="Timestamp of the measurement", default_factory=datetime.utcnow)
    model_config = ConfigDict(from_attributes=True)


class SensorDataOut(BaseModel):
    """Output schema for returning sensor data records."""

    id: str = Field(title="Unique record ID (UUID4 as string)")
    sensor_id: str = Field(title="Sensor ID")
    metric: MetricEnum = Field(title="Metric category")
    value: float = Field(title="Measured value")
    timestamp: datetime = Field(title="Timestamp of the measurement")
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, sensor_data) -> "SensorDataOut":
        """ Convert a models.SensorData object to SensorDataOut schema instance """
        return cls.model_validate({
            "id": str(sensor_data.id),
            "sensor_id": sensor_data.sensor_id,
            "metric": sensor_data.metric,
            "value": sensor_data.value,
            "timestamp": sensor_data.timestamp
        })

    @classmethod
    def from_models(cls, sensor_data_list) -> List["SensorDataOut"]:
        """ Convert a list of models.SensorData objects to a list of SensorDataOut schema instances """
        return [cls.from_model(sensor_data) for sensor_data in sensor_data_list]


class BatchGetRequest(BaseModel):
    """Request schema for batch retrieval of sensor data by sensor IDs."""

    sensor_ids: List[str] = Field(title="List of sensor IDs to retrieve data for", min_length=1, max_length=1000)


class AskRequest(BaseModel):
    """Request schema for natural language questions about sensor data."""

    question: str = Field(title="Question about sensor records", min_length=5, max_length=1000)


class AskResponse(BaseModel):
    """Response schema for LLM-based sensor data queries, including LLM response summary,
    row list, and aggregations."""

    llm_highlights: str = Field(
        title="LLM-generated summary of the answer to the question based on sensor data"
    )
    sensors: Optional[List[SensorDataOut]] = Field(
        default=None,
        title="List of sensor data records returned by the LLM->SQL query, if any."
    )
    aggregation: Optional[str] = Field(
        default=None,
        title="Native language output, textual aggregation result returned by the LLM->SQL query, if any."
    )
    followup_question: Optional[str] = Field(
        default=None,
        title="A followup question the user could ask, if any."
    )
