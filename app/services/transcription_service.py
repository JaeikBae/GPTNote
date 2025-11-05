"""Audio transcription service for converting speech to text."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from openai import OpenAI

from app.config import get_settings


class TranscriptionError(RuntimeError):
    """Raised when transcription fails for operational reasons."""


class TranscriptionNotConfigured(TranscriptionError):
    """Raised when transcription is requested without proper configuration."""


@dataclass
class TranscriptionResult:
    """Represents the output of a transcription request."""

    text: str


class TranscriptionService:
    """Handles speech-to-text transcription via OpenAI (or future providers)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: OpenAI | None = None

    def _client_instance(self) -> OpenAI:
        if not self.settings.openai_api_key:
            raise TranscriptionNotConfigured(
                "OpenAI API key is required for audio transcription."
            )
        if self._client is None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> TranscriptionResult:
        if not audio_bytes:
            raise TranscriptionError("Audio payload is empty.")

        client = self._client_instance()
        buffer = BytesIO(audio_bytes)
        buffer.name = filename or "audio-input"

        try:
            response = client.audio.transcriptions.create(
                model=self.settings.openai_transcription_model,
                file=buffer,
                response_format="json",
                temperature=0,
            )
        except Exception as exc:  # noqa: BLE001
            raise TranscriptionError(f"Transcription request failed: {exc}") from exc

        text = self._extract_text(response)
        if not text:
            raise TranscriptionError("Transcription completed but returned empty text.")
        return TranscriptionResult(text=text)

    @staticmethod
    def _extract_text(response: Any) -> str | None:
        if response is None:
            return None

        # OpenAI SDK returns an object with attribute access or dict-like behaviour.
        if hasattr(response, "text"):
            text = getattr(response, "text")
            if text:
                return str(text).strip()

        if isinstance(response, dict) and response.get("text"):
            return str(response["text"]).strip()

        return None

