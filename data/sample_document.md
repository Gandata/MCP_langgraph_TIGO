# Sample Document for Vector Search

## Introduction
This is a sample document to demonstrate the Qdrant vector database integration with the MCP agent.

## Features
- **Vector Search**: The system can store and retrieve documents using semantic search
- **Multiple File Types**: Supports various file formats including markdown, text, and code files
- **Metadata Storage**: Each document is stored with relevant metadata like filename and file size

## Google Gemini Integration
The project uses Google Gemini 2.0 Flash model instead of OpenAI GPT models. This provides:
- Cost-effective AI processing
- Advanced reasoning capabilities
- Multimodal support for future enhancements

## MCP (Model Context Protocol) Servers
The system integrates with multiple MCP servers:
- **Dataflow Server**: Handles data processing and analysis
- **Qdrant Server**: Manages vector database operations
- **Git Server**: Provides version control functionality

## Usage Instructions
1. Place documents in the `data` folder
2. Use `/upload` command to index documents in Qdrant
3. Use `/search <query>` to find relevant information
4. Chat normally with the AI assistant

## Technical Details
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Database**: Qdrant Cloud
- **Collection**: knowledge_base
- **AI Model**: Google Gemini 2.0 Flash
