import os

from typing import Optional
from httpx import DigestAuth

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.load.dump import dumps

from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph
from langgraph.utils.runnable import RunnableCallable
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.prebuilt.tool_node import ToolNode, tools_condition

from backend.graph import State
from backend.utils import get_logger, get_datetime_formatted
from backend.prompts import system_message
from backend.tools import (
    set_light,
    get_light,
    set_temperature,
    get_temperature,
    activate_scene

)

logger = get_logger("agent")


class Agent():
    def __init__(self):
        self.ollama_chat = ChatOllama(
            model=os.getenv("OLLAMA_MODEL"),
            base_url=os.getenv("OLLAMA_HOST"),
            client_kwargs={
                "auth": DigestAuth(os.getenv("OLLAMA_HOST_USERNAME"), os.getenv("OLLAMA_HOST_PASSWORD"))
            },
            temperature=0.0,
            num_ctx=8192
        )

        self.tools = [
            set_light, get_light, set_temperature, get_temperature, activate_scene
        ]

        self.system_message = system_message

        chat_prompt_template = ChatPromptTemplate([
            ("system", "{system_message}"),
            MessagesPlaceholder(variable_name="messages")
        ])

        if self.tools:
            self.agent = chat_prompt_template | self.ollama_chat.bind_tools(self.tools)
            self.tool_node = ToolNode(
                tools=self.tools
            )
        else:
            self.agent = chat_prompt_template | self.ollama_chat
            self.tool_node = None

    def init_run(self, state: State):
        mod_state = {}

        mod_state["datatime_now"] = get_datetime_formatted()

        return mod_state if mod_state else None

    def compose_system_message(self, state: State) -> str:
        input_vars = {var_name: state.get(var_name, None) for var_name in self.system_message.input_variables}
        return self.system_message.format(**input_vars)
    
    async def agenerate(self, state: State):
        logger.debug("---GENERATING---")

        messages = state["messages"]
        sys_msg = self.compose_system_message(state=state)
        agent_input = {
            "system_message": sys_msg,
            "messages": messages
        }

        logger.debug(dumps(agent_input, pretty=True, ensure_ascii=False))
        response = await self.agent.ainvoke(agent_input)

        return {"messages": [response]}
    
    def generate(self, state: State):
        logger.debug("---GENERATING---")

        messages = state["messages"]
        sys_msg = self.compose_system_message(state=state)
        agent_input = {
            "system_message": sys_msg,
            "messages": messages
        }

        logger.debug(dumps(agent_input, pretty=True, ensure_ascii=False))
        response = self.agent.invoke(agent_input)

        return {"messages": [response]}
    
    def build_graph(self, checkpointer: Optional[BaseCheckpointSaver]) -> CompiledGraph:
        workflow = StateGraph(State)

        workflow.add_node("init_run", self.init_run)
        workflow.add_node("agent", RunnableCallable(self.generate, self.agenerate))
        if self.tools:
            workflow.add_node("agent_tools", self.tool_node)

        workflow.set_entry_point("init_run")
        workflow.add_edge("init_run", "agent")
        if self.tools:
            workflow.add_conditional_edges(
                "agent",
                tools_condition,
                {
                    "tools": "agent_tools",
                    END: END
                }
            )
            workflow.add_edge("agent_tools", "agent")
        else:
            workflow.add_edge("agent", END)

        return workflow.compile(
            checkpointer=checkpointer
        )