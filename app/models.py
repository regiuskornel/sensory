"""
Database models for sensor data.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Enum as SAEnum,  text, DateTime, String, Float
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class MetricEnum(str, Enum):
    """
    Enum for supported sensor metric types.
    """

    TEMPERATURE = "temperature"  #: Sensor measures temperature. Any scale.
    HUMIDITY = "humidity"  #: Sensor measures humidity. 0-100%
    PRESSURE = "pressure"  #: Sensor measures pressure. Any scale.
    SPEED = "speed"  #: Sensor measures speed, velocity, wind speed. Below the speed of light.
    AMBIENT = "ambient"  #: Sensor measures ambient conditions like brightness.
    LEVEL = "level"  #: Sensor measures level. E.g. water level.
    FREQUENCY = "frequency"  #: Sensor measures frequency (ticks per second).
    TICKS = "ticks"  #: Sensor measures number of ticks, pulses, events.
    BINARY = "binary"  #: Sensor measures binary state, e.g. open/closed, on/off represented as 1.0/0.0.


class SensorData(Base):
    """
    SQLAlchemy ORM model for sensor data records.
    Each record represents a single measurement from a sensor at a specific time.
    Same sensor can have multiple metrics at the same time(stamp).
    """

    __tablename__ = "sensor_data"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
    )  # Unique row ID
    timestamp = Column(
        DateTime, primary_key=True, index=True, default=datetime.now
    )  # When the measurement was taken.
    sensor_id = Column(
        String, index=True
    )  # Sensor unique ID, sensor name or serial number.
    metric = Column(SAEnum(MetricEnum), index=True)  # Type of metric being recorded.
    value = Column(
        Float
    )  # The recorded value. The interpretation depends on the metric type.
