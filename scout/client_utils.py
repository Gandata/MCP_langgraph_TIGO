from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, add_messages, START, END
from langchain_core.messages import HumanMessage, AIMessageChunk
from typing import AsyncGenerator
from my_mcp.config import mcp_config
import asyncio

async def print_tools():
    async with MultiServerMCPClient(
            connections=mcp_config
        ) as client:
        print(f"Connected to MCP servers: {list(client.connections.keys())}")

        for server_name, server_tools in client.server_name_to_tools.items():
            print(f"\n--------------------")
            print(f"\n {server_name} tools:\n")
            for tool in server_tools:
                print(tool.name + "\n" + tool.description, end='\n\n', flush=True)

def main():
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(print_tools())

if __name__ == "__main__":
    main()