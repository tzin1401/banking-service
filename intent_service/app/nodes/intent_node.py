"""Intent detection node — Ollama-based classification.

Sends a structured prompt to the Ollama LLM asking it to classify the customer
message into one of the BANKING77 intent labels. The model returns a JSON
object with intent, confidence, and reason.
"""

from __future__ import annotations

import json
import logging
import re

import requests

from app.core.schemas import IntentResult
from app.core.settings import Settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BANKING77 label set (subset of most common intents)
# ---------------------------------------------------------------------------

BANKING77_LABELS: list[str] = [
    "activate_my_card",
    "age_limit",
    "apple_pay_or_google_pay",
    "atm_support",
    "automatic_top_up",
    "balance_not_updated_after_bank_transfer",
    "balance_not_updated_after_cheque_or_cash_deposit",
    "beneficiary_not_allowed",
    "cancel_transfer",
    "card_about_to_expire",
    "card_acceptance",
    "card_arrival",
    "card_delivery_estimate",
    "card_linking",
    "card_not_working",
    "card_payment_fee_charged",
    "card_payment_not_recognised",
    "card_payment_wrong_exchange_rate",
    "card_swallowed",
    "cash_withdrawal_charge",
    "cash_withdrawal_not_recognised",
    "change_pin",
    "compromised_card",
    "contactless_not_working",
    "country_support",
    "declined_card_payment",
    "declined_cash_withdrawal",
    "declined_transfer",
    "direct_debit_payment_not_recognised",
    "disposable_card_limits",
    "edit_personal_details",
    "exchange_charge",
    "exchange_rate",
    "exchange_via_app",
    "extra_charge_on_statement",
    "failed_transfer",
    "fiat_currency_support",
    "get_disposable_virtual_card",
    "get_physical_card",
    "getting_spare_card",
    "getting_virtual_card",
    "lost_or_stolen_card",
    "lost_or_stolen_phone",
    "order_physical_card",
    "passcode_forgotten",
    "pending_card_payment",
    "pending_cash_withdrawal",
    "pending_top_up",
    "pending_transfer",
    "pin_blocked",
    "receiving_money",
    "Refund_not_showing_up",
    "request_refund",
    "reverted_card_payment?",
    "supported_cards_and_currencies",
    "terminate_account",
    "top_up_by_bank_transfer_charge",
    "top_up_by_card_charge",
    "top_up_by_cash_or_cheque",
    "top_up_failed",
    "top_up_limits",
    "top_up_reverted",
    "topping_up_by_card",
    "transaction_charged_twice",
    "transfer_fee_charged",
    "transfer_into_account",
    "transfer_not_received_by_recipient",
    "transfer_timing",
    "unable_to_verify_identity",
    "verify_my_identity",
    "verify_source_of_funds",
    "verify_top_up",
    "virtual_card_not_working",
    "visa_or_mastercard",
    "why_verify_identity",
    "wrong_amount_of_cash_received",
    "wrong_exchange_rate_for_cash_withdrawal",
]


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an intent classification engine for a banking customer support system. "
    "You must classify the customer's message into exactly ONE of the provided intent labels. "
    "Always return a valid JSON object with no additional text."
)

USER_PROMPT_TEMPLATE = """\
Classify the following customer message into exactly one of these intent labels:

{labels}

Customer message:
\"\"\"{message}\"\"\"

Return ONLY a JSON object with these keys:
- "intent": the predicted intent label (must be one from the list above)
- "confidence": a float between 0.0 and 1.0
- "reason": a brief one-sentence explanation

Return ONLY the JSON object, no preamble, no markdown fences.
"""


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _strip_json(text: str) -> str:
    """Extract a JSON object from arbitrary LLM output."""
    text = text.strip()
    fence = _JSON_FENCE_RE.search(text)
    if fence:
        return fence.group(1)
    obj = _JSON_OBJECT_RE.search(text)
    if obj:
        return obj.group(0)
    return text


# ---------------------------------------------------------------------------
# Intent Node
# ---------------------------------------------------------------------------


class IntentNode:
    """Detect intent using Ollama LLM with a classification prompt."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.intent_model_name
        self.timeout = settings.ollama_timeout

    def run(self, message: str) -> IntentResult:
        """Classify the customer message into a BANKING77 intent."""

        labels_str = ", ".join(BANKING77_LABELS)
        prompt = USER_PROMPT_TEMPLATE.format(labels=labels_str, message=message.strip())

        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 256,
                },
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = (data.get("message", {}) or {}).get("content", "").strip()

            if not content:
                logger.warning("Empty response from Ollama for intent prediction.")
                return IntentResult(intent="default", confidence=0.0, reason="Empty LLM response")

            # Parse JSON from LLM output
            candidate = _strip_json(content)
            parsed = json.loads(candidate)

            intent = str(parsed.get("intent", "default")).strip()
            confidence = float(parsed.get("confidence", 0.0))
            reason = str(parsed.get("reason", "")).strip()

            # Validate intent is in the known label set
            if intent not in BANKING77_LABELS:
                logger.warning("LLM returned unknown intent '%s', using as-is.", intent)

            return IntentResult(intent=intent, confidence=confidence, reason=reason)

        except (requests.RequestException, json.JSONDecodeError, Exception) as exc:
            logger.exception("Intent prediction failed.")
            return IntentResult(
                intent="default",
                confidence=0.0,
                reason=f"Prediction error: {exc}",
            )
