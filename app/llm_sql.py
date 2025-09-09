"""Module to manage Langchain SQL Agent for querying the sensor data database."""

import os
from typing import List, Optional
from string import Template
from langchain.agents import AgentExecutor
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent,  SQLDatabaseToolkit
from pydantic import SecretStr, BaseModel, Field
from app.database import get_engine
from .config import get_settings

class AskResponseFormater(BaseModel):
    """Always use this tool to structure your response to the user. When the result would be multiple values, use the id_list field to return the list of row IDs. 
    When the result is a single aggregation value, use the aggregation field to return the result. 
    If there is no result to return, return an empty string in the answer field."""
    answer: str = Field(description="The answer to the user's question")
    followup_question: str = Field(description="A followup question the user could ask")
    id_list: Optional[List[str]] = Field(
        default=None,
        description="The list of row IDs returned by the LLM->SQL query. Only include this field if there is a list of IDs to return.",
    )
    aggregation: Optional[str] = Field(
        default=None,
        description="The aggregation result returned by the LLM->SQL query. Only include this field if there is an aggregation to return.",
    )

parser = PydanticOutputParser(pydantic_object=AskResponseFormater)
def parse_response(output: str) -> AskResponseFormater:
    """
    Get the typed AskResponseFormater from LLM reponse.
    """
    return parser.parse(output)

def get_prompt() -> Template:
    """
    Create the prompt template for the SQL agent.
    Expected variable: 'userquestion'
    """
    # Define the prompt with format instructions
    format_instructions = parser.get_format_instructions()
    return Template(
    'You are an expert Postgres TimescaleDB SQL assistant. ' \
    'Limits the result to 1000 rows. ' \
    'Use the following format instructions to structure your response. ' \
    f'{format_instructions}'
    'Question: ${userquestion}')

def load_sql_database() -> SQLDatabase:
    """
    Load the SQL tables to LLM context.
    """
    engine = get_engine()
    return SQLDatabase(engine=engine)


def load_llm() -> ChatOpenAI:
    """ 
    Load the OpenAI model using the key and model_id specified in config.
    """

    openai_api_key : SecretStr = SecretStr(get_settings().openai_api_key)
    if openai_api_key.get_secret_value() == "Invalid":
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # load OpenAI model
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=openai_api_key)

def load_sql_agent() -> AgentExecutor:
    """
    Create the Langchain SQL AgentExecutor Hands over the optional tool functions to
    the AgentExecutor.
    """

    llm = load_llm()
    db = load_sql_database()
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    # set extra tool functions the agent can use
    # extra_tools = [[AskResponseFormater]]
    #    [output_plot, output_time_series_plot, output_table]
    extra_tools = []
    # model_with_tools = model.bind_tools([AskResponseFormater], llm=load_llm())
    # create SQL agent
    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        max_iterations=10,
        max_execution_time=45,
        extra_tools=extra_tools,
        verbose=True,
    )
