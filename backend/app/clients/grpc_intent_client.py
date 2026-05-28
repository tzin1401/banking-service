"""gRPC client for the Intent Service.

Connects to the Intent Service microservice and calls the IntentRecognizer RPC
to classify customer messages.
"""

from __future__ import annotations

import logging

import grpc

from app.clients.intent_grpc import intent_service_pb2, intent_service_pb2_grpc
from app.core.schemas import IntentResult

logger = logging.getLogger(__name__)


class GrpcIntentClient:
    """Client that calls the Intent Service over gRPC."""

    def __init__(self, host: str = "intent-service", port: int = 50051) -> None:
        self.target = f"{host}:{port}"
        self._channel: grpc.Channel | None = None
        self._stub: intent_service_pb2_grpc.IntentServiceStub | None = None

    def _ensure_channel(self) -> intent_service_pb2_grpc.IntentServiceStub:
        """Lazily create the gRPC channel and stub."""
        if self._stub is None:
            logger.info("Opening gRPC channel to %s", self.target)
            self._channel = grpc.insecure_channel(self.target)
            self._stub = intent_service_pb2_grpc.IntentServiceStub(self._channel)
        return self._stub

    def predict(self, message: str) -> IntentResult:
        """Send a message to the Intent Service and return the result."""
        stub = self._ensure_channel()
        request = intent_service_pb2.IntentRequest(message=message)

        try:
            response = stub.IntentRecognizer(request, timeout=120)
            return IntentResult(
                intent=response.intent,
                confidence=response.confidence,
                source="grpc",
            )
        except grpc.RpcError as exc:
            logger.exception("gRPC call to Intent Service failed.")
            return IntentResult(
                intent="default",
                confidence=0.0,
                source="grpc",
            )

    def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel is not None:
            self._channel.close()
            self._channel = None
            self._stub = None
