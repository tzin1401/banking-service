"""Intent detection node — gRPC-based.

Delegates intent classification to the Intent Service microservice via gRPC.
This replaces the Lab 3 Unsloth/mock-based implementation.
"""

from __future__ import annotations

import logging

from app.clients.grpc_intent_client import GrpcIntentClient
from app.core.schemas import IntentResult

logger = logging.getLogger(__name__)


class IntentNode:
    """Detect intent by calling the Intent Service over gRPC."""

    def __init__(self, grpc_client: GrpcIntentClient) -> None:
        self.client = grpc_client

    def run(self, message: str) -> IntentResult:
        """Return the predicted intent for the message via gRPC."""
        logger.info("Calling Intent Service via gRPC...")
        return self.client.predict(message)
