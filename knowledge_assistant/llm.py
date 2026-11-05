"""Provider-agnostic LLM client. Standard library only (urllib) - no SDK lock-in.

Providers: anthropic (Claude), openai, gemini, xai (Grok), mock (offline, deterministic).

Normalised message format used everywhere in this repo:
  {"role": "user", "content": str}
  {"role": "assistant", "content": str, "tool_calls": [{"id","name","args","extra"}]}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}

`chat(...)` supports two modes:
  * tool calling  : pass `tools=[{"name","description","parameters"(JSON schema)}]`
  * structured out: pass `json_schema=<JSON schema>`; response `.text` is a JSON string
"""
from __future__ import annotations

import copy
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field


class LLMError(RuntimeError):
    pass


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict
    extra: dict | None = None  # provider-specific payload that must be echoed back (e.g. Gemini thought signatures)

    def as_message(self) -> dict:
        return {"id": self.id, "name": self.name, "args": self.args, "extra": self.extra}


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    provider: str = ""
    model: str = ""

    def assistant_message(self) -> dict:
        return {"role": "assistant", "content": self.text, "tool_calls": [t.as_message() for t in self.tool_calls]}


DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
    "xai": "grok-4",
}
KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
}


def _post_json(url: str, headers: dict, payload: dict, timeout: int = 90, retries: int = 3) -> dict:
    data = json.dumps(payload).encode()
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method="POST", headers={"content-type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:600]
            last = LLMError(f"HTTP {e.code} from {url}: {body}")
            if e.code not in (408, 409, 429, 500, 502, 503, 529):
                raise last
        except (urllib.error.URLError, TimeoutError) as e:
            last = LLMError(f"network error: {e}")
        time.sleep(1.5 * (2 ** attempt))
    raise last or LLMError("unknown error")


_STRIP = {"default", "title", "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems", "format", "pattern", "examples"}


def strictify(schema: dict) -> dict:
    """Make a pydantic JSON schema acceptable to OpenAI/xAI strict structured outputs."""
    s = copy.deepcopy(schema)

    def walk(n):
        if isinstance(n, dict):
            for k in list(n):
                if k in _STRIP and not isinstance(n[k], dict):
                    del n[k]
            props = n.get("properties")
            if isinstance(props, dict):
                n["additionalProperties"] = False
                n["required"] = list(props)
                for v in props.values():
                    walk(v)
            for k, v in n.items():
                if k != "properties":
                    walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(s)
    return s


class LLM:
    provider = "base"

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(self.provider, "")

    def chat(self, system: str, messages: list[dict], *, tools: list[dict] | None = None,
             json_schema: dict | None = None, schema_name: str = "output") -> LLMResponse:
        raise NotImplementedError

    def _key(self) -> str:
        k = os.getenv(KEY_ENV[self.provider])
        if not k:
            raise LLMError(f"{KEY_ENV[self.provider]} is not set (provider={self.provider}). Use --provider mock for offline mode.")
        return k


class AnthropicLLM(LLM):
    provider = "anthropic"

    def chat(self, system, messages, *, tools=None, json_schema=None, schema_name="output"):
        msgs: list[dict] = []
        for m in messages:
            if m["role"] == "user":
                msgs.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                blocks = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls") or []:
                    blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["args"]})
                msgs.append({"role": "assistant", "content": blocks or [{"type": "text", "text": "(no content)"}]})
            elif m["role"] == "tool":
                block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
                if msgs and msgs[-1]["role"] == "user" and isinstance(msgs[-1]["content"], list):
                    msgs[-1]["content"].append(block)
                else:
                    msgs.append({"role": "user", "content": [block]})
        payload: dict = {"model": self.model, "max_tokens": 4096, "system": system, "messages": msgs}
        if json_schema:
            payload["tools"] = [{"name": f"emit_{schema_name}", "description": "Return the final structured result.", "input_schema": json_schema}]
            payload["tool_choice"] = {"type": "tool", "name": f"emit_{schema_name}"}
        elif tools:
            payload["tools"] = [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in tools]
        d = _post_json("https://api.anthropic.com/v1/messages",
                       {"x-api-key": self._key(), "anthropic-version": "2023-06-01"}, payload)
        text, calls = "", []
        for b in d.get("content", []):
            if b["type"] == "text":
                text += b["text"]
            elif b["type"] == "tool_use":
                if json_schema:
                    text = json.dumps(b["input"])
                else:
                    calls.append(ToolCall(b["id"], b["name"], b["input"]))
        u = d.get("usage", {})
        return LLMResponse(text, calls, {"input_tokens": u.get("input_tokens", 0), "output_tokens": u.get("output_tokens", 0)}, self.provider, self.model)


class OpenAICompatLLM(LLM):
    """OpenAI Chat Completions wire format (also used by xAI Grok)."""
    provider = "openai"
    base_url = "https://api.openai.com/v1"

    def chat(self, system, messages, *, tools=None, json_schema=None, schema_name="output"):
        msgs: list[dict] = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "assistant":
                am: dict = {"role": "assistant", "content": m.get("content") or None}
                if m.get("tool_calls"):
                    am["tool_calls"] = [{"id": t["id"], "type": "function",
                                         "function": {"name": t["name"], "arguments": json.dumps(t["args"])}} for t in m["tool_calls"]]
                msgs.append(am)
            elif m["role"] == "tool":
                msgs.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
            else:
                msgs.append({"role": "user", "content": m["content"]})
        payload: dict = {"model": self.model, "messages": msgs}
        if json_schema:
            payload["response_format"] = {"type": "json_schema",
                                          "json_schema": {"name": schema_name, "schema": strictify(json_schema), "strict": True}}
        elif tools:
            payload["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in tools]
        d = _post_json(f"{self.base_url}/chat/completions", {"authorization": f"Bearer {self._key()}"}, payload)
        msg = d["choices"][0]["message"]
        calls = []
        for tc in msg.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc["function"]["arguments"]}
            calls.append(ToolCall(tc["id"], tc["function"]["name"], args))
        u = d.get("usage", {})
        return LLMResponse(msg.get("content") or "", calls, {"input_tokens": u.get("prompt_tokens", 0), "output_tokens": u.get("completion_tokens", 0)}, self.provider, self.model)


class OpenAILLM(OpenAICompatLLM):
    provider = "openai"


class XAILLM(OpenAICompatLLM):
    provider = "xai"
    base_url = "https://api.x.ai/v1"


class GeminiLLM(LLM):
    provider = "gemini"

    def chat(self, system, messages, *, tools=None, json_schema=None, schema_name="output"):
        contents: list[dict] = []
        for m in messages:
            if m["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                parts = []
                if m.get("content"):
                    parts.append({"text": m["content"]})
                for t in m.get("tool_calls") or []:
                    parts.append(t.get("extra") or {"functionCall": {"name": t["name"], "args": t["args"]}})
                contents.append({"role": "model", "parts": parts or [{"text": "(no content)"}]})
            elif m["role"] == "tool":
                part = {"functionResponse": {"name": m["name"], "response": {"result": m["content"]}}}
                if contents and contents[-1]["role"] == "user" and "functionResponse" in contents[-1]["parts"][0]:
                    contents[-1]["parts"].append(part)
                else:
                    contents.append({"role": "user", "parts": [part]})
        payload: dict = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents, "generationConfig": {"temperature": 0}}
        if json_schema:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseJsonSchema"] = json_schema
        elif tools:
            payload["tools"] = [{"functionDeclarations": [{"name": t["name"], "description": t["description"], "parameters": t["parameters"]} for t in tools]}]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        d = _post_json(url, {"x-goog-api-key": self._key()}, payload)
        cand = (d.get("candidates") or [{}])[0]
        text, calls = "", []
        for i, p in enumerate((cand.get("content") or {}).get("parts", [])):
            if "text" in p and not p.get("thought"):
                text += p["text"]
            elif "functionCall" in p:
                fc = p["functionCall"]
                calls.append(ToolCall(f"call_{i}_{fc['name']}", fc["name"], fc.get("args") or {}, extra=p))
        u = d.get("usageMetadata", {})
        return LLMResponse(text, calls, {"input_tokens": u.get("promptTokenCount", 0), "output_tokens": u.get("candidatesTokenCount", 0)}, self.provider, self.model)


PROVIDERS = {"anthropic": AnthropicLLM, "claude": AnthropicLLM, "openai": OpenAILLM, "gemini": GeminiLLM, "google": GeminiLLM, "xai": XAILLM, "grok": XAILLM}


def get_llm(provider: str | None = None, model: str | None = None) -> LLM:
    provider = (provider or os.getenv("LLM_PROVIDER") or "mock").lower()
    if provider == "auto":
        for p in ("anthropic", "openai", "gemini", "xai"):
            if os.getenv(KEY_ENV[p]):
                provider = p
                break
        else:
            provider = "mock"
    if provider == "mock":
        from .mock import MockLLM
        return MockLLM(model)
    if provider not in PROVIDERS:
        raise LLMError(f"unknown provider '{provider}'. Choose one of: mock, auto, anthropic, openai, gemini, xai")
    return PROVIDERS[provider](model)
