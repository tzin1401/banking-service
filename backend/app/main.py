"""FastAPI application — API Gateway for the Banking AI-Agent.

Lab 4: Microservice architecture. This gateway orchestrates the agentic
workflow, calling the Intent Service via gRPC and Ollama via HTTP.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent.orchestrator import BankingAgent
from app.core.schemas import AgentResponse, CustomerRequest
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: build the agent once and reuse it across requests
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Building BankingAgent (ollama=%s, model=%s, intent_service=%s:%d)",
        settings.ollama_url,
        settings.ollama_model,
        settings.intent_service_host,
        settings.intent_service_port,
    )
    agent = BankingAgent(settings=settings)
    app.state.agent = agent
    app.state.settings = settings
    yield
    logger.info("Shutting down BankingAgent.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    app = FastAPI(
        title="Banking AI-Agent — API Gateway",
        description=(
            "Agentic workflow for banking customer support — Lab 4, "
            "Applications of NLP in Industry, University of Science, VNU-HCM. "
            "Microservice architecture with gRPC Intent Service and Ollama."
        ),
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    @app.get("/health", tags=["meta"])
    def health() -> dict[str, Any]:
        """Check whether the system is running."""
        return {"status": "ok"}

    # ------------------------------------------------------------------
    @app.get("/config", tags=["meta"])
    def config() -> dict[str, Any]:
        """Return the current system configuration."""
        settings = app.state.settings
        return {
            "ollama_url": settings.ollama_url,
            "ollama_model": settings.ollama_model,
            "intent_service_host": settings.intent_service_host,
            "intent_service_port": settings.intent_service_port,
            "mock_llm": settings.mock_llm,
            "llm_max_tokens": settings.llm_max_tokens,
            "llm_reasoning_effort": settings.llm_reasoning_effort,
        }

    # ------------------------------------------------------------------
    @app.post("/run-agent", response_model=AgentResponse, tags=["agent"])
    def run_agent(request: CustomerRequest) -> AgentResponse:
        """Execute the full agentic workflow."""
        agent: BankingAgent = app.state.agent
        try:
            return agent.run(request.message)
        except Exception as exc:
            logger.exception("Agent.run failed.")
            raise HTTPException(
                status_code=500, detail=f"Agent failure: {exc}"
            ) from exc

    return app


app = create_app()
