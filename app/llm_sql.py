"""Module to manage Langchain SQL Agent for querying the sensor data database."""

from typing import List, Optional, Type
from string import Template
from langchain.agents import AgentExecutor
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent,  SQLDatabaseToolkit
from langchain_community.tools.sql_database.tool import ListSQLDatabaseTool
from pydantic import SecretStr, BaseModel, Field
from app.database import get_engine
from .config import get_settings

def get_llm_agent():
    """Get the LLM SQL agent instance for DI."""
    return load_sql_agent()

class _ListSQLDatabaseToolInput(BaseModel):
    tool_input: str = Field("", description="An empty string")

class CustomListSQLDatabaseTool(ListSQLDatabaseTool):
    """
    A custom version of ListSQLDatabaseTool that always returns 'sensor_data' as the only table.
    Should be a table view instead of a table.
    """
    name: str = "handmade_table_list"
    description: str = "List of only necessary sensory tables."
    args_schema: Type[BaseModel] = _ListSQLDatabaseToolInput

    def _run(self, *args, **kwargs):
        return "sensor_data"

class CustomSQLDatabaseToolkit(SQLDatabaseToolkit):
    def get_tools(self):
        # Get parent's tools, but skip the base ListSQLDatabaseTool
        default_tools = super().get_tools()
        filtered_tools = [tool for tool in default_tools if not isinstance(tool, ListSQLDatabaseTool)]
        # Insert your custom tool at the beginning
        return [CustomListSQLDatabaseTool(db=self.db)] + filtered_tools

class AskResponseFormater(BaseModel):
    """Always use this tool to structure your response to the user.
    When the result contains multiple values, use the 'id_list' field to return the list of all row IDs from the result.
    When the result is a single aggregation value, use 'scalar' field to return the result. 
    If there is no result to return, return an empty string in the answer field.
    Otherwise, if there is any result to return, must fill in either the 'id_list' or 'scalar' field, but not both.
    """
    answer: str = Field(description="The short answer to the user's question.")
    followup_question: str = Field(description="A followup question the user could ask.")
    id_list: Optional[List[str]] = Field(
        default=None,
        description="The array of row IDs.",
        title="Id List",
    )
    scalar: Optional[str] = Field(
        default=None,
        description="The scalar result.",
    )

parser = PydanticOutputParser(pydantic_object=AskResponseFormater)
def parse_response(output: str) -> AskResponseFormater:
    """
    Get the typed AskResponseFormater from LLM reponse.
    """
    result = parser.parse(output)
    print(f"LLM parsed response: {result}")
    return result

def get_prompt() -> Template:
    """
    Create the prompt template for the SQL agent.
    Expected variable: 'userquestion'
    """
    # Define the prompt with format instructions
    format_instructions = parser.get_format_instructions()
    print(f"LLM format instructions: {format_instructions}")
    return Template(
    'You are an expert Postgres TimescaleDB SQL assistant. ' \
    'Limits the result to 1000 rows. ' \
    'Use the following format instructions to structure your response: ' \
    f'{format_instructions}. ' \
    'Question: ${userquestion}')

def get_manual_prompt() -> Template:
    """
    Create the prompt template for the SQL agent.
    Expected variable: 'userquestion'
    """
    # Define the prompt with format instructions
    format_instructions = parser.get_format_instructions()
    print(f"LLM format instructions: {format_instructions}")
    return Template(
    'You are an expert Postgres TimescaleDB SQL assistant. ' \
    'This is the table structure you can query: ' \
    'CREATE TABLE sensor_data (id UUID NOT NULL, timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, sensor_id VARCHAR NOT NULL, metric varchar NOT NULL, value DOUBLE PRECISION NOT NULL ' \
    '"metric" is an enumerated type with possible values: temperature, humidity, pressure, speed, level, ambient, frequency, ticks, binary. ' \
    'The "id" column is the primary key. ' \
    'Limits the result to 1000 rows. ' \
    'Use the following format instructions to structure your response: ' \
    f'{format_instructions}. ' \
    'Question: ${userquestion}')

def load_sql_database() -> SQLDatabase:
    """
    Load the SQL tables to LLM context.
    """
    engine = get_engine()
    return SQLDatabase(engine=engine)


def load_llm() -> ChatOpenAI:
    """ Load the OpenAI model using the key and model_id specified in config."""

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
    toolkit = CustomSQLDatabaseToolkit(db=db, llm=llm)
    # Override database discovery tool with custom version.
    # set extra tool functions the agent can use
    #    [output_plot, output_table]
    extra_tools = []
    sql_agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        max_iterations=10,
        max_execution_time=45,
        extra_tools=extra_tools,
        verbose=True,
    )
    return sql_agent
