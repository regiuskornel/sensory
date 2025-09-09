"""
API schemas using Pydantic models.
"""
from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict

class MetricEnum(str, Enum):
    """Enumeration of supported sensor metric types."""
    temperature = "temperature" # Sensor measures temperature. Any scale.
    humidity = "humidity" # Sensor measures humidity. 0-100%
    pressure = "pressure" # Sensor measures pressure. Any scale.
    speed = "speed" # Sensor measures speed, velocity, wind speed. Beloww the speed of light.
    ambient = "ambient" # Sensor measures ambient conditions like brightness.
    level = "level" # Sensor measures level. E.g. water level.
    frequency = "frequency" # Sensor measures frequency (ticks per second).
    ticks = "ticks" # Sensor measures number of ticks, pulses, events.

class SensorDataIn(BaseModel):
    """Input schema for creating a new sensor data record."""
    sensor_id: str
    metric: MetricEnum
    value: float
    timestamp: datetime # When the measurement was taken. It used insted of insertion time.

class SensorDataOut(BaseModel):
    """Output schema for returning sensor data records."""
    id: str
    sensor_id: str
    metric: MetricEnum
    value: float
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class BatchGetRequest(BaseModel):
    """Request schema for batch retrieval of sensor data by sensor IDs."""
    sensor_ids: List[str]

class AskRequest(BaseModel):
    """Request schema for natural language questions about sensor data."""
    question: str

class AskResponse(BaseModel):
    """Response schema for LLM-based sensor data queries, including LLM response summary, row list, and aggregations."""
    llm_highlights: str
    sensors: Optional[List[SensorDataOut]] = None # The list of sensor data records returned by the LLM->SQL query, if any.
    aggregation: Optional[str] = None # Native language output, textual aggregation result returned by the LLM->SQL query, if any.
