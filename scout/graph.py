from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, add_messages, START
from langchain_core.messages import SystemMessage
from pydantic import BaseModel
from typing import List, Annotated
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
import os


class AgentState(BaseModel):
        messages: Annotated[List, add_messages]

system_prompt = """
## Role
Your name is Scout and you are an expert data scientist. You help customers manage their data science projects.

## Context
1. You are only able to access files within the working directory `projects`:
{working_dir}
2. Within each project, there are two important objects:
    a. A `data` directory, which contains the user's data.
    b. A `main.py` file which contains the code for the project. The main.py file is the entry point for the project and will contain all the code to load, transform, and model the data.

## Work Requirements
1. All work must be done within this directory.
2. Always use absolute paths when specifying files.

## Tools
You have access to four categories of tools:

1. dataflow - used to load the user's data into the session and query it
2. filesystem - used to read and write files
3. git - used for all local git operations
4. github - used for all github operations

## Instructions
Assist the customer in all aspects of their data science workflow.
""".format(working_dir=os.environ.get("MCP_FILESYSTEM_DIR", None))


def build_agent_graph(tools: List = []):
    llm = ChatOpenAI(name="Scout", model="gpt-4.1-mini-2025-04-14")
    if tools:
        llm = llm.bind_tools(tools)

    def assistant(state: AgentState) -> AgentState:
        response = llm.invoke([SystemMessage(content=system_prompt)] + state.messages)
        state.messages.append(response)
        return state

    builder = StateGraph(AgentState)

    builder.add_node("Scout", assistant)
    builder.add_node(ToolNode(tools))

    builder.add_edge(START, "Scout")
    builder.add_conditional_edges(
        "Scout",
        tools_condition,
    )
    builder.add_edge("tools", "Scout")

    return builder.compile(checkpointer=MemorySaver())

# visualize graph
if __name__ == "__main__":
    from IPython.display import display, Image
    
    graph = build_agent_graph()
    display(Image(graph.get_graph().draw_mermaid_png()))