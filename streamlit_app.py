"""
Aplicación de Streamlit para el chat con B2Bot.

Esta aplicación proporciona una interfaz web para interactuar con el agente B2Bot
con funcionalidades de:
- Chat en tiempo real con streaming
- Historial de herramientas utilizadas por el agente
- Carga de documentos a Qdrant
- Búsqueda en la base de conocimientos
"""

import streamlit as st
import asyncio
import nest_asyncio
from typing import AsyncGenerator, Dict, List, Any
from pathlib import Path
import datetime
import json

# Configurar nest_asyncio para permitir bucles asíncronos anidados en Streamlit
nest_asyncio.apply()

# Importar componentes del agente
from langchain_mcp_adapters.client import MultiServerMCPClient
from scout.my_mcp.config import mcp_config
from scout.graph import build_agent_graph, AgentState
from langchain_core.messages import HumanMessage, AIMessageChunk


# Configuración de la página
st.set_page_config(
    page_title="B2Bot - Asistente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .tool-history {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #1f77b4;
    }
    
    .tool-name {
        font-weight: bold;
        color: #1f77b4;
        font-size: 14px;
    }
    
    .tool-time {
        font-size: 12px;
        color: #666;
    }
    
    .tool-args {
        font-size: 12px;
        background-color: #e1e5fe;
        padding: 5px;
        border-radius: 5px;
        margin-top: 5px;
        font-family: monospace;
    }
    
    .chat-container {
        height: 600px;
        overflow-y: auto;
    }
    
    .status-indicator {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .status-processing {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-ready {
        background-color: #d4edda;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)


async def stream_graph_response_with_tools(
    entrada: AgentState, 
    grafo, 
    config: dict = {}
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Transmite la respuesta del grafo y captura información de herramientas utilizadas.
    
    Yields:
        Dict con 'type' (content|tool), 'data' (contenido o info de herramienta)
    """
    async for fragmento_mensaje, metadata in grafo.astream(
        input=entrada,
        stream_mode="messages",
        config=config
    ):
        if isinstance(fragmento_mensaje, AIMessageChunk):
            if fragmento_mensaje.response_metadata:
                motivo_finalizacion = fragmento_mensaje.response_metadata.get("finish_reason", "")
                if motivo_finalizacion == "tool_calls":
                    yield {"type": "content", "data": "\n\n"}

            if fragmento_mensaje.tool_call_chunks:
                fragmento_herramienta = fragmento_mensaje.tool_call_chunks[0]
                nombre_herramienta = fragmento_herramienta.get("name", "")
                argumentos = fragmento_herramienta.get("args", "")
                
                if nombre_herramienta:
                    # Registrar herramienta utilizada
                    tool_info = {
                        "name": nombre_herramienta,
                        "args": argumentos,
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                    }
                    yield {"type": "tool", "data": tool_info}
                    yield {"type": "content", "data": f"\n\n🔧 **Usando herramienta:** {nombre_herramienta}\n\n"}
                
                if argumentos:
                    yield {"type": "content", "data": argumentos}
            else:
                if fragmento_mensaje.content:
                    yield {"type": "content", "data": fragmento_mensaje.content}


@st.cache_resource
def initialize_agent():
    """Inicializa el agente MCP una sola vez usando cache."""
    async def _init():
        cliente = MultiServerMCPClient(connections=mcp_config)
        herramientas = await cliente.get_tools()
        grafo = build_agent_graph(tools=herramientas)
        return grafo
    
    return asyncio.run(_init())


def initialize_session_state():
    """Inicializa el estado de la sesión de Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "tool_history" not in st.session_state:
        st.session_state.tool_history = []
    
    if "agent_initialized" not in st.session_state:
        st.session_state.agent_initialized = False
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"streamlit_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"


def add_tool_to_history(tool_info: Dict[str, Any]):
    """Agrega una herramienta utilizada al historial."""
    st.session_state.tool_history.append(tool_info)
    # Mantener solo las últimas 50 herramientas
    if len(st.session_state.tool_history) > 50:
        st.session_state.tool_history = st.session_state.tool_history[-50:]


def display_tool_history():
    """Muestra el historial de herramientas en la barra lateral."""
    st.sidebar.header("🔧 Historial de Herramientas")
    
    if not st.session_state.tool_history:
        st.sidebar.info("No se han utilizado herramientas aún.")
        return
    
    # Mostrar las últimas 10 herramientas
    recent_tools = st.session_state.tool_history[-10:]
    
    for i, tool in enumerate(reversed(recent_tools)):
        with st.sidebar.expander(f"🔧 {tool['name']} - {tool['timestamp']}", expanded=False):
            st.write(f"**Herramienta:** {tool['name']}")
            st.write(f"**Hora:** {tool['timestamp']}")
            if tool['args']:
                st.write("**Argumentos:**")
                if isinstance(tool['args'], str):
                    st.code(tool['args'], language="json")
                else:
                    st.code(json.dumps(tool['args'], indent=2, ensure_ascii=False), language="json")
    
    # Botón para limpiar historial
    if st.sidebar.button("🗑️ Limpiar Historial", type="secondary"):
        st.session_state.tool_history = []
        st.rerun()


def display_chat_history():
    """Muestra el historial de chat."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def handle_special_commands(user_input: str, grafo) -> bool:
    """
    Maneja comandos especiales como /cargar y /buscar.
    
    Returns:
        True si se manejó un comando especial, False en caso contrario.
    """
    if user_input == "/cargar":
        with st.spinner("Cargando documentos a Qdrant..."):
            try:
                result = asyncio.run(cargar_documentos_a_qdrant(
                    grafo, 
                    carpeta_datos="data", 
                    nombre_coleccion="knowledge_base"
                ))
                st.success("✅ Documentos cargados exitosamente en Qdrant")
                return True
            except Exception as e:
                st.error(f"❌ Error al cargar documentos: {str(e)}")
                return True
    
    elif user_input.startswith("/buscar "):
        consulta = user_input[8:].strip()
        if consulta:
            st.info(f"🔍 Buscando: {consulta}")
            # El procesamiento se hará en el flujo normal del chat
            return False
        else:
            st.warning("Por favor proporciona una consulta de búsqueda. Ejemplo: /buscar funciones python")
            return True
    
    elif user_input == "/buscar":
        st.warning("Por favor proporciona una consulta de búsqueda. Ejemplo: /buscar funciones python")
        return True
    
    elif user_input == "/ayuda":
        st.info("""
        **Comandos disponibles:**
        
        - `/cargar` - Cargar documentos desde la carpeta 'data' a Qdrant
        - `/buscar <consulta>` - Buscar información en los documentos
        - `/ayuda` - Mostrar esta ayuda
        - O simplemente escribe tu pregunta para conversar con B2Bot
        """)
        return True
    
    elif user_input.startswith("/"):
        st.warning("Comando desconocido. Escribe `/ayuda` para ver los comandos disponibles.")
        return True
    
    return False


async def process_user_message(user_input: str, grafo):
    """Procesa un mensaje del usuario y genera la respuesta del agente."""
    config_grafo = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }
    
    # Crear mensaje de entrada
    if user_input.startswith("/buscar "):
        consulta = user_input[8:].strip()
        prompt = f"Busca en la base de datos vectorial Qdrant en la colección 'knowledge_base' información relacionada con: {consulta}"
        entrada = AgentState(messages=[HumanMessage(content=prompt)])
    else:
        entrada = AgentState(messages=[HumanMessage(content=user_input)])
    
    # Crear contenedor para la respuesta del asistente
    response_container = st.empty()
    response_text = ""
    
    # Procesar respuesta del agente con streaming
    async for chunk in stream_graph_response_with_tools(entrada, grafo, config_grafo):
        if chunk["type"] == "tool":
            # Agregar herramienta al historial
            add_tool_to_history(chunk["data"])
        elif chunk["type"] == "content":
            response_text += chunk["data"]
            response_container.markdown(response_text)
    
    return response_text


def main():
    """Función principal de la aplicación Streamlit."""
    
    # Título de la aplicación
    st.title("🤖 B2Bot - Asistente de IA")
    st.markdown("**Agente conversacional con base de conocimientos vectorial**")
    
    # Inicializar estado de sesión
    initialize_session_state()
    
    # Inicializar agente (solo una vez)
    if not st.session_state.agent_initialized:
        with st.spinner("Inicializando B2Bot..."):
            try:
                grafo = initialize_agent()
                st.session_state.grafo = grafo
                st.session_state.agent_initialized = True
                st.success("✅ B2Bot inicializado correctamente")
            except Exception as e:
                st.error(f"❌ Error al inicializar B2Bot: {str(e)}")
                st.stop()
    
    # Layout con dos columnas
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Información del sistema en la barra lateral
        st.sidebar.header("ℹ️ Información del Sistema")
        st.sidebar.markdown(f"""
        **Estado:** <span class="status-indicator status-ready">Conectado</span>

        **ID de Sesión:** `{st.session_state.thread_id[:12]}...`
        
        **Mensajes en historial:** {len(st.session_state.messages)}
        
        **Herramientas utilizadas:** {len(st.session_state.tool_history)}
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown("---")
        
        # Botones de utilidad
        st.sidebar.header("🛠️ Utilidades")
        
        if st.sidebar.button("🗑️ Limpiar Chat"):
            st.session_state.messages = []
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # Mostrar historial de herramientas
        display_tool_history()
    
    with col1:
        # Área principal del chat
        st.header("💬 Chat")
        
        # Contenedor para el historial de chat
        chat_container = st.container()
        
        with chat_container:
            # Mostrar historial de mensajes
            display_chat_history()
        
        # Input del usuario
        if prompt := st.chat_input("Escribe tu mensaje aquí... (Usa /ayuda para ver comandos)"):
            # Verificar comandos especiales
            if handle_special_commands(prompt, st.session_state.grafo):
                st.rerun()
                return
            
            # Agregar mensaje del usuario al historial
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Mostrar mensaje del usuario
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generar y mostrar respuesta del asistente
            with st.chat_message("assistant"):
                with st.status("Procesando...", expanded=False) as status:
                    try:
                        response_text = asyncio.run(process_user_message(prompt, st.session_state.grafo))
                        status.update(label="✅ Completado", state="complete", expanded=False)
                    except Exception as e:
                        st.error(f"❌ Error al procesar mensaje: {str(e)}")
                        response_text = "Lo siento, ocurrió un error al procesar tu mensaje."
            
            # Agregar respuesta del asistente al historial
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Forzar actualización de la interfaz
            st.rerun()


if __name__ == "__main__":
    main()
