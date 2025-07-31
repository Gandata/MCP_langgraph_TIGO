# MCP-Langgraph para B2Bot

Este proyecto consiste en la creación de un agente conversacional para el área B2B (y nómina), donde su función principal será responder preguntas acerca de la base de documentos de la empresa utilizando tecnologías de recuperación aumentada por generación (RAG).

## Descripción General

Este proyecto implementa un agente conversacional inteligente que:

- Utiliza Google Gemini 2.0 Flash como modelo base (vía Google AI Studio)
- Integra con múltiples servidores MCP para diferentes funcionalidades
- Usa Langgraph para orquestar el flujo de conversación
- Implementa Qdrant como base de datos vectorial para almacenar y buscar documentos
- Proporciona una interfaz de streaming para respuestas en tiempo real
- Permite cargar documentos automáticamente desde la carpeta `data/`
- Ofrece búsqueda semántica en la base de conocimientos

## Prerrequisitos

- Python 3.13+
- Node.js (para servidores MCP externos)
- UV package manager
- Google AI Studio API key
- Qdrant (opcional, si se usa servidor externo)

## Instalación

1. Clona el repositorio:

```bash
git clone <repository-url>
cd MCP_LANGGRAPH_TIGO
```

2. Crea y activa el entorno virtual:

```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate
```

3. Instala las dependencias usando uv:

```bash
uv pip install -e .
```

4. Crea las variables de entorno:
   Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```
GOOGLE_API_KEY=tu_llave_api_googleai
```

## Servidores MCP

Este proyecto integra varios servidores MCP para diferentes funcionalidades:

1. **Servidor Dataflow**: Implementación personalizada para carga y consulta de datos
2. **Servidor Weather**: Proporciona información meteorológica actual
3. **Servidor Qdrant**: Base de datos vectorial para almacenamiento y búsqueda de documentos
4. **Servidor Filesystem**: Utiliza `@modelcontextprotocol/server-filesystem` para operaciones de archivos

## Uso

1. Inicia la aplicación (entorno gráfico de streamlit):

```bash
python run_streamlit.py
```

Interactúa con B2Bot:

**Conversación normal:**

```
USER: ¿Qué información tienes sobre RAG?
USER: Explícame cómo funciona el fine-tuning según los documentos
```

3. B2Bot utilizará sus herramientas para:

- Buscar en la base de conocimientos vectorial
- Procesar y analizar documentos
- Proporcionar respuestas contextuales basadas en los documentos de la empresa
- Realizar consultas meteorológicas cuando sea necesario

4. Escribe 'quit' o 'exit' para terminar la sesión.

## Cómo Funciona

### Arquitectura del Sistema

1. **`graph.py`** - Define la estructura del agente Langgraph:

   - Configura el prompt del sistema y el estado del agente
   - Configura el LLM (Google Gemini 2.0 Flash)
   - Define el flujo del grafo de conversación

2. **`client.py`** - Cliente principal:

   - Inicializa el cliente MCP con múltiples servidores
   - Maneja respuestas en streaming
   - Gestiona la sesión interactiva
   - Implementa funciones para cargar y buscar documentos en Qdrant

3. **Servidores MCP** - Proporcionan herramientas para:
   - Operaciones del sistema de archivos
   - Manipulación de datos
   - Búsqueda vectorial en Qdrant
   - Consultas meteorológicas
   - Procesamiento de documentos

### Flujo de Trabajo RAG

1. **Indexación**: Los documentos de la carpeta `data/` se procesan y almacenan en Qdrant
2. **Consulta**: Las preguntas del usuario se convierten en embeddings
3. **Recuperación**: Se buscan documentos similares en la base vectorial
4. **Generación**: El LLM genera respuestas basadas en el contexto recuperado

## Características Principales

- **RAG (Retrieval-Augmented Generation)**: Combina búsqueda vectorial con generación de texto
- **Streaming**: Respuestas en tiempo real con indicadores de herramientas
- **Multi-servidor MCP**: Integración con múltiples servidores para diferentes funcionalidades
- **Base de conocimientos**: Indexación automática de documentos empresariales
- **Interfaz conversacional**: Chat intuitivo con comandos especiales

## Comentarios Adicionales

Este proyecto fue modificado y adaptado del tutorial de kenneth-liao sobre agentes MCP para crear un sistema RAG especializado en el área B2B de la empresa.

### Próximas Mejoras

- Migración a Mistral-7B con vLLM para mayor control local
- Expansión de tipos de documentos soportados
- Implementación de métricas de relevancia

### Comentarios adicionales

Este proyecto está basado en el tutorial de kenneth-liao de mcp-intro
