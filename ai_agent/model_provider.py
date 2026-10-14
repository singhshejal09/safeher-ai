"""Swappable response-model adapters. Secrets are read from environment only."""
from __future__ import annotations

import asyncio
import json
from typing import Protocol
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class ModelProvider(Protocol):
    async def generate(self, *, message: str, language: str, category: str, history: list[dict[str, str]]) -> str: ...


class DemoModelProvider:
    """A no-secret scripted provider for local development and viva demos."""

    async def generate(self, *, message: str, language: str, category: str, history: list[dict[str, str]]) -> str:
        if language == "hi":
            return "मैं सुन रही हूँ। आपको अभी सब कुछ तय करने की ज़रूरत नहीं है। हम एक छोटा अगला कदम साथ सोच सकते हैं।"
        if language == "hinglish":
            return "Main sun rahi hoon. Aapko abhi sab decide karne ki zaroorat nahi. Hum ek chhota next step saath soch sakte hain."
        return "Thank you for telling me. You deserve support, and you can choose what happens next."


class RemoteJsonModelProvider:
    """Generic model gateway adapter expecting JSON input and {\"reply\": ...} output."""

    def __init__(self, url: str, api_key: str, model_name: str) -> None:
        if not url or not api_key or not model_name:
            raise ValueError("AI_API_URL, AI_API_KEY, and AI_MODEL_NAME are required for remote mode.")
        parsed = urlsplit(url)
        local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not local_http:
            raise ValueError("AI_API_URL must use HTTPS (HTTP is allowed only for localhost development).")
        if not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("AI_API_URL must be a valid endpoint without embedded credentials.")
        self.url = url
        self.api_key = api_key
        self.model_name = model_name

    async def generate(self, *, message: str, language: str, category: str, history: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model_name,
            "message": message,
            "language": language,
            "situation_category": category,
            "history": history[-10:],
            "system_instructions": (
                "Be supportive and non-judgmental. Give general safety guidance only. "
                "Do not make legal conclusions, invent laws or emergency numbers, or claim to contact services. "
                "Use only separately supplied verified rights sources for legal information."
            ),
        }
        def send_request() -> dict:
            request = Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            # Do not follow redirects: credentials and user text must only go
            # to the configured endpoint, never to a redirect destination.
            opener = build_opener(_NoRedirectHandler())
            with opener.open(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))

        result = await asyncio.to_thread(send_request)
        reply = result.get("reply") if isinstance(result, dict) else None
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("Configured model endpoint must return a non-empty 'reply' string.")
        return reply.strip()
