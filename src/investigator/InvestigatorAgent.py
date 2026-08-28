import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from profiler.profiler import Profiler
from investigator.tools import Tools
from investigator.models import InvestigationResult
from investigator.constants import SYSTEM_PROMPT, MODEL, PROFILED_SCHEMA_PATH, TARGET_SCHEMA_PATH

load_dotenv()

tools = Tools(PROFILED_SCHEMA_PATH)

# --- Constants -------------------------------------------------------
TOOLS = tools.get_all_tools()
# define llm
llm = ChatAnthropic(
    model=MODEL,
    temperature=1,
    thinking={"type": "enabled", "budget_tokens": 8000}
)
# InvestigationResult is bound as a "tool" too: the model calls it to submit
# its final structured answer instead of ending the loop with plain text.
llm_with_tools = llm.bind_tools(TOOLS + [InvestigationResult])


# --- Graph -------------------------------------------------------------
# call_model: ask the model what to do next (answer, or call a tool).
def call_model(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def route_after_chat(state: MessagesState):
    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        return END
    # InvestigationResult is the finish signal, not a real tool -- ToolNode
    # has no executor for it, so route straight to END instead.
    if any(call["name"] == "InvestigationResult" for call in tool_calls):
        return END
    return "tools"


builder = StateGraph(MessagesState)
builder.add_node("chat", call_model)
builder.add_node("tools", ToolNode(TOOLS))

builder.add_edge(START, "chat")
builder.add_conditional_edges("chat", route_after_chat, {"tools": "tools", END: END})
# After running a tool, go back to the model so it can use the result --
# possibly calling another tool, possibly answering. This is the loop.
builder.add_edge("tools", "chat")

# MemorySaver keeps message history in memory, scoped to a thread_id.
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

class InvestigatorAgent:
    def __init__(self):
        pass

    def run_agent(self):
        print("Investigator Agent booted!")
        print(f"Tools available: {', '.join(t.name for t in TOOLS)}\n")

        user_input = ""

        result = graph.invoke({"messages": [("user", user_input)]})
        last_message = result["messages"][-1]

        final_call = next(
            (call for call in last_message.tool_calls if call["name"] == "InvestigationResult"),
            None,
        )
        if final_call is not None:
            investigation_result = InvestigationResult(**final_call["args"])
            print(investigation_result)
            return investigation_result

        print(last_message.content)
        return None
