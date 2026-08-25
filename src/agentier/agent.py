from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from agentier.tools import calculator, get_current_time, write_and_edit_file
from profiler.profiler import Profiler

load_dotenv()

# --- Constants -------------------------------------------------------
SYSTEM_PROMPT = """
    You are a concise, helpful assistant. Use tools when they help answer the question accurately; otherwise just answer directly.
    """
MODEL = "claude-sonnet-4-5"
TOOLS = [calculator, get_current_time, write_and_edit_file]
# Fixed thread_id = one conversation for the whole run of this program.
CONFIG = {"configurable": {"thread_id": "single-session"}}

# --- Model -------------------------------------------------------------
llm = ChatAnthropic(
    model=MODEL,
    temperature=1,
    thinking={"type": "enabled", "budget_tokens": 2048}
)
llm_with_tools = llm.bind_tools(TOOLS)


# --- Graph -------------------------------------------------------------
# call_model: ask the model what to do next (answer, or call a tool).
def call_model(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("chat", call_model)
builder.add_node("tools", ToolNode(TOOLS))

builder.add_edge(START, "chat")
# tools_condition inspects the last message: if it has tool_calls, route to
# "tools"; otherwise route to END. This is the loop-or-stop decision that
# makes this an agent rather than a single-shot chain.
builder.add_conditional_edges("chat", tools_condition, {"tools": "tools", END: END})
# After running a tool, go back to the model so it can use the result --
# possibly calling another tool, possibly answering. This is the loop.
builder.add_edge("tools", "chat")

# MemorySaver keeps message history in memory, scoped to a thread_id.
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)


def run_agent():
    print("Welcome to your agent!")
    print(f"Tools available: {', '.join(t.name for t in TOOLS)}\n")

    target_schema_filepath = "../schemas/target_schema.json"
    profiler = Profiler(target_schema_filepath)


    # result = graph.invoke({"messages": [("user", user_input)]}, CONFIG)
    # content = result["messages"][-1].content
