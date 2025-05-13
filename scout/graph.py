from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, add_messages, START
from pydantic import BaseModel
from typing import List, Annotated
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


class AgentState(BaseModel):
        messages: Annotated[List, add_messages]


def build_agent_graph(tools: List = []):
    llm = ChatOpenAI(model="gpt-4.1-mini-2025-04-14")
    if tools:
        llm = llm.bind_tools(tools)

    def assistant(state: AgentState) -> AgentState:
        response = llm.invoke(state.messages)
        state.messages.append(response)
        return state

    builder = StateGraph(AgentState)

    builder.add_node(assistant)
    builder.add_node(ToolNode(tools))

    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    builder.add_edge("tools", "assistant")

    return builder.compile(checkpointer=MemorySaver())