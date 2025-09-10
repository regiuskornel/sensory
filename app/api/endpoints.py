"""API endpoints for managing and querying sensor data."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app import schemas, models
from app.dal import SensorDataDAL, get_sensor_data_dal
from app.llm_sql import get_prompt, parse_response, get_llm_agent

router = APIRouter()


@router.post("/sensors/data", response_model=schemas.SensorDataOut)
def create_sensor_data(
    data: schemas.SensorDataIn, dal: SensorDataDAL = Depends(get_sensor_data_dal)
):
    """
    Creates a new sensor data record in the database.

    Args:
        data (schemas.SensorDataIn): The input data for the sensor, validated by the SensorDataIn schema.
        dal (SensorDataDAL): The data access layer dependency.

    Returns:
        The created sensor data record.
    """

    sensor_data = models.SensorData(
        sensor_id=data.sensor_id,
        metric=data.metric,
        value=data.value,
        timestamp=data.timestamp,
    )
    return schemas.SensorDataOut.from_model(dal.create_sensor_data(sensor_data))


@router.get("/sensors/list", response_model=List[schemas.SensorDataOut])
def list_sensor_data(
    sensor_ids: Optional[List[str]] = Query(default=None, alias="sensor_id"),
    metrics: Optional[List[schemas.MetricEnum]] = Query(default=None, alias="metric"),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    dal: SensorDataDAL = Depends(get_sensor_data_dal),
):
    """
    Retrieve sensor data filtered by sensor IDs, metrics, and date range.

    Args:
        sensor_ids (Optional[List[str]]): List of sensor IDs to filter the data. Query parameter alias: "sensor_id".
        metrics (Optional[List[schemas.MetricEnum]]): List of metric types to filter the data. Query parameter alias: "metric".
        date_from (Optional[str]): Start date (inclusive) for filtering data in ISO format.
        date_to (Optional[str]): End date (inclusive) for filtering data in ISO format.
        dal (SensorDataDAL): The data access layer dependency.

    Returns:
        List: A list of sensor data records matching the provided filters.
    """
    # Convert metrics enum to string values if provided
    metric_strings = [metric.value for metric in metrics] if metrics else None

    rows = dal.list_sensor_data(sensor_ids, metric_strings, date_from, date_to)
    return schemas.SensorDataOut.from_models(rows)


@router.post("/sensors/batch_get", response_model=List[schemas.SensorDataOut])
def batch_get_sensor_data(
    request: schemas.BatchGetRequest, dal: SensorDataDAL = Depends(get_sensor_data_dal)
):
    """
    Retrieve sensor data for a batch of sensor IDs (strings).

    Args:
        request (schemas.BatchGetRequest): The request object containing a list of sensor IDs.
        dal (SensorDataDAL): The data access layer dependency.

    Raises:
        HTTPException: If the sensor_ids list in the request is empty or contains invalid values.

    Returns:
        List[schemas.SensorDataOut]: A list of sensor data objects corresponding to the provided sensor IDs.
    """
    # Input validation
    if not request.sensor_ids:
        raise HTTPException(status_code=400, detail="sensor_ids list must not be empty")

    # Pagination not implemented so smtg protection needed.
    if len(request.sensor_ids) > 1000:  # Reasonable limit to prevent server overload
        raise HTTPException(
            status_code=400, detail="sensor_ids list cannot exceed 1000 items"
        )

    # Validate each sensor_id
    for sensor_id in request.sensor_ids:
        if not sensor_id or not sensor_id.strip():
            raise HTTPException(
                status_code=400, detail="All sensor_ids must be non-empty strings"
            )

    rows = dal.get_sensor_rows_by_ids(request.sensor_ids)
    return schemas.SensorDataOut.from_models(rows)


@router.get("/sensors/ask", response_model=schemas.AskResponse)
def ask_sensor_data(
    q: str,
    dal: SensorDataDAL = Depends(get_sensor_data_dal),
    llm_agent=Depends(get_llm_agent),
):
    """
    Handles natural language queries about sensor data using an LangChain.

    This endpoint receives a user question, generates a prompt for the LLM,
    processes the LLM's response, and returns structured sensor data or aggregation results.

    Args:
        q (str): The user's natural language question about sensor data.
        dal (SensorDataDAL): The data access layer dependency.
        llm_agent: The LLM SQL agent dependency.

    Returns:
        schemas.AskResponse: Structured response containing highlights, sensor list, or aggregation results.

    Raises:
        HTTPException: For LLM invocation errors, response parsing errors, or schema conversion errors.
    """
    # Input validation, since no input model is used here.
    if not q or not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Query parameter 'q' is required and cannot be empty",
        )

    if len(q.strip()) > 1000:  # Reasonable limit for query length
        raise HTTPException(
            status_code=400, detail="Query length cannot exceed 1000 characters"
        )

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
            llm_highlights=parsed.answer, followup_question=parsed.followup_question
        )
        if (
            parsed.id_list
        ):  # LLM returned a list of row IDs, so the reponsone more likely a select result w/o aggregation.
            rows = dal.get_sensor_rows_by_ids(parsed.id_list)
            # Convert DB result to Pydantic models using from_models method.
            response.sensors = schemas.SensorDataOut.from_models(rows)
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
