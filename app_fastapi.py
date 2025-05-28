import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, status, Security, Depends
from fastapi.security import APIKeyHeader

from typing import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.graph.graph import CompiledGraph
from langgraph.checkpoint.memory import MemorySaver

from backend.agent import Agent
from backend.graph import plot_graph
from backend.app_schemas import InputSchema, OutputSchema, AppState


APP_API_TOKEN = os.getenv("APP_API_TOKEN")
def verify_api_token(api_token_header: str = Security(APIKeyHeader(name="token"))):
    """Verify API token from header"""
    if api_token_header != APP_API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[AppState]:
    agent = Agent()
    memory = MemorySaver()
    agent_chain = agent.build_graph(checkpointer=memory)

    # _ = plot_graph(graph=agent_chain, save_path="./graph.png")

    yield {"chain": agent_chain}

app = FastAPI(
    title="HDS",
    description="KKY/HDS SP2 (2025)",
    debug=False,
    lifespan=lifespan,
    dependencies=[Depends(verify_api_token)],
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