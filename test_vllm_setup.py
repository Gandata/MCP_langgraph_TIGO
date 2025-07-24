#!/usr/bin/env python3
"""
Quick start script for vLLM setup validation and testing.
This script helps validate your vLLM configuration and test the connection.
"""

import os
import sys
import asyncio
import httpx
from scout.vllm_config import get_vllm_config, print_vllm_config, validate_vllm_config

async def test_vllm_connection():
    """Test connection to vLLM server."""
    config = get_vllm_config()
    
    print("Testing vLLM Connection...")
    print_vllm_config()
    
    # Test models endpoint
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config['api_base_url']}/v1/models")
            if response.status_code == 200:
                models = response.json()
                print("✓ Successfully connected to vLLM server!")
                print(f"Available models: {len(models.get('data', []))}")
                
                # Print available models
                for model in models.get('data', []):
                    print(f"  - {model.get('id', 'Unknown')}")
                    
                return True
            else:
                print(f"✗ Error connecting to vLLM: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Failed to connect to vLLM server: {e}")
        print("Make sure vLLM is running at the configured endpoint.")
        return False

async def test_simple_completion():
    """Test a simple completion request."""
    config = get_vllm_config()
    
    print("\nTesting simple completion...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config['api_base_url']}/v1/chat/completions",
                json={
                    "model": config["model_name"],
                    "messages": [
                        {"role": "user", "content": "Hello! Can you hear me?"}
                    ],
                    "max_tokens": 50,
                    "temperature": 0.1
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print("✓ Simple completion test successful!")
                print(f"Response: {content}")
                return True
            else:
                print(f"✗ Completion test failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"✗ Completion test failed: {e}")
        return False

def check_environment():
    """Check if environment is properly configured."""
    print("Checking environment configuration...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✓ .env file found")
    else:
        print("⚠ .env file not found. Using default configuration.")
        print("Consider copying .env.example to .env and customizing it.")
    
    # Validate vLLM config
    if validate_vllm_config():
        print("✓ vLLM configuration looks good")
    else:
        print("⚠ vLLM configuration may need attention")
    
    # Check required directories
    if os.path.exists('data'):
        print("✓ data directory exists")
    else:
        print("⚠ data directory not found. Creating it...")
        os.makedirs('data', exist_ok=True)

async def main():
    """Main function to run all tests."""
    print("vLLM Configuration and Connection Test")
    print("=" * 50)
    
    # Check environment
    check_environment()
    print()
    
    # Test connection
    connection_ok = await test_vllm_connection()
    print()
    
    if connection_ok:
        # Test completion
        completion_ok = await test_simple_completion()
        print()
        
        if completion_ok:
            print("🎉 All tests passed! Your vLLM setup is ready.")
            print("You can now run: python -m scout.client")
        else:
            print("❌ Completion test failed. Check your vLLM server configuration.")
    else:
        print("❌ Connection test failed. Please check your vLLM server.")
        print("\nTo start vLLM server, run:")
        print("vllm serve meta-llama/Llama-3-8B-Instruct --host 0.0.0.0 --port 8002")

if __name__ == "__main__":
    asyncio.run(main())
