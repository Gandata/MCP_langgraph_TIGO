# MCP LangGraph TIGO with vLLM Integration

This project is a Model Context Protocol (MCP) agent that uses LangGraph for orchestration and vLLM as the backend language model provider. It includes integration with Qdrant vector database for document storage and retrieval.

## Prerequisites

### 1. vLLM Server Setup

You need to have vLLM running on your network. Here's how to set it up:

#### Install vLLM

```bash
pip install vllm
```

#### Start vLLM Server for Chat Completions

```bash
# Example with Llama-3-8B-Instruct
vllm serve meta-llama/Llama-3-8B-Instruct \
  --host 0.0.0.0 \
  --port 8002 \
  --api-key EMPTY
```

#### Optional: Start vLLM Server for Embeddings (if needed)

```bash
# Example with a sentence transformer model
vllm serve sentence-transformers/all-MiniLM-L6-v2 \
  --host 0.0.0.0 \
  --port 8003 \
  --task embed \
  --api-key EMPTY
```

### 2. Qdrant Vector Database

Install and run Qdrant:

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or install locally
pip install qdrant-client
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd MCP_langgraph_TIGO
```

2. Install dependencies:

```bash
pip install -e .
```

3. Set up environment variables:

```bash
cp .env.example .env
```

Edit the `.env` file with your vLLM server details:

```env
VLLM_API_ENDPOINT=http://192.168.1.10:8002
VLLM_MODEL_NAME=meta-llama/Llama-3-8B-Instruct
VLLM_TEMPERATURE=0.1
VLLM_MAX_TOKENS=8192
```

## Configuration

The project uses environment variables for configuration. Key settings:

- `VLLM_API_ENDPOINT`: Main vLLM server endpoint (default: http://192.168.1.10:8002)
- `VLLM_API_EMBED`: Embedding server endpoint (optional)
- `VLLM_MODEL_NAME`: Model name served by vLLM
- `VLLM_TEMPERATURE`: Model temperature (default: 0.1)
- `VLLM_MAX_TOKENS`: Maximum tokens to generate (default: 8192)

## Usage

### Run the MCP Client

```bash
python -m scout.client
```

### Available Commands

- `/upload` - Upload documents from the `data` folder to Qdrant
- `/search <query>` - Search documents in Qdrant
- `/config` - Show current vLLM configuration
- `/help` - Show help message
- `quit` or `exit` - Exit the program
- Type any question to chat with the AI assistant

### Document Upload

Place your documents in the `data/` folder. Supported formats:

- `.txt`, `.md`, `.py`, `.json`, `.csv`
- `.html`, `.xml`, `.docx`, `.pdf`

Use the `/upload` command to process and store them in Qdrant.

### Search and Chat

After uploading documents, you can:

1. Use `/search <query>` to find relevant documents
2. Ask questions naturally - the AI will use the uploaded documents as context

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │────│   LangGraph     │────│     vLLM        │
│   (scout)       │    │   Agent         │    │   (OpenAI API)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         └──────────────│   MCP Servers   │
                        │   (Tools)       │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │    Qdrant       │
                        │  Vector DB      │
                        └─────────────────┘
```

## Components

### 1. MCP Client (`scout/client.py`)

- Main interface for user interaction
- Handles document upload and search commands
- Streams responses from the LangGraph agent

### 2. LangGraph Agent (`scout/graph.py`)

- Orchestrates the conversation flow
- Integrates vLLM via OpenAI-compatible API
- Manages tool calling and state

### 3. vLLM Configuration (`scout/vllm_config.py`)

- Centralized configuration management
- Environment variable handling
- Validation and debugging utilities

### 4. MCP Tools

- Various tools available through MCP servers
- Configured in `scout/my_mcp/mcp_config.json`

## Troubleshooting

### vLLM Connection Issues

1. Check if vLLM server is running:

```bash
curl http://192.168.1.10:8002/v1/models
```

2. Verify the endpoint in your `.env` file

3. Check the `/config` command output in the client

### Model Loading Issues

1. Ensure you have enough GPU memory for your chosen model
2. Try a smaller model if needed:

```bash
vllm serve microsoft/DialoGPT-medium --port 8002
```

### Document Upload Issues

1. Check file permissions in the `data/` folder
2. Verify Qdrant is running on port 6333
3. Check the console output for specific error messages

## Development

### Adding New MCP Tools

1. Configure the tool in `scout/my_mcp/mcp_config.json`
2. The tool will be automatically available to the agent

### Customizing the Agent

Modify `scout/graph.py` to:

- Change system prompts
- Adjust model parameters
- Add custom logic to the conversation flow

### Testing

Run the existing task:

```bash
# From VS Code terminal or PowerShell
.venv\Scripts\activate
python -m scout.client
```

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your vLLM setup
5. Submit a pull request
