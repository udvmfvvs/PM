import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"


class AIConfigurationError(RuntimeError):
    pass


class AIServiceError(RuntimeError):
    pass


def load_root_env() -> None:
    for env_path in _env_candidates():
        if env_path.exists():
            _load_env_file(env_path)
            return


def get_openrouter_api_key() -> str:
    load_root_env()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise AIConfigurationError("OPENROUTER_API_KEY is not configured.")
    return api_key


class OpenRouterAIService:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = OPENROUTER_MODEL,
        api_url: str = OPENROUTER_API_URL,
    ):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url

    def ask(self, prompt: str) -> str:
        api_key = self.api_key if self.api_key is not None else get_openrouter_api_key()
        request = build_openrouter_request(
            api_key=api_key,
            model=self.model,
            api_url=self.api_url,
            prompt=prompt,
        )

        try:
            with urlopen(request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as error:
            raise AIServiceError(f"OpenRouter request failed with status {error.code}.") from error
        except URLError as error:
            raise AIServiceError("OpenRouter request failed.") from error

        return parse_openrouter_response(response_body)


def build_openrouter_request(
    api_key: str,
    model: str,
    api_url: str,
    prompt: str,
) -> Request:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }
    return Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )


def parse_openrouter_response(response_body: str) -> str:
    data: dict[str, Any] = json.loads(response_body)
    choices = data.get("choices")
    if not choices:
        raise AIServiceError("OpenRouter response did not include choices.")

    content = choices[0].get("message", {}).get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise AIServiceError("OpenRouter response did not include message content.")
    return content


def _env_candidates() -> list[Path]:
    app_file = Path(__file__).resolve()
    candidates = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        app_file.parents[2] / ".env",
    ]

    unique_candidates: list[Path] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


def _load_env_file(env_path: Path) -> None:
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        os.environ[key] = _clean_env_value(value)


def _clean_env_value(value: str) -> str:
    cleaned_value = value.strip()
    if len(cleaned_value) >= 2 and cleaned_value[0] == cleaned_value[-1] and cleaned_value[0] in {"'", '"'}:
        return cleaned_value[1:-1]
    return cleaned_value
