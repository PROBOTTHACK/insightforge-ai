import json
from itertools import count
from typing import Any

import httpx

from app.core.config import get_settings

_provider_counter = count()


async def select_dashboard_plan(prompt: str, dataset_context: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    for provider in _provider_order():
        try:
            if provider == "gemini":
                return await _gemini_plan(prompt, dataset_context, candidates)
            if provider == "huggingface":
                return await _huggingface_plan(prompt, dataset_context, candidates)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return None


async def interpret_chart_insight(chart: dict[str, Any]) -> str | None:
    prompt = json.dumps(
        {
            "task": "Write one concise business insight for this chart.",
            "instructions": [
                "Return plain text only.",
                "Do not mention that you are an AI.",
                "Do not invent facts beyond the provided chart data.",
                "Keep it under 30 words.",
            ],
            "chart": {
                "title": chart.get("title"),
                "chartType": chart.get("chartType"),
                "xAxis": chart.get("xAxis"),
                "yAxis": chart.get("yAxis"),
                "aggregation": chart.get("aggregation"),
                "dataSample": chart.get("data", [])[:12],
                "localInsight": chart.get("insight"),
            },
        },
        default=str,
    )

    for provider in _provider_order():
        try:
            if provider == "gemini":
                return await _gemini_text(prompt)
            if provider == "huggingface":
                return await _huggingface_text(prompt)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return None


async def answer_dashboard_question(question: str, context: dict[str, Any]) -> dict[str, Any] | None:
    prompt = json.dumps(
        {
            "task": "Answer a dashboard question using only the provided retrieved context.",
            "instructions": [
                "Be direct and business-friendly.",
                "If selected widgets are provided, prioritize them.",
                "If the answer is not supported by context, say what information is missing.",
                "Do not invent values.",
                "Return JSON only in the requested shape.",
                "Keep answer under 120 words unless the user asks for detail.",
            ],
            "requiredJsonShape": {
                "answer": "string",
                "sources": ["retrieved source title"],
                "confidence": "low | medium | high",
            },
            "question": question,
            "retrievedContext": context,
        },
        default=str,
    )

    for provider in _provider_order():
        try:
            if provider == "gemini":
                answer = _parse_answer_json(await _gemini_text(prompt, response_mime_type="application/json"))
            elif provider == "huggingface":
                answer = _parse_answer_json(
                    await _huggingface_text(prompt, system="You return only valid JSON. Do not include markdown.")
                )
            else:
                answer = None
            if answer:
                answer["provider"] = provider
                return answer
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return None


def _provider_order() -> list[str]:
    settings = get_settings()
    available: list[str] = []
    if settings.gemini_api_key:
        available.append("gemini")
    if settings.huggingface_api_key:
        available.append("huggingface")

    provider = settings.ai_provider.lower()
    if provider == "local" or not available:
        return []
    if provider in {"gemini", "huggingface"}:
        preferred = [item for item in available if item == provider]
        fallback = [item for item in available if item != provider]
        return [*preferred, *fallback]

    strategy = settings.ai_provider_strategy.lower()
    if provider == "balanced" or strategy == "balanced":
        if len(available) <= 1:
            return available
        offset = next(_provider_counter) % len(available)
        return [*available[offset:], *available[:offset]]

    return available


async def _gemini_plan(prompt: str, dataset_context: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = await _gemini_text(_planner_prompt(prompt, dataset_context, candidates), response_mime_type="application/json")
    return _parse_plan(text)


async def _gemini_text(prompt: str, response_mime_type: str | None = None) -> str:
    settings = get_settings()
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
        },
    }
    if response_mime_type:
        payload["generationConfig"]["responseMimeType"] = response_mime_type
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _huggingface_plan(prompt: str, dataset_context: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = await _huggingface_text(_planner_prompt(prompt, dataset_context, candidates), system="You return only valid JSON. Do not include markdown.")
    return _parse_plan(text)


async def _huggingface_text(prompt: str, system: str = "You return concise plain text.") -> str:
    settings = get_settings()
    payload = {
        "model": settings.huggingface_model,
        "provider": settings.huggingface_provider,
        "messages": [
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": prompt,
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
    return response.json()["choices"][0]["message"]["content"].strip()


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


def _parse_answer_json(text: str) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(text[start : end + 1])

    if not isinstance(data, dict) or not isinstance(data.get("answer"), str):
        return None
    sources = data.get("sources")
    if not isinstance(sources, list):
        sources = []
    confidence = data.get("confidence")
    if confidence not in {"low", "medium", "high"}:
        confidence = "medium"
    return {"answer": data["answer"], "sources": [str(source) for source in sources], "confidence": confidence}
