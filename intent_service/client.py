"""Test client for the Intent Service gRPC server.

Usage:
    python client.py "I lost my card and need a replacement"
"""

from __future__ import annotations

import sys

import grpc
import intent_service_pb2
import intent_service_pb2_grpc


def run(message: str, host: str = "localhost", port: int = 50051) -> None:
    """Send a message to the Intent Service and print the result."""
    target = f"{host}:{port}"
    print(f"Connecting to Intent Service at {target}...")

    with grpc.insecure_channel(target) as channel:
        stub = intent_service_pb2_grpc.IntentServiceStub(channel)
        request = intent_service_pb2.IntentRequest(message=message)
        response = stub.IntentRecognizer(request, timeout=120)

    print(f"  Intent:     {response.intent}")
    print(f"  Confidence: {response.confidence:.2f}")
    print(f"  Reason:     {response.reason}")


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "I lost my card"
    run(msg)
