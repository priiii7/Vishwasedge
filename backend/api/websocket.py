"""Real-time streaming responses via Server-Sent Events (SSE).

EventSource can't set Authorization headers, so the stream endpoint accepts
the JWT/API key as a query parameter instead.
"""

import json

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from backend.agents.orchestrator import QueryOptions, handle_query
from backend.core.config import get_settings
from backend.core.security import decode_access_token

stream_router = APIRouter(prefix="/api/v1", tags=["stream"])


def _authorize(token: str | None, api_key: str | None) -> None:
    settings = get_settings()
    if api_key and api_key == settings.default_api_key:
        return
    if token and decode_access_token(token) is not None:
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid credentials")


def _sse_event(event_type: str, content: object) -> str:
    return f"data: {json.dumps({'type': event_type, 'content': content})}\n\n"


async def _event_generator(query_text: str, context: dict | None):
    result = await handle_query(query_text, context, QueryOptions(include_explanation=True))

    for word in result.response_text.split(" "):
        yield _sse_event("token", word + " ")

    if result.explanation:
        yield _sse_event("explanation", result.explanation)

    yield _sse_event(
        "done",
        {
            "confidence": result.confidence,
            "tier_used": result.tier_used,
            "latency_ms": result.latency_ms,
        },
    )


@stream_router.get("/stream")
async def stream(
    query: str = Query(...),
    context: str = Query(default="{}"),
    token: str | None = Query(default=None),
    api_key: str | None = Query(default=None, alias="apiKey"),
) -> StreamingResponse:
    _authorize(token, api_key)
    try:
        parsed_context = json.loads(context) if context else {}
    except json.JSONDecodeError:
        parsed_context = {}

    return StreamingResponse(
        _event_generator(query, parsed_context),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
