"""
Database connection and session management for PostgreSQL with TimescaleDB extension.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

engine = create_engine(get_settings().timescale_db_connection, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_engine():
    """
    Returns the SQLAlchemy engine connected to the database.

    Returns:
        Engine: The SQLAlchemy engine instance.
    """
    return engine

def get_db_session():
    """
    Yields a database session that is automatically closed after use.

    This generator function creates a new SQLAlchemy session using SessionLocal,
    yields it for use in database operations, and ensures that the session is
    properly closed after the operation is complete, even if an exception occurs.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_postgres() -> None:
    """
    Initialize the PostgreSQL connection and create the hypertable.
    """
    # Sensor Data Table
    init_sql = """
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
 
    SELECT create_hypertable('sensor_data', 'timestamp', if_not_exists => TRUE);

    -- Clean up any existing data for a fresh start
    TRUNCATE TABLE sensor_data;

    -- Set default UUID for ID field if not already set. SQL Alchemy standard solution
    -- does not use the Postgres side column default when inserting via ORM. 
    -- Defining server side default in the model is make SQLite inmemory testing approach too complicated.
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'sensor_data' 
            AND column_name = 'id' 
            AND column_default IS NOT NULL
        ) THEN
            ALTER TABLE sensor_data ALTER COLUMN id SET DEFAULT uuid_generate_v4();
        END IF;
    END $$;

    -- Sample Data
    INSERT INTO sensor_data (timestamp, sensor_id, metric, value) VALUES
    ('2025-09-08T08:00:00+00:00', 'sensor_1', 'temperature', 20.0),
    ('2025-09-08T08:01:00+00:00', 'sensor_1', 'temperature', 20.32),
    ('2025-09-08T08:02:00+00:00', 'sensor_1', 'temperature', 20.63),
    ('2025-09-08T08:03:00+00:00', 'sensor_1', 'temperature', 20.95),
    ('2025-09-08T08:04:00+00:00', 'sensor_1', 'temperature', 21.27),
    ('2025-09-08T08:05:00+00:00', 'sensor_1', 'temperature', 21.58),
    ('2025-09-08T08:06:00+00:00', 'sensor_1', 'temperature', 21.89),
    ('2025-09-08T08:07:00+00:00', 'sensor_1', 'temperature', 22.19),
    ('2025-09-08T08:08:00+00:00', 'sensor_1', 'temperature', 22.49),
    ('2025-09-08T08:09:00+00:00', 'sensor_1', 'temperature', 22.79),
    ('2025-09-08T08:10:00+00:00', 'sensor_1', 'temperature', 23.07),
    ('2025-09-08T08:11:00+00:00', 'sensor_1', 'temperature', 23.35),
    ('2025-09-08T08:12:00+00:00', 'sensor_1', 'temperature', 23.63),
    ('2025-09-08T08:13:00+00:00', 'sensor_1', 'temperature', 23.89),
    ('2025-09-08T08:14:00+00:00', 'sensor_1', 'temperature', 24.15),
    ('2025-09-08T08:15:00+00:00', 'sensor_1', 'temperature', 24.39),
    ('2025-09-08T08:16:00+00:00', 'sensor_1', 'temperature', 24.62),
    ('2025-09-08T08:17:00+00:00', 'sensor_1', 'temperature', 24.85),
    ('2025-09-08T08:18:00+00:00', 'sensor_1', 'temperature', 25.06),
    ('2025-09-08T08:19:00+00:00', 'sensor_1', 'temperature', 25.25),
    ('2025-09-08T08:20:00+00:00', 'sensor_1', 'temperature', 25.43),
    ('2025-09-08T08:21:00+00:00', 'sensor_1', 'temperature', 25.59),
    ('2025-09-08T08:22:00+00:00', 'sensor_1', 'temperature', 25.74),
    ('2025-09-08T08:23:00+00:00', 'sensor_1', 'temperature', 25.87),
    ('2025-09-08T08:24:00+00:00', 'sensor_1', 'temperature', 25.99),
    ('2025-09-08T08:25:00+00:00', 'sensor_1', 'temperature', 26.08),
    ('2025-09-08T08:26:00+00:00', 'sensor_1', 'temperature', 26.16),
    ('2025-09-08T08:27:00+00:00', 'sensor_1', 'temperature', 26.22),
    ('2025-09-08T08:28:00+00:00', 'sensor_1', 'temperature', 26.26),
    ('2025-09-08T08:29:00+00:00', 'sensor_1', 'temperature', 26.28),
    ('2025-09-08T08:30:00+00:00', 'sensor_1', 'temperature', 26.28),
    ('2025-09-08T08:31:00+00:00', 'sensor_1', 'temperature', 26.26),
    ('2025-09-08T08:32:00+00:00', 'sensor_1', 'temperature', 26.22),
    ('2025-09-08T08:33:00+00:00', 'sensor_1', 'temperature', 26.16),
    ('2025-09-08T08:34:00+00:00', 'sensor_1', 'temperature', 26.08),
    ('2025-09-08T08:35:00+00:00', 'sensor_1', 'temperature', 25.99),
    ('2025-09-08T08:36:00+00:00', 'sensor_1', 'temperature', 25.87),
    ('2025-09-08T08:37:00+00:00', 'sensor_1', 'temperature', 25.74),
    ('2025-09-08T08:38:00+00:00', 'sensor_1', 'temperature', 25.59),
    ('2025-09-08T08:39:00+00:00', 'sensor_1', 'temperature', 25.43),
    ('2025-09-08T08:40:00+00:00', 'sensor_1', 'temperature', 25.25),
    ('2025-09-08T08:41:00+00:00', 'sensor_1', 'temperature', 25.06),
    ('2025-09-08T08:42:00+00:00', 'sensor_1', 'temperature', 24.85),
    ('2025-09-08T08:43:00+00:00', 'sensor_1', 'temperature', 24.62),
    ('2025-09-08T08:44:00+00:00', 'sensor_1', 'temperature', 24.39),
    ('2025-09-08T08:45:00+00:00', 'sensor_1', 'temperature', 24.15),
    ('2025-09-08T08:46:00+00:00', 'sensor_1', 'temperature', 23.89),
    ('2025-09-08T08:47:00+00:00', 'sensor_1', 'temperature', 23.63),
    ('2025-09-08T08:48:00+00:00', 'sensor_1', 'temperature', 23.35),
    ('2025-09-08T08:49:00+00:00', 'sensor_1', 'temperature', 23.07),
    ('2025-09-08T08:50:00+00:00', 'sensor_1', 'temperature', 22.79),
    ('2025-09-08T08:51:00+00:00', 'sensor_1', 'temperature', 22.49),
    ('2025-09-08T08:52:00+00:00', 'sensor_1', 'temperature', 22.19),
    ('2025-09-08T08:53:00+00:00', 'sensor_1', 'temperature', 21.89),
    ('2025-09-08T08:54:00+00:00', 'sensor_1', 'temperature', 21.58),
    ('2025-09-08T08:55:00+00:00', 'sensor_1', 'temperature', 21.27),
    ('2025-09-08T08:56:00+00:00', 'sensor_1', 'temperature', 20.95),
    ('2025-09-08T08:57:00+00:00', 'sensor_1', 'temperature', 20.63),
    ('2025-09-08T08:58:00+00:00', 'sensor_1', 'temperature', 20.32),

    ('2025-09-08T08:00:00+00:00', 'sensor_1', 'humidity', 40.0),
    ('2025-09-08T08:01:00+00:00', 'sensor_1', 'humidity', 40.32),
    ('2025-09-08T08:02:00+00:00', 'sensor_1', 'humidity', 40.63),
    ('2025-09-08T08:03:00+00:00', 'sensor_1', 'humidity', 40.95),
    ('2025-09-08T08:04:00+00:00', 'sensor_1', 'humidity', 41.27),
    ('2025-09-08T08:05:00+00:00', 'sensor_1', 'humidity', 41.58),
    ('2025-09-08T08:06:00+00:00', 'sensor_1', 'humidity', 41.89),
    ('2025-09-08T08:07:00+00:00', 'sensor_1', 'humidity', 42.19),
    ('2025-09-08T08:08:00+00:00', 'sensor_1', 'humidity', 42.49),
    ('2025-09-08T08:09:00+00:00', 'sensor_1', 'humidity', 42.79),
    ('2025-09-08T08:10:00+00:00', 'sensor_1', 'humidity', 43.07),
    ('2025-09-08T08:11:00+00:00', 'sensor_1', 'humidity', 43.35),
    ('2025-09-08T08:12:00+00:00', 'sensor_1', 'humidity', 43.63),
    ('2025-09-08T08:13:00+00:00', 'sensor_1', 'humidity', 43.89),
    ('2025-09-08T08:14:00+00:00', 'sensor_1', 'humidity', 44.15),
    ('2025-09-08T08:15:00+00:00', 'sensor_1', 'humidity', 44.39),
    ('2025-09-08T08:16:00+00:00', 'sensor_1', 'humidity', 44.62),
    ('2025-09-08T08:17:00+00:00', 'sensor_1', 'humidity', 44.85),
    ('2025-09-08T08:18:00+00:00', 'sensor_1', 'humidity', 45.06),
    ('2025-09-08T08:19:00+00:00', 'sensor_1', 'humidity', 45.25),
    ('2025-09-08T08:20:00+00:00', 'sensor_1', 'humidity', 45.43),
    ('2025-09-08T08:21:00+00:00', 'sensor_1', 'humidity', 45.59),
    ('2025-09-08T08:22:00+00:00', 'sensor_1', 'humidity', 45.74),
    ('2025-09-08T08:23:00+00:00', 'sensor_1', 'humidity', 45.87),
    ('2025-09-08T08:24:00+00:00', 'sensor_1', 'humidity', 45.99),
    ('2025-09-08T08:25:00+00:00', 'sensor_1', 'humidity', 46.08),
    ('2025-09-08T08:26:00+00:00', 'sensor_1', 'humidity', 46.16),
    ('2025-09-08T08:27:00+00:00', 'sensor_1', 'humidity', 46.22),
    ('2025-09-08T08:28:00+00:00', 'sensor_1', 'humidity', 46.26),
    ('2025-09-08T08:29:00+00:00', 'sensor_1', 'humidity', 46.28),
    ('2025-09-08T08:30:00+00:00', 'sensor_1', 'humidity', 46.28),
    ('2025-09-08T08:31:00+00:00', 'sensor_1', 'humidity', 46.26),
    ('2025-09-08T08:32:00+00:00', 'sensor_1', 'humidity', 46.22),
    ('2025-09-08T08:33:00+00:00', 'sensor_1', 'humidity', 46.16),
    ('2025-09-08T08:34:00+00:00', 'sensor_1', 'humidity', 46.08),
    ('2025-09-08T08:35:00+00:00', 'sensor_1', 'humidity', 45.99),
    ('2025-09-08T08:36:00+00:00', 'sensor_1', 'humidity', 45.87),
    ('2025-09-08T08:37:00+00:00', 'sensor_1', 'humidity', 45.74),
    ('2025-09-08T08:38:00+00:00', 'sensor_1', 'humidity', 45.59),
    ('2025-09-08T08:39:00+00:00', 'sensor_1', 'humidity', 45.43),
    ('2025-09-08T08:40:00+00:00', 'sensor_1', 'humidity', 45.25),
    ('2025-09-08T08:41:00+00:00', 'sensor_1', 'humidity', 45.06),
    ('2025-09-08T08:42:00+00:00', 'sensor_1', 'humidity', 44.85),
    ('2025-09-08T08:43:00+00:00', 'sensor_1', 'humidity', 44.62),
    ('2025-09-08T08:44:00+00:00', 'sensor_1', 'humidity', 44.39),
    ('2025-09-08T08:45:00+00:00', 'sensor_1', 'humidity', 44.15),
    ('2025-09-08T08:46:00+00:00', 'sensor_1', 'humidity', 43.89),
    ('2025-09-08T08:47:00+00:00', 'sensor_1', 'humidity', 43.63),
    ('2025-09-08T08:48:00+00:00', 'sensor_1', 'humidity', 43.35),
    ('2025-09-08T08:49:00+00:00', 'sensor_1', 'humidity', 43.07),
    ('2025-09-08T08:50:00+00:00', 'sensor_1', 'humidity', 42.79),
    ('2025-09-08T08:51:00+00:00', 'sensor_1', 'humidity', 42.49),
    ('2025-09-08T08:52:00+00:00', 'sensor_1', 'humidity', 42.19),
    ('2025-09-08T08:53:00+00:00', 'sensor_1', 'humidity', 41.89),
    ('2025-09-08T08:54:00+00:00', 'sensor_1', 'humidity', 41.58),
    ('2025-09-08T08:55:00+00:00', 'sensor_1', 'humidity', 41.27),
    ('2025-09-08T08:56:00+00:00', 'sensor_1', 'humidity', 40.95),
    ('2025-09-08T08:57:00+00:00', 'sensor_1', 'humidity', 40.63),
    ('2025-09-08T08:58:00+00:00', 'sensor_1', 'humidity', 40.32);
    
    -- Random other sensors, metrics, and values
    INSERT INTO sensor_data (timestamp, sensor_id, metric, value) VALUES
    ('2025-09-08T08:05:00+00:00', 'sensor_2', 'humidity', 55.2),
    ('2025-09-08T08:15:00+00:00', 'sensor_3', 'pressure', 1013.1),
    ('2025-09-08T08:25:00+00:00', 'sensor_3', 'humidity', 52.8),
    ('2025-09-08T08:35:00+00:00', 'sensor_1', 'pressure', 1012.6),
    ('2025-09-08T08:45:00+00:00', 'sensor_4', 'humidity', 53.6),
    ('2025-09-08T08:55:00+00:00', 'sensor_4', 'pressure', 1013.8);
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Upgrade to hypertables and insert sample data (for MVP demo).
    try:
        with engine.connect() as conn:
            conn.execute(text(init_sql))
            conn.commit()
        print("PostgreSQL with timescales has been initialized.")
    except Exception as e:
        print(f"Error occured when running query : {e}")
        print(init_sql)
        raise
