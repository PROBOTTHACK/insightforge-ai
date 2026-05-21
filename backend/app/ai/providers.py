import json
from typing import Any

import httpx

from app.core.config import get_settings


async def select_dashboard_plan(prompt: str, dataset_context: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    settings = get_settings()
    provider = settings.ai_provider.lower()

    try:
        if provider == "gemini" and settings.gemini_api_key:
            return await _gemini_plan(prompt, dataset_context, candidates)
        if provider == "huggingface" and settings.huggingface_api_key:
            return await _huggingface_plan(prompt, dataset_context, candidates)
    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return None


async def _gemini_plan(prompt: str, dataset_context: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    settings = get_settings()
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _planner_prompt(prompt, dataset_context, candidates)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_plan(text)


async def _huggingface_plan(prompt: str, dataset_context: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    settings = get_settings()
    payload = {
        "model": settings.huggingface_model,
        "provider": settings.huggingface_provider,
        "messages": [
            {
                "role": "system",
                "content": "You return only valid JSON. Do not include markdown.",
            },
            {
                "role": "user",
                "content": _planner_prompt(prompt, dataset_context, candidates),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }
    headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    return _parse_plan(text)


def _planner_prompt(prompt: str, dataset_context: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    return json.dumps(
        {
            "task": "Choose the best dashboard widgets for the user prompt.",
            "instructions": [
                "Return JSON only.",
                "Use only candidate widget indexes that are provided.",
                "Prefer 4 to 8 widgets.",
                "Keep KPI widgets first, then charts, then table if useful.",
            ],
            "required_shape": {
                "dashboardName": "short title",
                "widgetIndexes": [0, 1, 2],
            },
            "userPrompt": prompt,
            "dataset": dataset_context,
            "candidateWidgets": candidates,
        },
        default=str,
    )


def _parse_plan(text: str) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(text[start : end + 1])

    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("dashboardName"), str):
        return None
    if not isinstance(data.get("widgetIndexes"), list):
        return None
    return data
