import pandas as pd
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool
from typing import Optional
import duckdb
from pydantic import BaseModel

# Initialize FastMCP server
mcp = FastMCP("dataflow")

class DataFlowSession:
    def __init__(self):
        self.data: Optional[pd.DataFrame]  = None

    async def load_data(self, file_path: str) -> str:
        try:
            self.data = pd.read_csv(file_path)
            return f"Data loaded from {file_path}"
        except Exception as e:
            return f"Error loading data: {str(e)}"
    
    async def query_data(self, query: str) -> str:
        if self.data is None:
            return "No data loaded."
        
        try:
            con = duckdb.connect(database=':memory:')
            con.register('data', self.data)
            result = con.execute(query).fetchdf()
            return result.to_string()
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
session = DataFlowSession()


class LoadDataInput(BaseModel):
    file_path: str

class QueryDataInput(BaseModel):
    query: str

@mcp.tool()
async def load_data(file_path: str) -> str:
    return await session.load_data(file_path)


@mcp.tool()
async def query_data(query: str) -> str:
    return await session.query_data(query)


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="load_data",
            description="Load data from a file.",
            inputSchema=LoadDataInput
        ),
        Tool(
            name="query_data",
            description="Query the loaded data.",
            inputSchema=QueryDataInput
        )
    ]

if __name__ == "__main__":
    mcp.run(transport='stdio')