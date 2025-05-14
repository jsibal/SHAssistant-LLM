import os
import traceback

from typing import TypedDict, Optional, Union, Annotated, Literal, Any
from pydantic import BaseModel

from langchain_core.load.dump import dumps

from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import AnyMessage, add_messages

from backend.utils import get_logger


logger = get_logger("graph")


class PartialState(TypedDict, total=False):
    datatime_now: Optional[str]


class State(PartialState):
    messages: Annotated[list[AnyMessage], add_messages]


def tools_condition(state: Union[list[AnyMessage], dict[str, Any], BaseModel]) -> Literal["tools", "__end__"]:
    if isinstance(state, list):
        ai_message = state[-1]
    elif isinstance(state, dict) and (messages := state.get("messages", [])):
        ai_message = messages[-1]
    elif messages := getattr(state, "messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        logger.debug("---TOOL CALLS---")
        logger.debug(dumps(ai_message.tool_calls, pretty=True, ensure_ascii=False))
        return "tools"

    logger.debug("---CONTINUE---")
    return "__end__"


def plot_graph(graph: CompiledGraph, save_path: Optional[str] = None) -> Optional[bytes]:
    try:
        img = graph.get_graph().draw_mermaid_png()
        if save_path is not None and (os.path.exists(save_path) or os.access(os.path.dirname(save_path), os.W_OK)):
            logger.info(f"Saving drawn graph on path: {save_path}")
            with open(save_path, "wb") as f:
                f.write(img)
        return img
    except Exception:
        logger.error(traceback.format_exc())
        return None