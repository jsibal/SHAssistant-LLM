from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request

from typing import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.graph.graph import CompiledGraph
from langgraph.checkpoint.memory import MemorySaver

from backend.agent import Agent
from backend.graph import plot_graph
from backend.app_schemas import InputSchema, OutputSchema, AppState


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[AppState]:
    agent = Agent()
    memory = MemorySaver()
    agent_chain = agent.build_graph(checkpointer=memory)

    _ = plot_graph(graph=agent_chain, save_path="./graph.png")

    yield {"chain": agent_chain}

app = FastAPI(
    title="HDS",
    description="KKY/HDS SP2 (2025)",
    debug=False,
    lifespan=lifespan
)


@app.post("/hds/invoke")
async def invoke(invoke_data: InputSchema, request: Request) -> OutputSchema:
    chain: CompiledGraph = request.state.chain
    input = invoke_data.input
    config = invoke_data.config

    output = await chain.ainvoke(input=input, config=config)

    return {"output": output}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)