"""LLM provider abstraction for receipt extraction.

Supports multiple providers: Ollama (local), OpenAI, Google Gemini,
Anthropic Claude, and Groq. Each provider sends receipt images/text
to its respective API and returns structured JSON.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from receipt_sorter import CATEGORIES, parse_receipt_json

# ---------------------------------------------------------------------------
# Shared prompt
# ---------------------------------------------------------------------------

RECEIPT_PROMPT = (
    "Extract the purchase details from this receipt or invoice. Return only one JSON object with "
    'exactly these keys: "vendor", "date", "amount", "currency", "category", "description". '
    "Use an ISO date (YYYY-MM-DD), a plain non-negative numeric amount, and a three-letter "
    "currency code. Use an empty string when a value is unreadable. Choose category from "
    f"{', '.join(CATEGORIES)}. Never guess missing values. Keep description brief."
)

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, dict[str, Any]] = {
    "Ollama (Local)": {
        "models": ["gemma3:4b", "llava:7b", "llava:13b", "bakllava", "moondream"],
        "needs_api_key": False,
        "description": "Free, private, runs on your machine. Requires Ollama installed.",
    },
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o4-mini"],
        "needs_api_key": True,
        "env_key": "OPENAI_API_KEY",
        "description": "Powerful cloud vision models. Requires an OpenAI API key.",
    },
    "Google Gemini": {
        "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "needs_api_key": True,
        "env_key": "GOOGLE_API_KEY",
        "description": "Fast and affordable. Requires a Google AI API key.",
    },
    "Anthropic Claude": {
        "models": ["claude-sonnet-4-20250514", "claude-haiku-35-20241022"],
        "needs_api_key": True,
        "env_key": "ANTHROPIC_API_KEY",
        "description": "Excellent reasoning. Requires an Anthropic API key.",
    },
    "Groq": {
        "models": ["llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct"],
        "needs_api_key": True,
        "env_key": "GROQ_API_KEY",
        "description": "Ultra-fast inference. Requires a Groq API key.",
    },
}


def _mime_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".gif": "image/gif",
    }.get(suffix, "image/png")


def _prepare_image_data(file_name: str, file_bytes: bytes) -> tuple[list[str], str]:
    """Return (base64 images list, pdf text) from raw file bytes."""
    suffix = Path(file_name).suffix.lower()
    images: list[str] = []
    pdf_text = ""

    if suffix == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError(
                "PDF support requires PyMuPDF. Install requirements.txt and retry."
            ) from exc
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pdf_text = "\n".join(page.get_text() for page in doc).strip()
            if not pdf_text and len(doc):
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                images.append(base64.b64encode(pix.tobytes("png")).decode("ascii"))
            doc.close()
        except Exception as exc:
            raise ValueError(f"Could not read PDF: {exc}") from exc
    else:
        images.append(base64.b64encode(file_bytes).decode("ascii"))

    return images, pdf_text


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------

OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


def _extract_ollama(
    file_name: str, file_bytes: bytes, model: str, _api_key: str
) -> dict[str, str]:
    images, pdf_text = _prepare_image_data(file_name, file_bytes)
    prompt = RECEIPT_PROMPT + f"\n\nPDF text, if available:\n{pdf_text[:12000]}"

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": images}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 128},
    }
    request = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(
            f"Could not reach local Ollama at {OLLAMA_CHAT_URL}: {reason}. "
            f"Start Ollama and pull the model '{model}'."
        ) from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama did not return a valid response: {exc}") from exc

    try:
        return parse_receipt_json(data["message"]["content"])
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Ollama returned a response without message content.") from exc


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------


def _extract_openai(
    file_name: str, file_bytes: bytes, model: str, api_key: str
) -> dict[str, str]:
    images, pdf_text = _prepare_image_data(file_name, file_bytes)
    mime = _mime_type(file_name)

    content: list[dict[str, Any]] = []
    prompt_text = RECEIPT_PROMPT
    if pdf_text:
        prompt_text += f"\n\nPDF text:\n{pdf_text[:12000]}"
    content.append({"type": "text", "text": prompt_text})

    for img_b64 in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{img_b64}", "detail": "low"},
        })

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "max_tokens": 256,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach OpenAI API: {exc.reason}") from exc

    try:
        return parse_receipt_json(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected OpenAI response structure: {exc}") from exc


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------


def _extract_gemini(
    file_name: str, file_bytes: bytes, model: str, api_key: str
) -> dict[str, str]:
    images, pdf_text = _prepare_image_data(file_name, file_bytes)
    mime = _mime_type(file_name)

    parts: list[dict[str, Any]] = []
    prompt_text = RECEIPT_PROMPT
    if pdf_text:
        prompt_text += f"\n\nPDF text:\n{pdf_text[:12000]}"
    parts.append({"text": prompt_text})

    for img_b64 in images:
        parts.append({"inline_data": {"mime_type": mime, "data": img_b64}})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 256,
            "responseMimeType": "application/json",
        },
    }
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Gemini API: {exc.reason}") from exc

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return parse_receipt_json(text)
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini response structure: {exc}") from exc


# ---------------------------------------------------------------------------
# Anthropic Claude
# ---------------------------------------------------------------------------


def _extract_anthropic(
    file_name: str, file_bytes: bytes, model: str, api_key: str
) -> dict[str, str]:
    images, pdf_text = _prepare_image_data(file_name, file_bytes)
    mime = _mime_type(file_name)

    content: list[dict[str, Any]] = []
    for img_b64 in images:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": mime, "data": img_b64},
        })

    prompt_text = RECEIPT_PROMPT
    if pdf_text:
        prompt_text += f"\n\nPDF text:\n{pdf_text[:12000]}"
    prompt_text += "\n\nRespond with ONLY the JSON object, no other text."
    content.append({"type": "text", "text": prompt_text})

    payload = {
        "model": model,
        "max_tokens": 256,
        "temperature": 0,
        "messages": [{"role": "user", "content": content}],
    }
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Anthropic API: {exc.reason}") from exc

    try:
        text = data["content"][0]["text"]
        return parse_receipt_json(text)
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Anthropic response structure: {exc}") from exc


# ---------------------------------------------------------------------------
# Groq
# ---------------------------------------------------------------------------


def _extract_groq(
    file_name: str, file_bytes: bytes, model: str, api_key: str
) -> dict[str, str]:
    images, pdf_text = _prepare_image_data(file_name, file_bytes)
    mime = _mime_type(file_name)

    content: list[dict[str, Any]] = []
    prompt_text = RECEIPT_PROMPT
    if pdf_text:
        prompt_text += f"\n\nPDF text:\n{pdf_text[:12000]}"
    content.append({"type": "text", "text": prompt_text})

    for img_b64 in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{img_b64}"},
        })

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "max_tokens": 256,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Groq API: {exc.reason}") from exc

    try:
        return parse_receipt_json(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Groq response structure: {exc}") from exc


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_EXTRACTORS = {
    "Ollama (Local)": _extract_ollama,
    "OpenAI": _extract_openai,
    "Google Gemini": _extract_gemini,
    "Anthropic Claude": _extract_anthropic,
    "Groq": _extract_groq,
}


def extract_receipt_llm(
    provider: str,
    file_name: str,
    file_bytes: bytes,
    model: str,
    api_key: str = "",
) -> dict[str, str]:
    """Extract receipt fields using the selected LLM provider."""
    extractor = _EXTRACTORS.get(provider)
    if extractor is None:
        raise ValueError(f"Unknown provider: {provider}")
    return extractor(file_name, file_bytes, model, api_key)
