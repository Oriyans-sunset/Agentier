import time
from datetime import datetime, timezone
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from fixer.models import FixerResult
from fixer.tools import Tools
from fixer.constants import SYSTEM_PROMPT, MODEL, DATA_SCHEMA_PATH, INVESTIGATION_RESULT_PATH, FIXER_RESULT_PATH, LOG_PATH
from fixer.logger import FixerLogger

load_dotenv()

tools = Tools(INVESTIGATION_RESULT_PATH, DATA_SCHEMA_PATH)

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
llm_with_tools = llm.bind_tools(TOOLS + [FixerResult])

# --- Logging ----------------------------------------------------------
_logger = FixerLogger(LOG_PATH)


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
    if any(call["name"] == "FixerResult" for call in tool_calls):
        return END
    return "tools"


_tool_node = ToolNode(TOOLS)


def logged_tools(state: MessagesState):
    ai_msg = next(m for m in reversed(state["messages"]) if hasattr(m, "tool_calls"))
    calls_map = {call["id"]: call for call in ai_msg.tool_calls}

    called_at = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    result = _tool_node.invoke(state)
    t1 = time.perf_counter()
    completed_at = datetime.now(timezone.utc).isoformat()
    duration_ms = round((t1 - t0) * 1000)

    for tm in result["messages"]:
        original_call = calls_map.get(tm.tool_call_id, {})
        _logger.log_tool_call(
            tool_name=tm.name,
            input_args=original_call.get("args", {}),
            output=tm.content if isinstance(tm.content, str) else str(tm.content),
            status=tm.status,
            called_at=called_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

    return result


builder = StateGraph(MessagesState)
builder.add_node("chat", call_model)
builder.add_node("tools", logged_tools)

builder.add_edge(START, "chat")
builder.add_conditional_edges("chat", route_after_chat, {"tools": "tools", END: END})
# After running a tool, go back to the model so it can use the result --
# possibly calling another tool, possibly answering. This is the loop.
builder.add_edge("tools", "chat")

graph = builder.compile()

class InvestigatorAgent:
    def __init__(self):
        pass

    def run_agent(self):
        _logger.start_session(DATA_SCHEMA_PATH)
        print("Fixer/Doctor Agent booted!")
        print(f"Tools available: {', '.join(t.name for t in TOOLS)}\n")

        result = graph.invoke({"messages": [("user", "Start fixing.")]})
        last_message = result["messages"][-1]

        final_call = next(
            (call for call in last_message.tool_calls if call["name"] == "FixerResult"),
            None,
        )
        if final_call is not None:
            fixer_result = FixerResult(**final_call["args"])
            _logger.end_session(findings_count=len(fixer_result.findings))
            with open(FIXER_RESULT_PATH, "w") as f:
                f.write(fixer_result.model_dump_json(indent=2))
            print(fixer_result.model_dump_json(indent=2))
            return fixer_result

        _logger.end_session(findings_count=None)
        print(last_message.content)
        return None
