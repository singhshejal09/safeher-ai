"""Request and response types used by the REST endpoints."""
from __future__ import annotations

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def clean_plain_text(value: str) -> str:
    """Normalize user text; keep it as text rather than interpreting HTML/markup."""
    value = unicodedata.normalize("NFC", value)
    value = "".join(char for char in value if char in "\n\t" or unicodedata.category(char) != "Cc")
    return value.strip()


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatMessage(StrictRequest):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        value = clean_plain_text(value)
        if not value:
            raise ValueError("Message content must not be blank.")
        return value


class TextRequest(StrictRequest):
    text: str = Field(min_length=1, max_length=5000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = clean_plain_text(value)
        if not value:
            raise ValueError("Text must contain non-whitespace characters.")
        return value


class ChatRequest(StrictRequest):
    message: str = Field(min_length=1, max_length=5000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=30)
    jurisdiction: str | None = Field(default=None, max_length=120)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = clean_plain_text(value)
        if not value:
            raise ValueError("Message must contain non-whitespace characters.")
        return value


class NearbyRequest(StrictRequest):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    radius_km: float = Field(default=30, gt=0, le=100, allow_inf_nan=False)


class ComplaintRequest(TextRequest):
    preferred_language: str = Field(default="en", pattern="^(en|hi|hinglish)$")


class SupportResourceRecord(StrictRequest):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1200)
    category: str = Field(default="support", min_length=1, max_length=80)
    jurisdiction: str = Field(min_length=1, max_length=160)
    source_name: str = Field(min_length=1, max_length=180)
    source_url: str = Field(min_length=1, max_length=1000)
    reviewed_at: str = Field(min_length=10, max_length=10)
    verification_status: Literal["pending", "verified", "unverified"] = "pending"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    contact_number: str | None = Field(default=None, max_length=40)
    contact_label: str = Field(default="Call verified contact", max_length=100)
    coverage_radius_km: float | None = Field(default=None, ge=0, le=20000)


class RightsRecord(StrictRequest):
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1, max_length=4000)
    categories: list[str] = Field(default_factory=list, max_length=20)
    topic: str = Field(default="general", max_length=120)
    keywords: list[str] = Field(default_factory=list, max_length=80)
    content: dict[str, str] = Field(default_factory=dict)
    source_type: Literal["official_legislation", "official_government_information", "official_government_service"] = "official_government_information"
    jurisdiction: str = Field(min_length=1, max_length=160)
    source_name: str = Field(min_length=1, max_length=180)
    source_url: str = Field(min_length=1, max_length=1000)
    reviewed_at: str = Field(min_length=10, max_length=10)
    verification_status: Literal["pending", "verified", "unverified"] = "pending"

    @field_validator("content")
    @classmethod
    def content_keys_and_lengths_are_limited(cls, value: dict[str, str]) -> dict[str, str]:
        allowed_languages = {"en", "hi", "hinglish"}
        if set(value) - allowed_languages:
            raise ValueError("content may only use en, hi, and hinglish keys.")
        if any(len(text) > 6000 for text in value.values()):
            raise ValueError("Each localized content value must be at most 6000 characters.")
        return value


class ComplaintCategoryRecord(StrictRequest):
    label: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    active: bool = True


