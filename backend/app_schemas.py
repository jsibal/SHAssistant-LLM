from typing import Optional, TypedDict
from pydantic import BaseModel, Field

from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import AnyMessage


class AppState(TypedDict):
    chain: CompiledGraph


class ChainInput(BaseModel):
    messages: list[AnyMessage] = Field(..., description="Messages history.")

    datatime_now: Optional[str] = Field(default=None, description="Current date and time. Added on backend side when invoking.")


class ChainConfigurable(TypedDict, total=False):
    checkpoint_id: Optional[str]
    checkpoint_ns: Optional[str]
    thread_id: Optional[str]


class ChainConfig(TypedDict, total=False):
    configurable: Optional[ChainConfigurable]


class ChainOutput(BaseModel):
    messages: list[AnyMessage] = Field(..., description="Messages history.")

    datatime_now: Optional[str] = Field(default=None, description="Current date and time. Added on backend side when invoking.")

# ==================================================================================================================================

class InputSchema(BaseModel):
    input: ChainInput = Field(..., description="Input for the runnable.")
    config: ChainConfig = Field(..., description="Run config.")

class OutputSchema(BaseModel):
    output: ChainOutput = Field(..., description="Result of current run with state.")