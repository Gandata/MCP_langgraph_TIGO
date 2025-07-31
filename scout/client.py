"""
Este archivo implementa el Cliente MCP para nuestro Agente Langgraph.

Los Clientes MCP son responsables de conectarse y comunicarse con los servidores MCP.
Este cliente es análogo a Cursor o Claude Desktop y lo configurarías de la misma manera
especificando la configuración del servidor MCP en my_mcp/mcp_config.json.
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
        entrada: AgentState, grafo: StateGraph, config: dict = {}
        ) -> AsyncGenerator[str, None]:
    """
    Transmite la respuesta del grafo mientras analiza las llamadas a herramientas.

    Args:
        entrada: La entrada para el grafo.
        grafo: El grafo a ejecutar.
        config: La configuración a pasar al grafo. Requerida para la memoria.

    Yields:
        Una cadena procesada de la respuesta fragmentada del grafo.
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
                    yield "\n\n"

            if fragmento_mensaje.tool_call_chunks:
                fragmento_herramienta = fragmento_mensaje.tool_call_chunks[0]

                nombre_herramienta = fragmento_herramienta.get("name", "")
                argumentos = fragmento_herramienta.get("args", "")
                
                if nombre_herramienta:
                    cadena_llamada = f"\n\n< LLAMADA A HERRAMIENTA: {nombre_herramienta} >\n\n"
                if argumentos:
                    cadena_llamada = argumentos

                yield cadena_llamada
            else:
                yield fragmento_mensaje.content
            continue


async def cargar_documentos_a_qdrant(grafo: StateGraph, carpeta_datos: str = "data", nombre_coleccion: str = "knowledge_base"):
    """
    Carga todos los documentos desde la carpeta de datos a la base de datos vectorial Qdrant.
    
    Args:
        grafo: La instancia del grafo con herramientas MCP
        carpeta_datos: Ruta a la carpeta que contiene los documentos a cargar
        nombre_coleccion: Nombre de la colección Qdrant para almacenar documentos
    """
    ruta_datos = Path(carpeta_datos)
    if not ruta_datos.exists():
        print(f"La carpeta de datos '{carpeta_datos}' no existe.")
        return
    
    # Extensiones de archivo soportadas
    extensiones_soportadas = {'.txt', '.md', '.py', '.json', '.csv', '.html', '.xml', '.docx', '.pdf'}
    
    archivos_a_procesar = []
    for ruta_archivo in ruta_datos.rglob('*'):
        if ruta_archivo.is_file() and ruta_archivo.suffix.lower() in extensiones_soportadas:
            archivos_a_procesar.append(ruta_archivo)
    
    if not archivos_a_procesar:
        print(f"No se encontraron documentos compatibles en la carpeta '{carpeta_datos}'.")
        print(f"Extensiones soportadas: {', '.join(extensiones_soportadas)}")
        return
    
    print(f"Se encontraron {len(archivos_a_procesar)} documentos para cargar en Qdrant...")
    
    for ruta_archivo in archivos_a_procesar:
        try:
            # Leer contenido del archivo
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            if not contenido.strip():
                print(f"Saltando archivo vacío: {ruta_archivo}")
                continue
            
            # Crear un mensaje pidiendo al asistente que almacene el documento
            metadata_str = f"nombre_archivo: {ruta_archivo.name}, ruta_archivo: {str(ruta_archivo)}, extension: {ruta_archivo.suffix}"
            prompt = f"Por favor almacena este documento en la base de datos vectorial Qdrant con el nombre de colección '{nombre_coleccion}'. Contenido del documento: {contenido}\n\nMetadatos: {metadata_str}"
            
            # Usar el grafo para procesar la solicitud
            respuesta = await grafo.ainvoke(
                AgentState(messages=[HumanMessage(content=prompt)]),
                config={"configurable": {"thread_id": "carga_documentos"}}
            )
            
            print(f"✓ Procesado: {ruta_archivo.name}")
            
        except Exception as e:
            print(f"✗ Error al procesar {ruta_archivo.name}: {str(e)}")
    
    print(f"¡Proceso de carga de documentos completado!")


async def buscar_documentos_en_qdrant(grafo: StateGraph, consulta: str, nombre_coleccion: str = "knowledge_base"):
    """
    Busca documentos relevantes en Qdrant basándose en una consulta.
    
    Args:
        grafo: La instancia del grafo con herramientas MCP
        consulta: La consulta de búsqueda
        nombre_coleccion: Nombre de la colección Qdrant a buscar
        
    Returns:
        Resultados de búsqueda desde Qdrant
    """
    try:
        # Crear un mensaje pidiendo al asistente que busque documentos
        prompt = f"Por favor busca en la base de datos vectorial Qdrant en la colección '{nombre_coleccion}' información relacionada con: {consulta}"
        
        # Usar el grafo para procesar la solicitud de búsqueda
        respuesta = await grafo.ainvoke(
            AgentState(messages=[HumanMessage(content=prompt)]),
            config={"configurable": {"thread_id": "busqueda_documentos"}}
        )
        
        return respuesta
        
    except Exception as e:
        print(f"Error al buscar documentos: {str(e)}")
        return None


async def main():
    """
    Inicializa el cliente MCP y ejecuta el bucle de conversación del agente.

    El MultiServerMCPClient permite la conexión a múltiples servidores MCP usando un solo cliente y configuración.
    """
    # Crear el cliente sin usarlo como administrador de contexto
    cliente = MultiServerMCPClient(
        connections=mcp_config
    )
    
    # Obtener herramientas usando el nuevo método asíncrono
    herramientas = await cliente.get_tools()
    grafo = build_agent_graph(tools=herramientas)

    # pasar una configuración con thread_id para usar memoria
    config_grafo = {
        "configurable": {
            "thread_id": "1"
        }
    }

    print("Agente MCP para gestión interna TIGO")
    print("=" * 50)
    # print("Comandos disponibles:")
    # print("  /cargar     - Cargar documentos desde la carpeta data a Qdrant")
    # print("  /buscar     - Buscar documentos en Qdrant")
    # print("  /ayuda       - Mostrar este mensaje de ayuda")
    print("  salir/exit   - Salir del programa")
    print("  O simplemente escribe tu pregunta para conversar con el asistente")
    print("=" * 50)

    while True:
        entrada_usuario = input("\nUSUARIO: ").strip()
        
        if entrada_usuario.lower() in ["salir", "exit"]:
            break
        elif entrada_usuario == "/ayuda":
            print("\n Ayuda:")
            # print("  /cargar     - Cargar todos los documentos desde la carpeta 'data' a la base de datos vectorial Qdrant")
            # print("  /buscar     - Buscar información en los documentos cargados")
            print("  salir/exit   - Salir del programa")
            print("  O escribe cualquier pregunta para conversar con el asistente de IA")
            continue
        elif entrada_usuario == "/cargar":
            print("\n Cargando documentos a Qdrant...")
            await cargar_documentos_a_qdrant(grafo, carpeta_datos="data", nombre_coleccion="knowledge_base")
            continue
        elif entrada_usuario.startswith("/buscar "):
            consulta = entrada_usuario[8:].strip()  # Remover prefijo "/buscar "
            if consulta:
                print(f"\n Buscando: {consulta}")
                print("\n ---- RESULTADOS DE BÚSQUEDA ----\n")
                
                async for respuesta in stream_graph_response(
                    input = AgentState(messages=[HumanMessage(content=f"Busca en la base de datos vectorial Qdrant en la colección 'knowledge_base' información relacionada con: {consulta}")]),
                    grafo = grafo, 
                    config = {"configurable": {"thread_id": "busqueda"}}
                ):
                    print(respuesta, end="", flush=True)
                print("\n")
            else:
                print("Por favor proporciona una consulta de búsqueda. Ejemplo: /buscar funciones python")
            continue
        elif entrada_usuario == "/buscar":
            print("Por favor proporciona una consulta de búsqueda. Ejemplo: /buscar funciones python")
            continue
        elif entrada_usuario.startswith("/"):
            print("Comando desconocido. Escribe /ayuda para ver los comandos disponibles.")
            continue

        print(f"\n ----  USUARIO  ---- \n\n {entrada_usuario}")
        print("\n ----  ASISTENTE  ---- \n\n")

        async for respuesta in stream_graph_response(
            #input = AgentState(messages=[HumanMessage(content=entrada_usuario)]),
            entrada = AgentState(messages=[HumanMessage(content=entrada_usuario)]),
            grafo = grafo, 
            config = config_grafo
            ):
            print(respuesta, end="", flush=True)

if __name__ == "__main__":
    import asyncio
    # solo necesario si se ejecuta en un ipykernel
    import nest_asyncio
    nest_asyncio.apply()

    asyncio.run(main())