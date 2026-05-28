"""Pydantic schemas for the Intent Service."""

from __future__ import annotations

from pydantic import BaseModel


class IntentResult(BaseModel):
    """Output of the intent detection node."""

    intent: str
    confidence: float = 0.0
    reason: str = ""
