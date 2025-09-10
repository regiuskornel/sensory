"""API endpoints for managing and querying sensor data."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import dal, schemas, models
from app.database import get_db_session
from app.llm_sql import load_sql_agent, get_prompt, parse_response

router = APIRouter()

def get_llm_agent():
    """Get the LLM SQL agent instance."""
    return load_sql_agent()


@router.post("/sensors/data", response_model=schemas.SensorDataOut)
def create_sensor_data(
    data: schemas.SensorDataIn, session: Session = Depends(get_db_session)
):
    """
    Creates a new sensor data record in the database.

    Args:
        data (schemas.SensorDataIn): The input data for the sensor, validated by the SensorDataIn schema.
        session (Session, optional): The database session dependency.

    Returns:
        The created sensor data record.
    """

    # Input validation
    if not data.sensor_id or not data.sensor_id.strip():
        raise HTTPException(status_code=400, detail="sensor_id is required and cannot be empty")
    
    if data.value is None:
        raise HTTPException(status_code=400, detail="value is required")
    
    if not isinstance(data.value, (int, float)):
        raise HTTPException(status_code=400, detail="value must be a number")
    
    if data.metric not in schemas.MetricEnum:
        raise HTTPException(status_code=400, detail=f"metric must be one of: {list(schemas.MetricEnum)}")
    
    sensor_data = models.SensorData(
        sensor_id=data.sensor_id,
        metric=data.metric,
        value=data.value,
        timestamp=data.timestamp
    )
    return dal.create_sensor_data(session, sensor_data)


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
    rows = dal.list_sensor_data(session, sensor_ids, metrics, date_from, date_to)
    return list(schemas.SensorDataOut.model_validate(r) for r in rows)


@router.post("/sensors/batch_get", response_model=List[schemas.SensorDataOut])
def batch_get_sensor_data(
    request: schemas.BatchGetRequest, session: Session = Depends(get_db_session)
):
    """
    Retrieve sensor data for a batch of sensor IDs (strings).

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
def ask_sensor_data(
    q: str, 
    session: Session = Depends(get_db_session),
    llm_agent = Depends(get_llm_agent)
):
    """
    Handles natural language queries about sensor data using an LangChain.

    This endpoint receives a user question, generates a prompt for the LLM, 
    processes the LLM's response, and returns structured sensor data or aggregation results.
    It supports both direct data retrieval and aggregation queries, 
    mapping LLM output to API response schemas.

    Args:
        q (str): The user's natural language question about sensor data.
        session (Session): Database session dependency.
        llm_agent: The LLM SQL agent dependency.

    Returns:
        schemas.AskResponse: Structured response containing highlights, sensor data, or aggregation results.

    Raises:
        HTTPException: For LLM invocation errors, response parsing errors, or schema conversion errors.
    """
    # Input validation
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required and cannot be empty")
    
    if len(q.strip()) > 1000:  # Reasonable limit for query length
        raise HTTPException(status_code=400, detail="Query length cannot exceed 1000 characters")
    
    try:
        prompt_with_format = get_prompt().substitute(userquestion=q)
        answer = llm_agent.invoke({"input": prompt_with_format})["output"]
    except BaseException as e:
        print(f"Error invoking LLM: {e}")
        raise HTTPException(status_code=500, detail="LLM invocation error") from e

    try:
        parsed = parse_response(answer)
    except BaseException as e:
        print(f"Error parsing LLM structured response: {e}")
        raise HTTPException(
            status_code=500, detail="Invalid JSON response from LLM"
        ) from e

    try:
        response = schemas.AskResponse(
            llm_highlights=parsed.answer, 
            followup_question=parsed.followup_question)
        if (
            parsed.id_list
        ):  # LLM returned a list of row IDs, so the reponsone more likely a select result w/o aggregation.
            rows = dal.get_sensor_rows_by_ids(session, parsed.id_list)
            # Convert DB result to Pydantic models using attibute mapping.
            response.sensors = list(
                schemas.SensorDataOut.model_validate(r) for r in rows
            )
        elif (
            parsed.aggregation
        ):  # LLM returned an aggregation result, so user intention more likely an aggregation query.
            response.aggregation = parsed.aggregation
        else:
            raise HTTPException(
                status_code=404,
                detail="Unable to determine query result from LLM response",
            )
        return response
    except BaseException as e:
        raise HTTPException(
            status_code=500, detail="LLM to API schema conversion error"
        ) from e
