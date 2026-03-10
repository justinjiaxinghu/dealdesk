# backend/app/api/v1/snapshots.py
"""Snapshot CRUD and restore routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_chat_message_repo,
    get_chat_session_repo,
    get_exploration_session_repo,
    get_snapshot_repo,
)
from app.api.schemas import (
    ChatSessionResponse,
    CreateSnapshotRequest,
    SnapshotResponse,
)
from app.domain.entities.chat import ChatMessage, ChatSession
from app.domain.entities.snapshot import Snapshot
from app.domain.value_objects.enums import ChatRole, ConnectorType
from app.infrastructure.persistence.chat_repo import (
    SqlAlchemyChatMessageRepository,
    SqlAlchemyChatSessionRepository,
)
from app.infrastructure.persistence.exploration_repo import (
    SqlAlchemyExplorationSessionRepository,
)
from app.infrastructure.persistence.snapshot_repo import (
    SqlAlchemySnapshotRepository,
)

router = APIRouter(tags=["snapshots"])


@router.post(
    "/explorations/{exploration_id}/snapshots",
    response_model=SnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    exploration_id: UUID,
    body: CreateSnapshotRequest,
    exploration_repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
    chat_session_repo: Annotated[
        SqlAlchemyChatSessionRepository,
        Depends(get_chat_session_repo),
    ],
    message_repo: Annotated[
        SqlAlchemyChatMessageRepository,
        Depends(get_chat_message_repo),
    ],
    snapshot_repo: Annotated[
        SqlAlchemySnapshotRepository,
        Depends(get_snapshot_repo),
    ],
) -> SnapshotResponse:
    exploration = await exploration_repo.get_by_id(exploration_id)
    if exploration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )

    # Serialize all sessions + messages into session_data JSON
    sessions = await chat_session_repo.get_by_exploration_id(exploration_id)
    session_data: list[dict] = []
    for sess in sessions:
        messages = await message_repo.get_by_session_id(sess.id)
        session_data.append({
            "title": sess.title,
            "connectors": [c.value for c in sess.connectors],
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                }
                for msg in messages
            ],
        })

    entity = Snapshot(
        name=body.name,
        deal_id=exploration.deal_id,
        session_data={"sessions": session_data},
    )
    created = await snapshot_repo.create(entity)
    return SnapshotResponse.model_validate(created)


@router.get("/snapshots", response_model=list[SnapshotResponse])
async def list_snapshots(
    snapshot_repo: Annotated[
        SqlAlchemySnapshotRepository,
        Depends(get_snapshot_repo),
    ],
) -> list[SnapshotResponse]:
    snapshots = await snapshot_repo.list_all()
    return [SnapshotResponse.model_validate(s) for s in snapshots]


@router.get(
    "/deals/{deal_id}/snapshots",
    response_model=list[SnapshotResponse],
)
async def list_deal_snapshots(
    deal_id: UUID,
    snapshot_repo: Annotated[
        SqlAlchemySnapshotRepository,
        Depends(get_snapshot_repo),
    ],
) -> list[SnapshotResponse]:
    snapshots = await snapshot_repo.list_by_deal_id(deal_id)
    return [SnapshotResponse.model_validate(s) for s in snapshots]


@router.get(
    "/snapshots/{snapshot_id}",
    response_model=SnapshotResponse,
)
async def get_snapshot(
    snapshot_id: UUID,
    snapshot_repo: Annotated[
        SqlAlchemySnapshotRepository,
        Depends(get_snapshot_repo),
    ],
) -> SnapshotResponse:
    entity = await snapshot_repo.get_by_id(snapshot_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )
    return SnapshotResponse.model_validate(entity)


@router.post(
    "/snapshots/{snapshot_id}/restore",
    response_model=list[ChatSessionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def restore_snapshot(
    snapshot_id: UUID,
    exploration_id: UUID,
    snapshot_repo: Annotated[
        SqlAlchemySnapshotRepository,
        Depends(get_snapshot_repo),
    ],
    exploration_repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
    chat_session_repo: Annotated[
        SqlAlchemyChatSessionRepository,
        Depends(get_chat_session_repo),
    ],
    message_repo: Annotated[
        SqlAlchemyChatMessageRepository,
        Depends(get_chat_message_repo),
    ],
) -> list[ChatSessionResponse]:
    snapshot = await snapshot_repo.get_by_id(snapshot_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )

    exploration = await exploration_repo.get_by_id(exploration_id)
    if exploration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )

    # Hydrate sessions and messages from snapshot JSON
    restored_sessions: list[ChatSessionResponse] = []
    for sess_data in snapshot.session_data.get("sessions", []):
        connectors = [
            ConnectorType(c) for c in sess_data.get("connectors", [])
        ]
        chat_session = ChatSession(
            exploration_session_id=exploration_id,
            title=sess_data.get("title", "Restored Session"),
            connectors=connectors,
        )
        chat_session = await chat_session_repo.create(chat_session)

        # Restore messages
        messages_data = sess_data.get("messages", [])
        for msg_data in messages_data:
            msg = ChatMessage(
                session_id=chat_session.id,
                role=ChatRole(msg_data["role"]),
                content=msg_data.get("content", ""),
                tool_calls=msg_data.get("tool_calls"),
            )
            await message_repo.create(msg)

        restored_sessions.append(
            ChatSessionResponse.model_validate(chat_session)
        )

    return restored_sessions


@router.delete(
    "/snapshots/{snapshot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_snapshot(
    snapshot_id: UUID,
    snapshot_repo: Annotated[
        SqlAlchemySnapshotRepository,
        Depends(get_snapshot_repo),
    ],
) -> None:
    entity = await snapshot_repo.get_by_id(snapshot_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )
    await snapshot_repo.delete(snapshot_id)
