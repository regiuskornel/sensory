
# Sensory 

A simple data management for environmental sensors. Storing the recorded data and makes that available
via a simple REST API and native language query endpoints.

API defined in endpoints.py. The current implementation requires OpenAI platform API access.
Main frameworks:

* FastAPI for serving HTTP API 
* SQLAlchemy for database access
* LangChain NLP to SQL tooling


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

Application requires Postgres with Timescale extension. It run in Docker.
Docker pull and start Postgres with database 'timescaledb' creation.
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

### Run the app

```bash
pip install -r requirements.txt

fastapi dev app/main.py
```

### API documentation and test

http://localhost:8000/docs

