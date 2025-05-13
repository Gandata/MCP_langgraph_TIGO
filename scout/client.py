"""
This file implements the client for our Langgraph Agent.

Clients are responsible for interacting directly with MCP servers. This client is analagous to Cursor or 
Claude Desktop and you would configure them in the same way as we're doing in my_mcp/mcp_config.json.
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessageChunk
from typing import AsyncGenerator
from my_mcp.config import mcp_config
from scout.graph import build_agent_graph, AgentState


async def stream_response(
        input: AgentState, graph: StateGraph, config: dict = {}
        ) -> AsyncGenerator[str, None]:
    """
    Stream the response from the graph while parsing out tool calls.

    Args:
        input: The input to the graph.
        graph: The graph to run.
        config: The config to pass to the graph.

    Yields:
        A processed string from the graph's chunked response.
    """
    async for message_chunk, metadata in graph.astream(
        input=input,
        stream_mode="messages",
        config=config
        ):
        if isinstance(message_chunk, AIMessageChunk):
            if message_chunk.response_metadata:
                finish_reason = message_chunk.response_metadata.get("finish_reason", "")
                if finish_reason == "tool_calls":
                    yield "\n\n"

            if message_chunk.tool_call_chunks:
                tool_chunk = message_chunk.tool_call_chunks[0]

                tool_name = tool_chunk.get("name", "")
                args = tool_chunk.get("args", "")

                
                if tool_name:
                    tool_call_str = f"\n\n< TOOL CALL: {tool_name} >\n\n"

                if args:
                    tool_call_str = args
                yield tool_call_str
            else:
                yield message_chunk.content
            continue


async def main():
    async with MultiServerMCPClient(
        connections=mcp_config
    ) as client:
        graph = build_agent_graph(tools=client.get_tools())

        # pass a config with a thread_id to use memory
        graph_config = {
            "configurable": {
                "thread_id": "1"
            }
        }

        while True:
            user_input = input("\n\nUSER: ")
            if user_input in ["quit", "exit"]:
                break

            print("\n ----  USER  ---- \n\n", user_input)
            print("\n ----  ASSISTANT  ---- \n\n")

            async for response in stream_response(
                input = AgentState(messages=[HumanMessage(content=user_input)]),
                graph = graph, 
                config = graph_config
                ):
                print(response, end="", flush=True)

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()

    asyncio.run(main())