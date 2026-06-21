"""
Meta WhatsApp Cloud API messaging service.
Replaces Twilio. Uses direct Graph API calls — ₹0 cost for service-window replies.

API docs: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
Webhook docs: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components
"""
import httpx
from loguru import logger

from ..config import settings


# ─── Meta Cloud API constants ───────────────────────────────────────

META_API_BASE = f"https://graph.facebook.com/{settings.META_API_VERSION}"


class WhatsAppService:
    """Send WhatsApp messages via Meta Cloud API (direct, no BSP)."""

    def __init__(
        self,
        access_token: str = None,
        phone_number_id: str = None,
    ):
        self.access_token = access_token or settings.WHATSAPP_TOKEN
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = f"{META_API_BASE}/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def send_text(self, to: str, body: str) -> str | None:
        """Send a text message. Returns Meta message ID or None on failure."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body[:4096],  # WhatsApp max message length
            },
        }
        return self._send(payload)

    def send_interactive_buttons(
        self, to: str, body: str, buttons: list[dict]
    ) -> str | None:
        """Send interactive quick-reply buttons (max 3).
        buttons: [{"id": "btn_1", "title": "Option 1"}, ...]
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": btn["id"], "title": btn["title"][:20]},
                        }
                        for btn in buttons[:3]
                    ]
                },
            },
        }
        return self._send(payload)

    def _send(self, payload: dict) -> str | None:
        """POST to Meta Graph API. Returns message ID or None."""
        try:
            # Meta API is synchronous — use httpx in sync mode for simplicity
            response = httpx.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            msg_id = data.get("messages", [{}])[0].get("id", "")
            logger.info(f"Meta msg sent: {msg_id} to {payload.get('to')}")
            return msg_id
        except httpx.HTTPStatusError as e:
            logger.error(f"Meta API error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Meta send error: {e}")
            return None


def parse_meta_webhook(payload: dict) -> dict | None:
    """Parse a Meta WhatsApp Cloud API webhook payload.

    Returns dict with: from_number, to_number, body, message_id, message_type, timestamp
    Returns None if payload is not a user message (e.g. status updates, other objects).

    Example Meta webhook payload:
    {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "16505551234",
                        "phone_number_id": "PHONE_NUMBER_ID"
                    },
                    "contacts": [{"profile": {"name": "John"}, "wa_id": "919876543210"}],
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.xxx",
                        "timestamp": "1718700000",
                        "text": {"body": "Hello"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    """
    try:
        obj = payload.get("object", "")
        if obj != "whatsapp_business_account":
            return None

        entries = payload.get("entry", [])
        if not entries:
            return None

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                field = change.get("field", "")

                # Skip non-message webhooks (account_alerts, etc.)
                if field and field != "messages":
                    return None

                metadata = value.get("metadata", {})
                to_number = _strip_whatsapp_prefix(metadata.get("display_phone_number", ""))
                phone_number_id = metadata.get("phone_number_id", "")

                contacts = value.get("contacts", [])
                profile_name = ""
                if contacts:
                    profile_name = contacts[0].get("profile", {}).get("name", "")

                messages = value.get("messages", [])
                statuses = value.get("statuses", [])

                # Incoming message
                if messages:
                    msg = messages[0]
                    from_number = msg.get("from", "")
                    msg_id = msg.get("id", "")
                    msg_type = msg.get("type", "text")
                    timestamp = msg.get("timestamp", "")

                    # Extract body based on message type
                    body = ""
                    if msg_type == "text":
                        body = msg.get("text", {}).get("body", "")
                    elif msg_type == "interactive":
                        interactive = msg.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            body = interactive.get("button_reply", {}).get("title", "")
                        elif interactive.get("type") == "list_reply":
                            body = interactive.get("list_reply", {}).get("title", "")
                    elif msg_type == "button":
                        body = msg.get("button", {}).get("text", "")

                    return {
                        "from_number": from_number,
                        "to_number": to_number,
                        "phone_number_id": phone_number_id,
                        "body": body.strip(),
                        "message_id": msg_id,
                        "message_type": msg_type,
                        "timestamp": timestamp,
                        "profile_name": profile_name,
                    }

                # Status update (delivery/read receipts)
                if statuses:
                    status = statuses[0]
                    return {
                        "from_number": "",
                        "to_number": "",
                        "phone_number_id": phone_number_id,
                        "body": "",
                        "message_id": status.get("id", ""),
                        "message_type": "status",
                        "timestamp": status.get("timestamp", ""),
                        "profile_name": "",
                        "status": status.get("status", ""),  # sent, delivered, read, failed
                    }

        return None
    except Exception as e:
        logger.error(f"Error parsing Meta webhook: {e}")
        return None


def _strip_whatsapp_prefix(number: str) -> str:
    """Strip 'whatsapp:' prefix if present."""
    if number.startswith("whatsapp:"):
        return number[len("whatsapp:"):]
    return number
