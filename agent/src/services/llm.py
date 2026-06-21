"""
OpenRouter LLM client — with cost guardrails.
FIX #3: Hard max_tokens cap, timeout, and fallback on failure.
"""
import json
import httpx
from loguru import logger
from typing import Optional

from ..config import settings


# ─── Fallback reply when LLM fails ─────────────────────────────────

FALLBACK_REPLY = (
    "Sorry, I'm having trouble processing your message right now. "
    "Please try again in a moment, or call us directly. 🙏"
)


class LLMClient:
    """Async LLM client via OpenRouter API, with cost guardrails."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL
        self.max_tokens = settings.OPENROUTER_MAX_TOKENS  # FIX #3: Hard cap
        self.timeout = settings.OPENROUTER_TIMEOUT
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://whatsapp-agent-saas.com",
            "X-Title": "WhatsApp Agent SaaS",
        }

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = None,
    ) -> str:
        """Send a chat completion request. Returns response text or fallback."""
        # FIX #3: Enforce max_tokens cap
        effective_max = min(
            max_tokens or self.max_tokens,
            self.max_tokens,
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": effective_max,
        }

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip()
        except httpx.TimeoutException:
            logger.error(f"LLM timeout after {self.timeout}s")
            return FALLBACK_REPLY
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} — {e.response.text[:200]}")
            return FALLBACK_REPLY
        except Exception as e:
            logger.error(f"LLM client error: {e}")
            return FALLBACK_REPLY

    async def chat_with_history(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = None,
    ) -> str:
        """Send a chat completion with conversation history."""
        effective_max = min(max_tokens or self.max_tokens, self.max_tokens)
        all_messages = [{"role": "system", "content": system_prompt}] + messages
        payload = {
            "model": self.model,
            "messages": all_messages,
            "temperature": temperature,
            "max_tokens": effective_max,
        }

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip()
        except Exception as e:
            logger.error(f"LLM client error (history): {e}")
            return FALLBACK_REPLY

    async def classify_intent(self, message: str, business_context: dict) -> dict:
        """Classify customer message intent using LLM."""
        system = f"""You are an intent classifier for a WhatsApp chatbot serving a {business_context.get('industry', 'local')} business called "{business_context.get('name', 'the business')}".

Classify the customer's message into ONE of these intents:
- greeting: Hello, hi, hey, good morning, etc.
- book_appointment: Wants to book/schedule an appointment
- reschedule: Wants to change an existing appointment
- cancel: Wants to cancel an appointment
- check_availability: Asking about available slots/times
- pricing_query: Asking about prices/costs
- service_info: Asking about services offered
- location_query: Asking about address/directions
- hours_query: Asking about business hours
- confirm: Confirming something (yes, ok, sure, haan, ha)
- deny: Denying something (no, cancel, nahin, nahi)
- small_talk: Casual conversation
- other: Anything else

Also extract any entities like:
- service_name: specific service mentioned
- date: date mentioned (YYYY-MM-DD format if possible)
- time: time mentioned
- name: customer's name if provided

Respond in JSON format only:
{{"intent": "<intent>", "confidence": 0.0-1.0, "entities": {{...}}, "summary": "<brief summary>"}}"""

        # Intent classification uses fewer tokens
        response = await self.chat(system, message, temperature=0.2, max_tokens=150)
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            pass
        return {"intent": "other", "confidence": 0.0, "entities": {}, "summary": message}
