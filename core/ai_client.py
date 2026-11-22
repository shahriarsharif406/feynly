"""Gemini client with a retry -> backoff -> fallback-model ladder. Never raises raw API errors to the UI."""
from __future__ import annotations

import time
from typing import Callable

from pydantic import BaseModel, ValidationError

from . import config as C
from .validation import ConsistencyError


class AIUnavailable(RuntimeError):
    pass


_RETRYABLE = ("429", "503", "500", "unavailable", "resource_exhausted", "timeout", "deadline", "overloaded")


def _is_retryable(exc: Exception) -> bool:
    msg = f"{type(exc).__name__} {exc}".lower()
    return any(tok in msg for tok in _RETRYABLE)


class GeminiClient:
    def __init__(self, api_key: str, primary: str = C.MODEL_PRIMARY, fallback: str = C.MODEL_FALLBACK) -> None:
        from google import genai  # imported lazily so Demo Mode needs no SDK

        from google.genai import types

        try:
            self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=45_000))
        except Exception:
            self._client = genai.Client(api_key=api_key)
        self.primary, self.fallback = primary, fallback
        self.last_error = ""

    def _call(self, model: str, system: str, user: str, schema: type[BaseModel], temperature: float, max_tokens: int) -> str:
        from google.genai import types

        import json as _json

        def build(with_thinking: bool, with_schema: bool):
            sysmsg = system
            c = dict(
                response_mime_type="application/json",
                temperature=temperature,
                max_output_tokens=max(max_tokens, 8192),  # newer models count thinking tokens here
            )
            if with_schema:
                c["response_schema"] = schema
            else:
                sysmsg = system + "\n\nReturn ONLY valid JSON matching this JSON schema:\n" + _json.dumps(schema.model_json_schema())
            c["system_instruction"] = sysmsg
            if with_thinking:
                try:
                    c["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
                except Exception:
                    pass
            return types.GenerateContentConfig(**c)

        # Try progressively simpler configs when the API rejects the request (400).
        tiers = [(True, True), (False, True), (False, False)]
        resp = None
        last = None
        for i, (th, sc) in enumerate(tiers):
            try:
                resp = self._client.models.generate_content(model=model, contents=user, config=build(th, sc))
                break
            except Exception as e:
                last = e
                msg = str(e)
                if i < len(tiers) - 1 and ("400" in msg or "INVALID_ARGUMENT" in msg or "thinking" in msg.lower()):
                    continue
                raise
        if resp is None:
            raise last
        text = getattr(resp, "text", None)
        if not text:
            raise ConsistencyError("empty response")
        return text

    def transcribe(self, audio: bytes, mime: str, lang: str) -> str:
        """Speech to text for the optional voice input. Returns plain text or raises AIUnavailable."""
        from google.genai import types

        hint = "Bangla (Bengali script)" if lang == "bn" else "the language spoken"
        prompt = (
            f"Transcribe this speech verbatim in {hint}. Output only the transcript, no commentary. "
            "If there is no speech, output nothing."
        )
        part = types.Part.from_bytes(data=audio, mime_type=mime)
        for model in (self.primary, self.fallback):
            try:
                resp = self._client.models.generate_content(model=model, contents=[prompt, part])
                text = (getattr(resp, "text", None) or "").strip()
                if text:
                    return text
            except Exception:
                continue
        raise AIUnavailable("transcription failed")

    def generate_json(
        self,
        system: str,
        user: str,
        schema: type[BaseModel],
        temperature: float,
        max_tokens: int,
        validator: Callable[[BaseModel], BaseModel],
    ) -> tuple[BaseModel, str]:
        def attempt(model: str, prompt: str) -> BaseModel:
            return validator(schema.model_validate_json(self._call(model, system, prompt, schema, temperature, max_tokens)))

        for model in (self.primary, self.fallback):
            prompt = user
            delays = [2, 5] if model == self.primary else []
            tries = 0
            validation_retried = False
            while True:
                try:
                    return attempt(model, prompt), model
                except (ValidationError, ConsistencyError, ValueError) as e:
                    self.last_error = f"{model}: {type(e).__name__}: {str(e)[:160]}"
                    if validation_retried:
                        break  # give this model up, try the fallback
                    validation_retried = True
                    prompt = (
                        f"{user}\n\nYour previous output failed validation: {str(e)[:200]}. "
                        "Return only valid JSON matching the schema."
                    )
                except Exception as e:  # network / API errors
                    self.last_error = f"{model}: {type(e).__name__}: {str(e)[:160]}"
                    print("[feynly] AI error:", self.last_error, flush=True)
                    if not _is_retryable(e) or tries >= len(delays):
                        break
                    time.sleep(delays[tries])
                    tries += 1
        raise AIUnavailable("all models failed")


def get_client() -> GeminiClient | None:
    key = C.get_api_key()
    if not key:
        return None
    try:
        import streamlit as st

        @st.cache_resource(show_spinner=False)
        def _make(k: str) -> GeminiClient:
            return GeminiClient(k)

        return _make(key)
    except Exception:
        return GeminiClient(key)
