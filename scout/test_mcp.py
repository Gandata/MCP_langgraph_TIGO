#!/usr/bin/env python3
"""
Test script to verify MCP configuration works with MultiServerMCPClient
"""

import asyncio
import json
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_config():
    """Test the MCP configuration"""
    
    # Load the simple config first
    config_file = Path(__file__).parent / "my_mcp" / "mcp_config_simple.json"
    
    with open(config_file, "r") as f:
        config = json.load(f)
    
    # Extract the mcpServers dictionary for MultiServerMCPClient
    mcp_config = config["mcpServers"]
    
    print("Testing MCP Configuration...")
    print(f"Config: {mcp_config}")
    
    try:
        # Create the client
        client = MultiServerMCPClient(connections=mcp_config)
        
        # Get tools
        print("Getting tools...")
        tools = await client.get_tools()
        
        print(f"Successfully loaded {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
            
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_mcp_config())
