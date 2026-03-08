from __future__ import annotations

import json
import logging
from uuid import UUID

from openai import AsyncOpenAI

from app.domain.entities.chat import ChatMessage, ChatSession
from app.domain.entities.deal import Deal
from app.domain.entities.exploration import ExplorationSession
from app.domain.interfaces.providers import MarketSearchProvider
from app.domain.interfaces.repositories import (
    ChatMessageRepository,
    ChatSessionRepository,
    DealRepository,
    ExplorationSessionRepository,
    ExtractedFieldRepository,
    AssumptionRepository,
    AssumptionSetRepository,
    FieldValidationRepository,
)
from app.domain.value_objects.enums import ChatRole, ConnectorType

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real estate market data, property listings, comps, supply pipeline, and market trends.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

SYSTEM_PROMPT_DEAL = """You are a real estate market intelligence assistant analyzing a specific deal.

Deal Context:
{deal_context}

All research should be contextualized against this subject property. When returning property results, always note how they compare to the subject deal. Use the web_search tool to find market data, comparable properties, and validate assumptions.

When presenting properties you find, always include: address, property type, key financial metrics (cap rate, rent/sqft, sale price, NOI) where available, and how they compare to the subject deal.

Respond in markdown format."""

SYSTEM_PROMPT_FREE = """You are a real estate market intelligence assistant.

The user is exploring the market without a specific deal. Help them research properties, find comps, understand market trends, and discover opportunities. Use the web_search tool to find relevant data.

When presenting properties you find, always include: address, property type, key financial metrics (cap rate, rent/sqft, sale price, NOI) where available.

Respond in markdown format."""


class ChatService:
    def __init__(
        self,
        exploration_repo: ExplorationSessionRepository,
        chat_session_repo: ChatSessionRepository,
        chat_message_repo: ChatMessageRepository,
        deal_repo: DealRepository,
        extracted_field_repo: ExtractedFieldRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        validation_repo: FieldValidationRepository,
        market_search_provider: MarketSearchProvider,
        openai_api_key: str,
        openai_model: str,
    ) -> None:
        self._exploration_repo = exploration_repo
        self._chat_session_repo = chat_session_repo
        self._chat_message_repo = chat_message_repo
        self._deal_repo = deal_repo
        self._extracted_field_repo = extracted_field_repo
        self._assumption_set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._validation_repo = validation_repo
        self._search_provider = market_search_provider
        self._openai = AsyncOpenAI(api_key=openai_api_key)
        self._model = openai_model

    async def _build_deal_context(self, deal: Deal) -> str:
        lines = [
            f"Name: {deal.name}",
            f"Property Type: {deal.property_type.value}",
            f"Location: {deal.address}, {deal.city}, {deal.state}",
        ]
        if deal.square_feet:
            lines.append(f"Square Feet: {deal.square_feet:,.0f}")

        sets = await self._assumption_set_repo.get_by_deal_id(deal.id)
        if sets:
            assumptions = await self._assumption_repo.get_by_set_id(sets[0].id)
            if assumptions:
                lines.append("\nKey Assumptions:")
                for a in assumptions[:10]:
                    lines.append(f"  {a.key}: {a.value_number} {a.unit or ''}")

        return "\n".join(lines)

    async def send_message(
        self,
        session_id: UUID,
        user_content: str,
        connectors: list[ConnectorType],
    ) -> list[ChatMessage]:
        chat_session = await self._chat_session_repo.get_by_id(session_id)
        if chat_session is None:
            raise ValueError(f"ChatSession {session_id} not found")

        exploration = await self._exploration_repo.get_by_id(
            chat_session.exploration_session_id
        )
        if exploration is None:
            raise ValueError("ExplorationSession not found")

        # Persist user message
        user_msg = ChatMessage(
            session_id=session_id,
            role=ChatRole.USER,
            content=user_content,
        )
        user_msg = await self._chat_message_repo.create(user_msg)

        # Build system prompt
        deal: Deal | None = None
        if exploration.deal_id:
            deal = await self._deal_repo.get_by_id(exploration.deal_id)

        if deal:
            deal_context = await self._build_deal_context(deal)
            system_prompt = SYSTEM_PROMPT_DEAL.format(deal_context=deal_context)
        else:
            system_prompt = SYSTEM_PROMPT_FREE

        # Load conversation history
        history = await self._chat_message_repo.get_by_session_id(session_id)
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        for msg in history:
            if msg.role == ChatRole.TOOL:
                messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": (msg.tool_calls or [{}])[0].get("id", ""),
                })
            elif msg.role == ChatRole.ASSISTANT and msg.tool_calls:
                # Ensure each tool_call has "type": "function" (required by OpenAI API)
                tool_calls = [
                    {**tc, "type": tc.get("type", "function")}
                    for tc in msg.tool_calls
                ]
                messages.append({
                    "role": "assistant",
                    "content": msg.content or None,
                    "tool_calls": tool_calls,
                })
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        # Agentic loop
        new_messages: list[ChatMessage] = [user_msg]
        for _ in range(MAX_TOOL_ROUNDS):
            response = await self._openai.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
            )
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                # Persist assistant message with tool calls
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role=ChatRole.ASSISTANT,
                    content=choice.message.content or "",
                    tool_calls=tool_calls_data,
                )
                assistant_msg = await self._chat_message_repo.create(assistant_msg)
                new_messages.append(assistant_msg)
                messages.append({
                    "role": "assistant",
                    "content": choice.message.content or None,
                    "tool_calls": tool_calls_data,
                })

                # Execute each tool call
                for tc in choice.message.tool_calls:
                    args = json.loads(tc.function.arguments)
                    if tc.function.name == "web_search":
                        results = await self._search_provider.search(
                            query=args["query"],
                            connectors=connectors,
                            deal=deal,
                        )
                        tool_result = json.dumps(
                            [
                                {
                                    "title": r.title,
                                    "url": r.url,
                                    "snippet": r.snippet,
                                }
                                for r in results
                            ],
                            indent=2,
                        )
                    else:
                        tool_result = json.dumps(
                            {"error": f"Unknown tool: {tc.function.name}"}
                        )

                    tool_msg = ChatMessage(
                        session_id=session_id,
                        role=ChatRole.TOOL,
                        content=tool_result,
                        tool_calls=[{"id": tc.id}],
                    )
                    tool_msg = await self._chat_message_repo.create(tool_msg)
                    new_messages.append(tool_msg)
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tc.id,
                    })
            else:
                # Final response
                final_msg = ChatMessage(
                    session_id=session_id,
                    role=ChatRole.ASSISTANT,
                    content=choice.message.content or "",
                )
                final_msg = await self._chat_message_repo.create(final_msg)
                new_messages.append(final_msg)
                break

        return new_messages
