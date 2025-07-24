"""
vLLM Configuration Module

This module contains configuration settings for connecting to vLLM servers.
"""

import os
from typing import Dict, Any

# Default vLLM Configuration
VLLM_CONFIG = {
    "api_base_url": os.getenv("VLLM_API_ENDPOINT", "http://192.168.1.10:8002"),
    "api_embed_url": os.getenv("VLLM_API_EMBED", "http://192.168.1.10:8003/embed"),
    "api_key": "EMPTY",  # vLLM doesn't require API key for local deployments
    "model_name": os.getenv("VLLM_MODEL_NAME", "meta-llama/Llama-3-8B-Instruct"),  # Default model
    "embed_model_name": os.getenv("VLLM_EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
    "temperature": float(os.getenv("VLLM_TEMPERATURE", "0.1")),
    "max_tokens": int(os.getenv("VLLM_MAX_TOKENS", "8192")),
    "timeout": int(os.getenv("VLLM_TIMEOUT", "60")),
}

def get_vllm_config() -> Dict[str, Any]:
    """
    Get vLLM configuration settings.
    
    Returns:
        Dict containing vLLM configuration parameters
    """
    return VLLM_CONFIG.copy()

def validate_vllm_config() -> bool:
    """
    Validate that vLLM configuration is properly set.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    required_fields = ["api_base_url", "model_name"]
    
    for field in required_fields:
        if not VLLM_CONFIG.get(field):
            print(f"Warning: {field} is not configured in vLLM settings")
            return False
    
    return True

def print_vllm_config():
    """Print current vLLM configuration for debugging."""
    print("Current vLLM Configuration:")
    print("-" * 40)
    for key, value in VLLM_CONFIG.items():
        if "api_key" in key.lower():
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
    print("-" * 40)
