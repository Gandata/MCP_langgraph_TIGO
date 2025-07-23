"""
This file implements the MCP Client for our Langgraph Agent.

MCP Clients are responsible for connecting and communicating with MCP servers. 
This client is analagous to Cursor or Claude Desktop and you would configure them in the 
same way by specifying the MCP server configuration in my_mcp/mcp_config.json.
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessageChunk
from typing import AsyncGenerator
from scout.my_mcp.config import mcp_config
from scout.graph import build_agent_graph, AgentState
import os
import asyncio
from pathlib import Path


async def stream_graph_response(
        input: AgentState, graph: StateGraph, config: dict = {}
        ) -> AsyncGenerator[str, None]:
    """
    Stream the response from the graph while parsing out tool calls.

    Args:
        input: The input for the graph.
        graph: The graph to run.
        config: The config to pass to the graph. Required for memory.

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


async def upload_documents_to_qdrant(graph: StateGraph, data_folder: str = "data", collection_name: str = "knowledge_base"):
    """
    Upload all documents from the data folder to Qdrant vector database.
    
    Args:
        graph: The graph instance with MCP tools
        data_folder: Path to the folder containing documents to upload
        collection_name: Name of the Qdrant collection to store documents
    """
    data_path = Path(data_folder)
    if not data_path.exists():
        print(f"Data folder '{data_folder}' does not exist.")
        return
    
    # Supported file extensions
    supported_extensions = {'.txt', '.md', '.py', '.json', '.csv', '.html', '.xml', '.docx', '.pdf'}
    
    files_to_process = []
    for file_path in data_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            files_to_process.append(file_path)
    
    if not files_to_process:
        print(f"No supported documents found in '{data_folder}' folder.")
        print(f"Supported extensions: {', '.join(supported_extensions)}")
        return
    
    print(f"Found {len(files_to_process)} documents to upload to Qdrant...")
    
    for file_path in files_to_process:
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print(f"Skipping empty file: {file_path}")
                continue
            
            # Create a message asking the assistant to store the document
            metadata_str = f"filename: {file_path.name}, filepath: {str(file_path)}, extension: {file_path.suffix}"
            prompt = f"Please store this document in the Qdrant vector database with collection name '{collection_name}'. Document content: {content}\n\nMetadata: {metadata_str}"
            
            # Use the graph to process the request
            response = await graph.ainvoke(
                AgentState(messages=[HumanMessage(content=prompt)]),
                config={"configurable": {"thread_id": "document_upload"}}
            )
            
            print(f"✓ Processed: {file_path.name}")
            
        except Exception as e:
            print(f"✗ Failed to process {file_path.name}: {str(e)}")
    
    print(f"Document upload process completed!")


async def search_documents_in_qdrant(graph: StateGraph, query: str, collection_name: str = "knowledge_base"):
    """
    Search for relevant documents in Qdrant based on a query.
    
    Args:
        graph: The graph instance with MCP tools
        query: The search query
        collection_name: Name of the Qdrant collection to search
        
    Returns:
        Search results from Qdrant
    """
    try:
        # Create a message asking the assistant to search documents
        prompt = f"Please search the Qdrant vector database in collection '{collection_name}' for information related to: {query}"
        
        # Use the graph to process the search request
        response = await graph.ainvoke(
            AgentState(messages=[HumanMessage(content=prompt)]),
            config={"configurable": {"thread_id": "document_search"}}
        )
        
        return response
        
    except Exception as e:
        print(f"Error searching documents: {str(e)}")
        return None


async def main():
    """
    Initialize the MCP client and run the agent conversation loop.

    The MultiServerMCPClient allows connection to multiple MCP servers using a single client and config.
    """
    # Create the client without using it as a context manager
    client = MultiServerMCPClient(
        connections=mcp_config
    )
    
    # Get tools using the new async method
    tools = await client.get_tools()
    graph = build_agent_graph(tools=tools)

    # pass a config with a thread_id to use memory
    graph_config = {
        "configurable": {
            "thread_id": "1"
        }
    }

    print("MCP Agent with Qdrant Vector Database")
    print("=" * 50)
    print("Available commands:")
    print("  /upload     - Upload documents from data folder to Qdrant")
    print("  /search     - Search documents in Qdrant")
    print("  /help       - Show this help message")
    print("  quit/exit   - Exit the program")
    print("  Or just type your question to chat with the assistant")
    print("=" * 50)

    while True:
        user_input = input("\nUSER: ").strip()
        
        if user_input.lower() in ["quit", "exit"]:
            break
        elif user_input == "/help":
            print("\n Help:")
            print("  /upload     - Upload all documents from the 'data' folder to Qdrant vector database")
            print("  /search     - Search for information in the uploaded documents")
            print("  quit/exit   - Exit the program")
            print("  Or type any question to chat with the AI assistant")
            continue
        elif user_input == "/upload":
            print("\n Uploading documents to Qdrant...")
            await upload_documents_to_qdrant(graph, data_folder="data", collection_name="knowledge_base")
            continue
        elif user_input.startswith("/search "):
            query = user_input[8:].strip()  # Remove "/search " prefix
            if query:
                print(f"\n Searching for: {query}")
                print("\n ---- SEARCH RESULTS ----\n")
                
                async for response in stream_graph_response(
                    input = AgentState(messages=[HumanMessage(content=f"Search the Qdrant vector database in collection 'knowledge_base' for information related to: {query}")]),
                    graph = graph, 
                    config = {"configurable": {"thread_id": "search"}}
                ):
                    print(response, end="", flush=True)
                print("\n")
            else:
                print("Please provide a search query. Example: /search python functions")
            continue
        elif user_input == "/search":
            print("Please provide a search query. Example: /search python functions")
            continue
        elif user_input.startswith("/"):
            print("Unknown command. Type /help for available commands.")
            continue

        print(f"\n ----  USER  ---- \n\n {user_input}")
        print("\n ----  ASSISTANT  ---- \n\n")

        async for response in stream_graph_response(
            input = AgentState(messages=[HumanMessage(content=user_input)]),
            graph = graph, 
            config = graph_config
            ):
            print(response, end="", flush=True)

if __name__ == "__main__":
    import asyncio
    # only needed if running in an ipykernel
    import nest_asyncio
    nest_asyncio.apply()

    asyncio.run(main())