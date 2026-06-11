from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Protocol, Any

from .models import Answer, TestCase


@dataclass(frozen=True)
class AdapterResponse:
    output: str
    citations: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class ModelAdapter(Protocol):
    """Protocol for live model or application adapters."""

    def generate(self, case: TestCase) -> AdapterResponse:
        """Return the model output for one test case."""


def answer_from_response(case: TestCase, response: AdapterResponse) -> Answer:
    return Answer(
        case_id=case.id,
        output=response.output,
        citations=response.citations,
        metadata=response.metadata,
    )


class OpenAIAdapter:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini", api_base: str = "https://api.openai.com/v1"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.api_base = api_base.rstrip("/")

    def generate(self, case: TestCase) -> AdapterResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": case.input}
            ],
            "temperature": 0.0
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                output = response_data["choices"][0]["message"]["content"]
                return AdapterResponse(output=output)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenAI API request failed (HTTP {e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"OpenAI API request failed: {e}")


class OpenRouterAdapter:
    def __init__(self, api_key: str | None = None, model: str = "google/gemini-2.5-flash", api_base: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.api_base = api_base.rstrip("/")

    def generate(self, case: TestCase) -> AdapterResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")
        
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/XBarni999/promptwatch",
            "X-Title": "PromptWatch"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": case.input}
            ],
            "temperature": 0.0
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                output = response_data["choices"][0]["message"]["content"]
                return AdapterResponse(output=output)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenRouter API request failed (HTTP {e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"OpenRouter API request failed: {e}")


class GroqAdapter:
    def __init__(self, api_key: str | None = None, model: str = "llama-3.3-70b-versatile", api_base: str = "https://api.groq.com/openai/v1"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.api_base = api_base.rstrip("/")

    def generate(self, case: TestCase) -> AdapterResponse:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": case.input}
            ],
            "temperature": 0.0
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                output = response_data["choices"][0]["message"]["content"]
                return AdapterResponse(output=output)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Groq API request failed (HTTP {e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"Groq API request failed: {e}")


class HttpAdapter:
    def __init__(self, url: str, json_path: str | None = None, headers: dict[str, str] | None = None):
        self.url = url
        self.json_path = json_path
        self.headers = headers or {}

    def generate(self, case: TestCase) -> AdapterResponse:
        headers = {"Content-Type": "application/json"}
        headers.update(self.headers)
        
        data = {"input": case.input}
        req = urllib.request.Request(
            self.url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                body = res.read().decode("utf-8")
                try:
                    res_json = json.loads(body)
                    if self.json_path:
                        parts = self.json_path.split(".")
                        val = res_json
                        for part in parts:
                            if isinstance(val, dict):
                                val = val.get(part, {})
                            else:
                                val = ""
                        output = str(val)
                    else:
                        if isinstance(res_json, dict):
                            output = (
                                res_json.get("output") or 
                                res_json.get("response") or 
                                res_json.get("text") or 
                                res_json.get("answer") or 
                                body
                            )
                        else:
                            output = body
                except json.JSONDecodeError:
                    output = body
                
                # Extrapolate citations or metadata from response if any
                citations = []
                metadata = {}
                if isinstance(res_json, dict):
                    if "citations" in res_json and isinstance(res_json["citations"], list):
                        citations = [str(c) for c in res_json["citations"]]
                    if "metadata" in res_json and isinstance(res_json["metadata"], dict):
                        metadata = res_json["metadata"]
                
                return AdapterResponse(output=output, citations=citations, metadata=metadata)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"HTTP adapter request failed (HTTP {e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"HTTP adapter request failed: {e}")


def get_adapter(adapter_name: str, model: str | None = None, url: str | None = None, json_path: str | None = None) -> ModelAdapter:
    adapter_name = adapter_name.lower()
    if adapter_name == "openai":
        return OpenAIAdapter(model=model or "gpt-4o-mini")
    elif adapter_name == "openrouter":
        return OpenRouterAdapter(model=model or "google/gemini-2.5-flash")
    elif adapter_name == "groq":
        return GroqAdapter(model=model or "llama-3.3-70b-versatile")
    elif adapter_name == "http":
        if not url:
            raise ValueError("HTTP adapter requires a custom URL via --url")
        return HttpAdapter(url=url, json_path=json_path)
    else:
        raise ValueError(f"Unknown adapter type: {adapter_name}")
