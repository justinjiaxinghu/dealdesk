# backend/app/api/v1/chat.py
"""Chat session and message routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_chat_message_repo,
    get_chat_session_repo,
    get_chat_service,
)
from app.api.schemas import (
    ChatMessageResponse,
    ChatSessionResponse,
    CreateChatSessionRequest,
    SendMessageRequest,
    UpdateChatSessionRequest,
)
from app.domain.entities.chat import ChatSession
from app.domain.value_objects.enums import ConnectorType
from app.infrastructure.persistence.chat_repo import (
    SqlAlchemyChatMessageRepository,
    SqlAlchemyChatSessionRepository,
)
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


def _parse_connectors(raw: list[str]) -> list[ConnectorType]:
    """Parse connector strings, skipping unknown providers (e.g. onedrive, box)."""
    result = []
    for c in raw:
        try:
            result.append(ConnectorType(c))
        except ValueError:
            # File connector providers (onedrive, box, etc.) are not ConnectorType members —
            # they're handled separately by the connector service search.
            pass
    return result


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------


@router.post(
    "/explorations/{exploration_id}/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_session(
    exploration_id: UUID,
    body: CreateChatSessionRequest,
    repo: Annotated[
        SqlAlchemyChatSessionRepository,
        Depends(get_chat_session_repo),
    ],
) -> ChatSessionResponse:
    connectors = _parse_connectors(body.connectors)
    entity = ChatSession(
        exploration_session_id=exploration_id,
        title=body.title,
        connectors=connectors,
    )
    created = await repo.create(entity)
    return ChatSessionResponse.model_validate(created)


@router.get(
    "/explorations/{exploration_id}/sessions",
    response_model=list[ChatSessionResponse],
)
async def list_chat_sessions(
    exploration_id: UUID,
    repo: Annotated[
        SqlAlchemyChatSessionRepository,
        Depends(get_chat_session_repo),
    ],
) -> list[ChatSessionResponse]:
    sessions = await repo.get_by_exploration_id(exploration_id)
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get(
    "/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
)
async def get_chat_session(
    session_id: UUID,
    repo: Annotated[
        SqlAlchemyChatSessionRepository,
        Depends(get_chat_session_repo),
    ],
) -> ChatSessionResponse:
    entity = await repo.get_by_id(session_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ChatSession {session_id} not found",
        )
    return ChatSessionResponse.model_validate(entity)


@router.patch(
    "/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
)
async def update_chat_session(
    session_id: UUID,
    body: UpdateChatSessionRequest,
    repo: Annotated[
        SqlAlchemyChatSessionRepository,
        Depends(get_chat_session_repo),
    ],
) -> ChatSessionResponse:
    entity = await repo.get_by_id(session_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ChatSession {session_id} not found",
        )
    if body.title is not None:
        entity.title = body.title
        entity.updated_at = datetime.utcnow()
    updated = await repo.update(entity)
    return ChatSessionResponse.model_validate(updated)


@router.delete(
    "/chat/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat_session(
    session_id: UUID,
    repo: Annotated[
        SqlAlchemyChatSessionRepository,
        Depends(get_chat_session_repo),
    ],
) -> None:
    entity = await repo.get_by_id(session_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ChatSession {session_id} not found",
        )
    await repo.delete(session_id)


# ---------------------------------------------------------------------------
# Chat Messages
# ---------------------------------------------------------------------------


@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def list_messages(
    session_id: UUID,
    message_repo: Annotated[
        SqlAlchemyChatMessageRepository,
        Depends(get_chat_message_repo),
    ],
) -> list[ChatMessageResponse]:
    messages = await message_repo.get_by_session_id(session_id)
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.post(
    "/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    session_id: UUID,
    body: SendMessageRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> list[ChatMessageResponse]:
    connectors = _parse_connectors(body.connectors)
    try:
        new_messages = await service.send_message(
            session_id=session_id,
            user_content=body.content,
            connectors=connectors,
            raw_connectors=body.connectors,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    return [ChatMessageResponse.model_validate(m) for m in new_messages]
