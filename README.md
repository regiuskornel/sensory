
# Sensory 


A simple data management for environmental sensors. Storing the recorded data and makes that available
via a simple REST API and native language query endpoints.

**Designed for an MVP demo. Not intended to be a production ready application.**

API defined in endpoints.py. The current implementation requires OpenAI platform API access.

Main frameworks:

* FastAPI for serving HTTP API 
* SQLAlchemy for database access
* LangChain NLP to SQL tooling

Application leverages Postgres Timescale DB extension for effective query over large time series dataset.

Code structure:

```bash
project_root/
├── app/
│   ├── __init__.py
│   ├── dal.py            # DB access logic
│   ├── database.py       # Database config & session management
│   ├── main.py           # FastAPI app entry point
│   ├── models.py         # SQLAlchemy ORM models
│   ├── llm_sql.py        # LangChain utility
│   ├── schemas.py        # Pydantic API schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py  # API route definitions
├── examples/             # Couple of recorded LLM queries and answers.
├── .env                  # Required applicaton configuration
├── requirements.txt
```

## Run the application

### Environment

Requires Python >=3.12

Application requires Postgres with Timescale extension. which should run in Docker.

Host and start Postgres with database 'timescaledb' creation in Docker.
'sensory_db' will be [created](https://hub.docker.com/_/postgres#environment-variables) 
automatically during the first startup.

```bash
sudo apt-get install -y postgresql-client
docker pull timescale/timescaledb:latest-pg17
docker run -v ~/psql:/pgdata -e PGDATA=/pgdatav \
  -d --name timescaledb -p 127.0.0.1:5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=sensory_db \
  timescale/timescaledb:latest-pg17 
```

Postgres CLI available by

```bash
docker exec -it timescaledb psql -U postgres
```

Copy  .env.template to .env file and fill out the environment variables (requires Open AI API key)

### Run the app

```bash
pip install -r requirements.txt

fastapi dev app/main.py
```

### API documentation and manual testing

http://localhost:8000/docs


## Known limitations and potential improvements.

* LLM latency is high (>20 seconds). Requires to LangChain fine tuning and prompt research. (Cache table structure, etc)
* LLM asked to return row IDs, then the application DAL layer retrieves the responsed full row values using ID list. This 2 phased approach ensures to retrieve rows that the actual user has acces and/or can be part of complex join (result enhancement). This not be used in this MVP application.
* Need to investigate which is more effective? 
   a) fine tune model class AskResponseFormater annotations and/or 
   b) enhance the prompt template get_prompt()
* Should be tested with large amount of sensor data.
* '/sensors/data' API endpoint is very naive at this phase. 
  * Accepts arbitrary sensor data w/o checking if it a registered sensor or not. (requires sensor registration API). 
  * Not protected from typical sensor overload. No throttle implemented. (After a power/network outage and restoration, typically all joined sensor start to send data in a short time period which maybe cause service overload.)
  * Missing sensor device authentication.
* Missing API user authz.
* Missing load and automatic E2E testing.
