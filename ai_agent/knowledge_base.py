"""Official-source filtering and lightweight multilingual retrieval (RAG)."""
from __future__ import annotations

from datetime import date
import json
import re
from pathlib import Path
from urllib.parse import urlparse

# Keep this allowlist narrow. It covers the official sources currently curated
# for India and prevents an arbitrary HTTPS URL being presented as government law.
OFFICIAL_HOSTS = ("indiacode.nic.in", "nalsa.gov.in", "cybercrime.gov.in", "wcd.gov.in")
MAX_SOURCE_AGE_DAYS = 365
STOP_WORDS = {
    "a", "an", "the", "is", "are", "am", "i", "me", "my", "what", "how", "can", "could", "would", "do", "does", "about", "for", "to", "of", "in", "on", "and", "or", "please", "tell", "want", "know", "help", "me", "my", "kya", "hai", "hain", "ka", "ki", "ke", "ko", "mein", "me", "mujhe", "batao", "karo", "sakti", "sakta", "mere", "meri", "mera", "aur", "ya", "kaise", "kahan", "क्या", "है", "हैं", "में", "मुझे", "मेरे", "मेरी", "का", "की", "के", "को", "और", "क्या", "कैसे", "कहाँ", "बताएं", "बताओ", "मेरा", "मेरी", "मुझे", "मदद", "किया", "गया", "रहा", "रही", "रहे", "जा", "जाता", "जाती", "जाते", "कर", "हुआ", "हुई", "हुए", "अधिकार",
}


def _is_official_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    host = (parsed.hostname or "").casefold()
    return parsed.scheme == "https" and any(host == domain or host.endswith("." + domain) for domain in OFFICIAL_HOSTS)


def is_official_source_url(value: object) -> bool:
    """Public validator used by admin CRUD for current official domains."""
    return _is_official_url(value)


def _source_records(path: Path) -> list[dict]:
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError):
        return []
    return records if isinstance(records, list) else []


def _validated_records(records: list[dict], *, jurisdiction: str | None) -> list[dict]:
    if not jurisdiction:
        return []
    results = []
    for item in records:
        if not isinstance(item, dict) or item.get("verification_status") != "verified":
            continue
        required = ("title", "summary", "source_name", "jurisdiction", "source_url", "reviewed_at")
        if not all(item.get(field) for field in required) or not _is_official_url(item.get("source_url")):
            continue
        try:
            reviewed_at = date.fromisoformat(item["reviewed_at"])
            age_in_days = (date.today() - reviewed_at).days
            if age_in_days < 0 or age_in_days > MAX_SOURCE_AGE_DAYS:
                continue
        except (TypeError, ValueError):
            continue
        if item["jurisdiction"].casefold() != jurisdiction.casefold():
            continue
        results.append(item)
    return results


def _tokens(value: object) -> set[str]:
    tokens = {
        token.casefold()
        for token in re.findall(r"[\w\u0900-\u097f]+", str(value or ""), flags=re.UNICODE)
        if len(token) > 1 and token.casefold() not in STOP_WORDS
    }
    if tokens & {"work", "office", "manager", "boss", "काम", "कार्यालय"}:
        tokens.add("workplace")
    return tokens


def _localized_content(item: dict, language: str) -> str:
    content = item.get("content", {})
    if isinstance(content, dict):
        return str(content.get(language) or content.get("en") or item["summary"])
    return str(item["summary"])


def _score(item: dict, query: str, category: str | None) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    title_tokens = _tokens(item.get("title"))
    keyword_tokens = _tokens(item.get("keywords", [])) | _tokens(item.get("retrieval_terms", []))
    content = item.get("content", {})
    if isinstance(content, dict):
        content_text = " ".join(str(value) for value in content.values())
    else:
        content_text = str(item.get("summary", ""))
    content_tokens = _tokens(content_text)
    keyword_matches = query_tokens & keyword_tokens
    # Generic terms such as "harassment" occur in many records. A single
    # generic match should not outrank a topic-specific source.
    generic_terms = {
        "harassment", "complaint", "report", "rights", "safety", "women", "woman",
        "crime", "online", "legal", "law", "laws", "information", "support",
        "help", "apply", "applies", "applicable", "know", "tell", "question",
    }
    specific_keyword_matches = keyword_matches - generic_terms
    specific_title_matches = (query_tokens & title_tokens) - generic_terms
    specific_content_matches = (query_tokens & content_tokens) - generic_terms
    score = 4.0 * len(specific_keyword_matches) + 0.75 * len(keyword_matches & generic_terms)
    score += 3.0 * len(specific_title_matches) + 0.75 * len(specific_content_matches)
    categories = {str(value).casefold() for value in item.get("categories", [])}
    specific_evidence = bool(specific_keyword_matches or specific_title_matches or specific_content_matches)
    if specific_evidence and category and category.casefold() not in {"general_query", "harassment"} and category.casefold() in categories:
        score += 2.5
    return score


def retrieve_rights(
    records: list[dict], *, question: str, category: str | None = None,
    jurisdiction: str | None = None, language: str = "en", limit: int = 3,
) -> list[dict]:
    """Retrieve only reviewed official entries relevant to a user's question."""
    verified = _validated_records(records, jurisdiction=jurisdiction)
    if not question.strip():
        if category:
            verified = [item for item in verified if category in item.get("categories", [])]
        return [
            {
                "id": item.get("id"), "title": item["title"],
                "summary": _localized_content(item, language), "content": _localized_content(item, language),
                "topic": item.get("topic", "general"), "sourceName": item["source_name"],
                "sourceType": item.get("source_type", "official_government"),
                "jurisdiction": item["jurisdiction"], "reviewedAt": item["reviewed_at"],
                "url": item["source_url"], "categories": item.get("categories", []),
            }
            for item in verified[:limit]
        ]
    ranked = [(_score(item, question, category), item) for item in verified]
    ranked = [(score, item) for score, item in ranked if score >= 2.0]
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    output = []
    for score, item in ranked[:limit]:
        output.append({
            "id": item.get("id"),
            "title": item["title"],
            "summary": _localized_content(item, language),
            "content": _localized_content(item, language),
            "topic": item.get("topic", item.get("categories", ["general"])[0]),
            "sourceName": item["source_name"],
            "sourceType": item.get("source_type", "official_government"),
            "jurisdiction": item["jurisdiction"],
            "reviewedAt": item["reviewed_at"],
            "url": item["source_url"],
            "categories": item.get("categories", []),
            "relevanceScore": round(score, 2),
        })
    return output


def get_verified_rights(
    path: Path, *, category: str | None = None, jurisdiction: str | None = None,
    query: str = "", language: str = "en", limit: int = 20,
) -> list[dict]:
    records = _source_records(path)
    return retrieve_rights(
        records, question=query, category=category, jurisdiction=jurisdiction,
        language=language, limit=limit,
    )
