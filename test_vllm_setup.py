import os
from openai import OpenAI

# VLLM_API_ENDPOINT = os.getenv("VLLM_API_ENDPOINT")
# VLLM_API_EMBED = os.getenv("VLLM_API_EMBED")
# VLLM_MODEL_NAME = os.getenv("VLLM_MODEL_NAME") # Default if not set
# EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")


VLLM_API_ENDPOINT="http://192.168.1.10:8002"

# vLLM embeddings endpoint (if using a separate embedding service)
VLLM_API_EMBED="http://192.168.1.10:8003/embed"

# Model name served by vLLM
VLLM_MODEL_NAME="Mistral-7B-Instruct-Raft-Wifi"

# Embedding model name (if using separate embedding service)
VLLM_EMBED_MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"

print(VLLM_API_ENDPOINT)
# --- Initialize OpenAI client for vLLM ---
vllm_client = OpenAI(
    base_url=VLLM_API_ENDPOINT + "/v1",
    #api_key="dummy_key_vllm_doesnt_need_auth_by_default" # vLLM doesn't require an API key by default
    api_key="not-needed" # vLLM doesn't require an API key by default
)

# Test inference
response = vllm_client.chat.completions.create(
    model=VLLM_MODEL_NAME,
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.choices[0].message.content)