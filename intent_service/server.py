"""gRPC server for the Intent Service.

Listens on GRPC_PORT (default 50051) and exposes the IntentRecognizer RPC.
Uses Ollama via HTTP to classify customer messages into BANKING77 intents.
"""

from __future__ import annotations

import logging
import sys
from concurrent import futures

import grpc

# Generated gRPC stubs
import intent_service_pb2
import intent_service_pb2_grpc

from app.core.settings import get_settings
from app.nodes.intent_node import IntentNode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class IntentServicer(intent_service_pb2_grpc.IntentServiceServicer):
    """gRPC servicer that delegates to the IntentNode."""

    def __init__(self) -> None:
        settings = get_settings()
        self.intent_node = IntentNode(settings)
        logger.info(
            "IntentServicer initialised (model=%s, ollama=%s)",
            settings.intent_model_name,
            settings.ollama_base_url,
        )

    def IntentRecognizer(self, request, context):
        """Handle an IntentRecognizer RPC call."""
        message = request.message
        logger.info("Received intent request: '%.80s...'", message)

        result = self.intent_node.run(message)

        logger.info(
            "Intent result: intent=%s, confidence=%.2f, reason=%s",
            result.intent,
            result.confidence,
            result.reason,
        )

        return intent_service_pb2.IntentResponse(
            intent=result.intent,
            confidence=result.confidence,
            reason=result.reason,
        )


def serve() -> None:
    """Start the gRPC server."""
    settings = get_settings()
    port = settings.grpc_port

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    intent_service_pb2_grpc.add_IntentServiceServicer_to_server(
        IntentServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("Intent Service gRPC server started on port %d", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
