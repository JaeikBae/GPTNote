"""Service to orchestrate GPT-like assistant responses."""

from __future__ import annotations

import textwrap
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import get_settings
from app.repositories import MemoryRepository
from app.schemas import AssistantChatRequest, AssistantChatResponse


class AssistantService:
    """Generates assistant responses, optionally using OpenAI."""

    def __init__(self, session: Session):
        self.session = session
        self.memory_repo = MemoryRepository(session)
        self.settings = get_settings()
        self._client: OpenAI | None = None

    def _client_instance(self) -> OpenAI:
        if not self.settings.openai_api_key:
            raise RuntimeError("OpenAI API key is not configured")
        if self._client is None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def _collect_memories(self, memory_ids: list) -> tuple[list[Any], list[str]]:
        records = []
        snippets: list[str] = []
        for memory_id in memory_ids:
            memory = self.memory_repo.get(memory_id)
            if not memory:
                continue
            records.append(memory)
            snippet = textwrap.dedent(
                f"""
                제목: {memory.title}
                내용: {memory.content}
                태그: {', '.join(memory.tags) if memory.tags else '없음'}
                """
            ).strip()
            snippets.append(snippet)
        return records, snippets

    def _build_prompt(self, message: str, snippets: list[str]) -> list[dict[str, str]]:
        system_prompt = (
            "You are MindDock, an AI assistant that helps organize and synthesize "
            "captured memories, tasks, and ideas for the user."
        )
        prompt: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        if snippets:
            memories_context = "\n\n".join(snippets)
            prompt.append(
                {
                    "role": "system",
                    "content": (
                        "Here are relevant memories captured by the user:\n"
                        f"{memories_context}"
                    ),
                }
            )
        prompt.append({"role": "user", "content": message})
        return prompt

    def chat(self, payload: AssistantChatRequest) -> AssistantChatResponse:
        memory_ids = payload.memory_ids or []
        memory_records, snippets = self._collect_memories(memory_ids)

        if self.settings.openai_api_key:
            client = self._client_instance()
            messages = self._build_prompt(payload.message, snippets)
            if payload.history:
                for entry in payload.history:
                    if "role" in entry and "content" in entry:
                        messages.append({"role": entry["role"], "content": entry["content"]})
            completion = client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                temperature=0.7,
            )
            reply = completion.choices[0].message.content or ""
        else:
            reply = self._build_fallback_response(payload.message, snippets)

        used_ids = [memory.id for memory in memory_records]
        return AssistantChatResponse(reply=reply, used_memory_ids=used_ids)

    @staticmethod
    def _build_fallback_response(message: str, snippets: list[str]) -> str:
        if snippets:
            joined = "\n\n".join(snippets[:3])
            return (
                "(로컬 요약 모드) 제공된 메모를 바탕으로 핵심 정리를 시도합니다.\n"
                f"사용자 질문: {message}\n\n"
                f"참고 메모:\n{joined}\n\n"
                "MindDock 정리: 주요 메모를 다시 확인하고 필요한 실행 항목을 도출해 보세요."
            )
        return (
            "(로컬 응답) 아직 연결된 메모가 없습니다. 현재 메시지를 기반으로 "
            "우선순위를 정하고 필요한 메모를 MindDock에 저장해 주세요."
        )

