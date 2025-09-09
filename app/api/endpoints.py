"""API endpoints for managing and querying sensor data."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import dal, schemas
from app.database import get_db_session
from app.llm_sql import load_sql_agent, get_prompt, parse_response

router = APIRouter()
llmsql = load_sql_agent()

@router.post("/sensors/data", response_model=schemas.SensorDataOut)
def create_sensor_data(data: schemas.SensorDataIn, session: Session = Depends(get_db_session)):
    """
    Creates a new sensor data record in the database.

    Args:
        data (schemas.SensorDataIn): The input data for the sensor, validated by the SensorDataIn schema.
        session (Session, optional): The database session dependency.

    Returns:
        The created sensor data record.
    """
    return dal.create_sensor_data(session, data)


@router.get("/sensors/list", response_model=List[schemas.SensorDataOut])
def list_sensor_data(
    sensor_ids: Optional[List[str]] = Query(default=None, alias="sensor_id"),
    metrics: Optional[List[schemas.MetricEnum]] = Query(default=None, alias="metric"),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    session: Session = Depends(get_db_session),
):
    """
    Retrieve sensor data filtered by sensor IDs, metrics, and date range.

    Args:
        sensor_ids (Optional[List[str]]): List of sensor IDs to filter the data. Query parameter alias: "sensor_id".
        metrics (Optional[List[schemas.MetricEnum]]): List of metric types to filter the data. Query parameter alias: "metric".
        date_from (Optional[str]): Start date (inclusive) for filtering data in ISO format.
        date_to (Optional[str]): End date (inclusive) for filtering data in ISO format.
        session (Session): Database session dependency.

    Returns:
        List: A list of sensor data records matching the provided filters.
    """
    return dal.list_sensor_data(session, sensor_ids, metrics, date_from, date_to)

@router.post("/sensors/batch_get", response_model=List[schemas.SensorDataOut])
def batch_get_sensor_data(
    request: schemas.BatchGetRequest, session: Session = Depends(get_db_session)
):
    """
    Retrieve sensor data for a batch of sensor IDs.

    Args:
        request (schemas.BatchGetRequest): The request object containing a list of sensor IDs.
        session (Session, optional): The database session dependency.

    Raises:
        HTTPException: If the sensor_ids list in the request is empty.

    Returns:
        List[schemas.SensorData]: A list of sensor data objects corresponding to the provided sensor IDs.
    """
    if not request.sensor_ids:
        raise HTTPException(status_code=400, detail="sensor_ids list must not be empty")
    return dal.get_sensor_rows_by_ids(session, request.sensor_ids)

@router.get("/sensors/ask", response_model=schemas.AskResponse)
def ask_sensor_data(q: str, session: Session = Depends(get_db_session)):
    """
    Handles natural language queries about sensor data using an LangChain.

    This endpoint receives a user question, generates a prompt for the LLM, processes the LLM's response,
    and returns structured sensor data or aggregation results. It supports both direct data retrieval and
    aggregation queries, mapping LLM output to API response schemas.

    Args:
        q (str): The user's natural language question about sensor data.
        session (Session): Database session dependency.

    Returns:
        schemas.AskResponse: Structured response containing highlights, sensor data, or aggregation results.

    Raises:
        HTTPException: For LLM invocation errors, response parsing errors, or schema conversion errors.
    """
    try:
        prompt_with_format = get_prompt().substitute(userquestion=q)
        answer = llmsql.invoke({"input": prompt_with_format})["output"]
    except BaseException as e:
        print(f"Error invoking LLM: {e}")
        raise HTTPException(status_code=500, detail="LLM invocation error") from e

    try:
        parsed = parse_response(answer)
    except BaseException as e:
        print(f"Error parsing LLM structured response: {e}")
        raise HTTPException(status_code=500, detail="Invalid JSON response from LLM") from e

    try:
        response = schemas.AskResponse(llm_highlights=parsed.answer)
        if parsed.id_list: # LLM returned a list of row IDs, so the reponsone more likely a select result w/o aggregation.
            rows = dal.get_sensor_rows_by_ids(session, parsed.id_list)
            # Convert DB result to Pydantic models using attibute mapping.
            response.sensors = list(schemas.SensorDataOut.model_validate(r) for r in rows)
        elif parsed.aggregation: # LLM returned an aggregation result, so user intention more likely an aggregation query.
            response.aggregation = parsed.aggregation
        else:
            raise HTTPException(status_code=404, detail="Unable to determine query result from LLM response")
        return response
    except BaseException as e:
        raise HTTPException(status_code=500, detail="LLM to API schema conversion error") from e

