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


async def interpret_chart_insight(chart: dict[str, Any]) -> str | None:
    settings = get_settings()
    provider = settings.ai_provider.lower()
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

    try:
        if provider == "gemini" and settings.gemini_api_key:
            return await _gemini_text(prompt)
        if provider == "huggingface" and settings.huggingface_api_key:
            return await _huggingface_text(prompt)
    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return None


async def answer_dashboard_question(question: str, context: dict[str, Any]) -> str | None:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    prompt = json.dumps(
        {
            "task": "Answer a dashboard question using only the provided retrieved context.",
            "instructions": [
                "Be direct and business-friendly.",
                "If selected widgets are provided, prioritize them.",
                "If the answer is not supported by context, say what information is missing.",
                "Do not invent values.",
                "Keep the answer under 120 words unless the user asks for detail.",
            ],
            "question": question,
            "retrievedContext": context,
        },
        default=str,
    )

    try:
        if provider == "gemini" and settings.gemini_api_key:
            return await _gemini_text(prompt)
        if provider == "huggingface" and settings.huggingface_api_key:
            return await _huggingface_text(prompt)
    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return None


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
