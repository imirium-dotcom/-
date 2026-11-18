import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Optional

import requests

from key_manager import KeyManager


OLLAMA_URL = "http://localhost:11434"
OPENAI_API_URL = "https://api.openai.com/v1/responses"

DEFAULT_CONTEXT = 4096
DEFAULT_NUM_PREDICT = 2048
RETRY_NUM_PREDICT = 4096
COMPARISON_NUM_PREDICT = 1536
REQUEST_TIMEOUT = 300

DEFAULT_COMPARISON_MODEL = "gemma4:12b"

OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
GEMINI_DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
ANTHROPIC_DEFAULT_MODEL = os.getenv(
    "ANTHROPIC_MODEL",
    "claude-3-5-haiku-latest",
)

# Максимальное количество одновременно работающих моделей.
# При необходимости можно изменить через переменную окружения.
MAX_PARALLEL_MODELS = max(
    1,
    int(os.getenv("ARMITAGE_MAX_PARALLEL_MODELS", "8")),
)


MODEL_SETTINGS = {
    "qwen3.5:4b": {
        "num_ctx": 8192,
        "num_predict": 1024,
        "temperature": 0.4,
    },
    "gemma4:12b": {
        "num_ctx": 8192,
        "num_predict": 1024,
        "temperature": 0.3,
    },
    "qwen3.8:27b": {
        "num_ctx": 16384,
        "num_predict": 2048,
        "temperature": 0.3,
    },
}


ARMITAGE_CONTEXT = """
Ты работаешь как модельный координатор Armitage — AI Core пользователя.

Твоя задача:
- отвечать на запросы пользователя;
- выбирать подходящие модели и провайдеры;
- использовать локальные модели Ollama;
- использовать подключённые внешние провайдеры;
- собирать результаты разных моделей;
- сопоставлять ответы;
- находить противоречия и недостающую информацию;
- объединять полезные результаты;
- не выдавать предположения за проверенные факты;
- сохранять существующую функциональность AI Core;
- учитывать контекст проекта;
- не утверждать, что функция реализована, если это не подтверждено.

Модели должны сотрудничать, а не заменять друг друга.
Успешный ответ одной модели не должен останавливать работу остальных.

При сравнении:
- выделяй совпадения;
- выявляй противоречия;
- учитывай аргументы каждой модели;
- не считай совпадение ответов доказательством истинности;
- не выдумывай источники и результаты проверок.

Отвечай на русском языке, если пользователь не попросил другой язык.

Не заявляй, что можешь непосредственно изменять файлы компьютера,
если соответствующий инструмент или исполнитель фактически не запущен.
""".strip()


class ModelCoordinator:

    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        ollama_url: str = OLLAMA_URL,
        timeout: int = REQUEST_TIMEOUT,
    ):
        self.key_manager = key_manager or KeyManager()

        self.ollama_url = ollama_url.rstrip("/")
        self.chat_url = f"{self.ollama_url}/api/chat"
        self.tags_url = f"{self.ollama_url}/api/tags"
        self.show_url = f"{self.ollama_url}/api/show"

        self.timeout = timeout

        self.last_usage = {}
        self.last_errors = {}

    # =========================================================
    # PROVIDERS / KEY MANAGER
    # =========================================================

    def _get_provider_key(self, provider: str) -> Optional[str]:

        provider = str(provider).strip().lower()

        try:
            key = self.key_manager.get_key(provider)

            if key:
                return key

        except Exception:
            pass

        env_names = {
            "openai": ["OPENAI_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "openrouter": ["OPENROUTER_API_KEY"],
            "groq": ["GROQ_API_KEY"],
            "mistral": ["MISTRAL_API_KEY"],
            "deepseek": ["DEEPSEEK_API_KEY"],
            "huggingface": ["HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN"],
            "cloudflare": ["CLOUDFLARE_API_TOKEN"],
            "nvidia": ["NVIDIA_API_KEY"],
            "replicate": ["REPLICATE_API_TOKEN"],
            "together": ["TOGETHER_API_KEY"],
            "fireworks": ["FIREWORKS_API_KEY"],
            "perplexity": ["PERPLEXITY_API_KEY"],
            "cohere": ["COHERE_API_KEY"],
        }

        for env_name in env_names.get(provider, []):
            value = os.getenv(env_name)

            if value:
                return value

        return None

    def _provider_has_key(self, provider: str) -> bool:
        return bool(self._get_provider_key(provider))

    def _get_provider_config(self, provider: str) -> dict:

        provider = str(provider).strip().lower()

        try:
            getter = getattr(
                self.key_manager,
                "get_provider_config",
                None,
            )

            if callable(getter):
                config = getter(provider)

                if isinstance(config, dict):
                    return dict(config)

        except Exception as exc:
            self.last_errors[f"{provider}_config"] = str(exc)

        try:
            providers = self.key_manager.list_providers()

            if isinstance(providers, dict):
                item = providers.get(provider, {})

                return dict(item) if isinstance(item, dict) else {}

            if isinstance(providers, list):

                for item in providers:

                    if not isinstance(item, dict):
                        continue

                    item_id = str(
                        item.get("provider") or item.get("id") or ""
                    ).lower()

                    if item_id == provider:
                        return dict(item)

        except Exception as exc:
            self.last_errors[f"{provider}_config"] = str(exc)

        return {}

    # =========================================================
    # TASK CLASSIFICATION
    # =========================================================

    def classify_task(self, text: str) -> str:

        text = (text or "").lower()

        vision_words = (
            "изображение",
            "картинка",
            "фото",
            "фотограф",
            "рисунок",
            "изучи изображение",
            "проанализируй изображение",
            "vision",
            "image",
        )

        audio_words = (
            "аудио",
            "голос",
            "микрофон",
            "распознай речь",
            "озвучь",
            "синтез речи",
            "audio",
            "speech",
            "voice",
        )

        code_words = (
            "код",
            "программ",
            "функци",
            "класс ",
            "python",
            "javascript",
            "скрипт",
            "файл .py",
            "исправь ошибку",
            "отлад",
            "рефактор",
            "api",
        )

        complex_words = (
            "архитектур",
            "спроектируй",
            "разработай систему",
            "сравни модели",
            "проанализируй проект",
            "проанализируй сложную задачу",
            "многоэтап",
            "план реализации",
            "интегрируй",
            "координатор",
            "создай модуль",
            "проанализируй",
            "сложную задачу",
        )

        if any(word in text for word in vision_words):
            return "vision"

        if any(word in text for word in audio_words):
            return "audio"

        if any(word in text for word in code_words):
            return "code"

        if any(word in text for word in complex_words):
            return "complex"

        return "simple"

    def preferred_models(self, task_type: str) -> list:

        if task_type == "code":
            return [
                "qwen3.8:27b",
                "qwen3.5:4b",
                "gemma4:12b",
            ]

        if task_type == "complex":
            return [
                "qwen3.8:27b",
                "gemma4:12b",
                "qwen3.5:4b",
            ]

        if task_type == "vision":
            return [
                "gemma4:12b",
                "qwen3.8:27b",
                "qwen3.5:4b",
            ]

        if task_type == "audio":
            return [
                "qwen3.5:4b",
                "gemma4:12b",
                "qwen3.8:27b",
            ]

        return [
            "qwen3.5:4b",
            "gemma4:12b",
            "qwen3.8:27b",
        ]

    # =========================================================
    # OLLAMA
    # =========================================================

    def list_models(self) -> dict:

        try:
            response = requests.get(
                self.tags_url,
                timeout=10,
            )

            response.raise_for_status()

            payload = response.json()

            models = []

            for item in payload.get("models", []):

                name = item.get("name") or item.get("model")

                if name:
                    models.append(name)

            return {
                "available": True,
                "models": models,
                "error": None,
            }

        except Exception as exc:

            self.last_errors["ollama"] = str(exc)

            return {
                "available": False,
                "models": [],
                "error": str(exc),
            }

    def is_model_available(self, model_name: str) -> bool:

        result = self.list_models()

        if not result["available"]:
            return False

        models = result["models"]

        if model_name in models:
            return True

        requested_base = model_name.split(":")[0]

        return any(
            model.split(":")[0] == requested_base
            for model in models
        )

    # =========================================================
    # EXTERNAL MODEL CATALOG
    # =========================================================

    def _default_provider_models(self) -> dict:

        return {
            "openai": [OPENAI_DEFAULT_MODEL],
            "gemini": [GEMINI_DEFAULT_MODEL],
            "anthropic": [ANTHROPIC_DEFAULT_MODEL],

            "openrouter": ["openai/gpt-oss-20b:free"],
            "groq": ["llama-3.3-70b-versatile"],
            "mistral": ["mistral-small-latest"],
            "deepseek": ["deepseek-chat"],
            "together": [
                "meta-llama/Llama-3.3-70B-Instruct-Turbo"
            ],
            "fireworks": [
                "accounts/fireworks/models/llama-v3p3-70b-instruct"
            ],
            "nvidia": ["meta/llama-3.3-70b-instruct"],
            "perplexity": ["sonar"],
        }

    def get_available_model_names(self) -> list:

        available = self.list_models()

        result = list(available.get("models", []))

        supported_providers = {
            "openai",
            "openrouter",
            "groq",
            "mistral",
            "deepseek",
            "together",
            "fireworks",
            "nvidia",
            "perplexity",
            "gemini",
            "anthropic",
        }

        try:
            catalog = self.key_manager.list_catalog()

        except Exception as exc:

            self.last_errors["key_manager_catalog"] = str(exc)

            catalog = []

        if isinstance(catalog, dict):

            catalog_items = [
                {
                    "provider": provider,
                    **(
                        data
                        if isinstance(data, dict)
                        else {}
                    ),
                }
                for provider, data in catalog.items()
            ]

        elif isinstance(catalog, list):

            catalog_items = catalog

        else:

            catalog_items = []

        registered = set()

        for item in catalog_items:

            if not isinstance(item, dict):
                continue

            provider = str(
                item.get("provider")
                or item.get("id")
                or ""
            ).strip().lower()

            if provider not in supported_providers:
                continue

            registered.add(provider)

        # OpenAI может быть настроен только через переменную окружения.
        # Поэтому отдельно учитываем его наличие.
        for provider in supported_providers:

            if self._provider_has_key(provider):
                registered.add(provider)

        defaults = self._default_provider_models()

        for provider in registered:

            if not self._provider_has_key(provider):
                continue

            config = self._get_provider_config(provider)

            models = config.get("models", [])

            if not isinstance(models, list):
                models = []

            provider_models = []

            for model_item in models:

                if isinstance(model_item, str):

                    model_name = model_item.strip()

                elif isinstance(model_item, dict):

                    if model_item.get("enabled", True) is False:
                        continue

                    model_name = str(
                        model_item.get("id")
                        or model_item.get("name")
                        or ""
                    ).strip()

                else:

                    continue

                if model_name:
                    provider_models.append(model_name)

            # Если пользователь не добавил модель вручную,
            # используем модель по умолчанию для данного провайдера.
            if not provider_models:
                provider_models = defaults.get(provider, [])

            for model_name in provider_models:

                if model_name:
                    result.append(
                        f"{provider}:{model_name}"
                    )

        return list(dict.fromkeys(result))

    def get_model_details(self, model_name: str) -> dict:

        try:
            response = requests.post(
                self.show_url,
                json={"name": model_name},
                timeout=20,
            )

            response.raise_for_status()

            return response.json()

        except Exception as exc:

            return {
                "error": str(exc),
                "model": model_name,
            }

    # =========================================================
    # MODEL SELECTION
    # =========================================================

    def select_models(self, task_type: str) -> list:

        available = self.get_available_model_names()

        preferred = self.preferred_models(task_type)

        selected = [
            model
            for model in preferred
            if model in available
        ]

        # Все доступные внешние провайдеры включаются в маршрут.
        external = [
            model
            for model in available
            if ":" in str(model)
        ]

        selected.extend(external)

        if not selected:
            selected = available

        return list(dict.fromkeys(selected))

    # =========================================================
    # PROMPTS / CONTEXT
    # =========================================================

    def build_system_prompt(
        self,
        task_type: str,
        extra_instructions: Optional[str] = None,
    ) -> str:

        parts = [
            ARMITAGE_CONTEXT,
            f"Тип задачи: {task_type}.",
            "Отвечай на русском языке, если пользователь не попросил другой язык.",
            "Не придумывай результаты выполнения инструментов.",
        ]

        if extra_instructions:
            parts.append(str(extra_instructions))

        return "\n\n".join(parts)

    def clean_context(self, context) -> list:

        if context is None:
            return []

        if isinstance(context, str):

            return [
                {
                    "role": "user",
                    "content": context,
                }
            ]

        if not isinstance(context, list):
            return []

        cleaned = []

        for item in context:

            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role not in (
                "system",
                "user",
                "assistant",
                "developer",
            ):
                continue

            if content is None:
                continue

            if isinstance(content, (str, list)):

                cleaned.append({
                    "role": role,
                    "content": content,
                })

        return cleaned

    # =========================================================
    # OPENAI RESPONSES API
    # =========================================================

    def _request_openai_model(
        self,
        model: str,
        messages: list,
        system_prompt: str,
        max_tokens: int,
    ) -> dict:

        api_key = self._get_provider_key("openai")

        if not api_key:

            return {
                "success": False,
                "complete": False,
                "model": model,
                "text": "",
                "error": "Ключ OpenAI не найден.",
            }

        requested_model = model

        if requested_model.startswith("openai:"):
            requested_model = requested_model.split(":", 1)[1]

        if not requested_model:
            requested_model = OPENAI_DEFAULT_MODEL

        input_messages = []

        for message in messages:

            role = message.get("role", "user")

            if role == "system":
                continue

            content = message.get("content", "")

            input_messages.append({
                "role": role,
                "content": (
                    content
                    if isinstance(content, (str, list))
                    else str(content)
                ),
            })

        payload = {
            "model": requested_model,
            "instructions": system_prompt,
            "input": input_messages,
            "max_output_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        started = time.time()

        try:

            response = requests.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            elapsed = round(time.time() - started, 2)

            if not response.ok:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = response.text

                error_message = (
                    error_data.get("error", {}).get(
                        "message",
                        str(error_data),
                    )
                    if isinstance(error_data, dict)
                    else str(error_data)
                )

                self.last_errors["openai"] = error_message

                return {
                    "success": False,
                    "complete": False,
                    "model": f"openai:{requested_model}",
                    "text": "",
                    "error": error_message,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                }

            data = response.json()

            output_text = data.get("output_text", "")

            if not output_text:

                chunks = []

                for item in data.get("output", []):

                    for content_item in item.get("content", []):

                        if content_item.get("type") in (
                            "output_text",
                            "text",
                        ):

                            value = content_item.get("text", "")

                            if value:
                                chunks.append(value)

                output_text = "\n".join(chunks)

            usage = data.get("usage", {})

            self.last_usage[f"openai:{requested_model}"] = usage

            status = data.get("status", "")

            incomplete_details = data.get(
                "incomplete_details"
            )

            complete = (
                status != "incomplete"
                and not incomplete_details
                and bool(output_text.strip())
            )

            return {
                "success": bool(output_text.strip()),
                "complete": complete,
                "model": f"openai:{requested_model}",
                "text": output_text.strip(),
                "error": None if output_text.strip() else (
                    "OpenAI вернул пустой ответ."
                ),
                "elapsed": elapsed,
                "usage": usage,
                "status": status,
                "incomplete_details": incomplete_details,
            }

        except Exception as exc:

            self.last_errors["openai"] = str(exc)

            return {
                "success": False,
                "complete": False,
                "model": f"openai:{requested_model}",
                "text": "",
                "error": str(exc),
            }

    # =========================================================
    # OPENAI-COMPATIBLE PROVIDERS
    # =========================================================

    def _get_openai_compatible_config(
        self,
        provider: str,
    ) -> dict:

        defaults = {

            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "env_model": "OPENROUTER_MODEL",
                "default_model": "openai/gpt-oss-20b:free",
            },

            "groq": {
                "base_url": "https://api.groq.com/openai/v1",
                "env_model": "GROQ_MODEL",
                "default_model": "llama-3.3-70b-versatile",
            },

            "mistral": {
                "base_url": "https://api.mistral.ai/v1",
                "env_model": "MISTRAL_MODEL",
                "default_model": "mistral-small-latest",
            },

            "deepseek": {
                "base_url": "https://api.deepseek.com",
                "env_model": "DEEPSEEK_MODEL",
                "default_model": "deepseek-chat",
            },

            "together": {
                "base_url": "https://api.together.xyz/v1",
                "env_model": "TOGETHER_MODEL",
                "default_model": (
                    "meta-llama/Llama-3.3-70B-Instruct-Turbo"
                ),
            },

            "fireworks": {
                "base_url": "https://api.fireworks.ai/inference/v1",
                "env_model": "FIREWORKS_MODEL",
                "default_model": (
                    "accounts/fireworks/models/llama-v3p3-70b-instruct"
                ),
            },

            "nvidia": {
                "base_url": "https://integrate.api.nvidia.com/v1",
                "env_model": "NVIDIA_MODEL",
                "default_model": "meta/llama-3.3-70b-instruct",
            },

            "perplexity": {
                "base_url": "https://api.perplexity.ai",
                "env_model": "PERPLEXITY_MODEL",
                "default_model": "sonar",
            },
        }

        config = defaults.get(provider, {}).copy()

        stored = self._get_provider_config(provider)

        custom_url = (
            stored.get("base_url")
            or stored.get("api_base")
            or stored.get("endpoint")
            or stored.get("url")
        )

        if custom_url:
            config["base_url"] = str(custom_url).rstrip("/")

        custom_model = (
            stored.get("default_model")
            or stored.get("model")
        )

        if custom_model:
            config["default_model"] = str(custom_model)

        env_model = config.get("env_model")

        if env_model and os.getenv(env_model):
            config["default_model"] = os.getenv(env_model)

        return config

    def _request_openai_compatible_model(
        self,
        provider: str,
        model: str,
        messages: list,
        system_prompt: str,
        max_tokens: int,
    ) -> dict:

        api_key = self._get_provider_key(provider)

        if not api_key:

            return {
                "success": False,
                "complete": False,
                "model": f"{provider}:{model}",
                "text": "",
                "error": f"Ключ {provider} не найден.",
            }

        config = self._get_openai_compatible_config(provider)

        requested_model = model

        if ":" in requested_model:

            prefix, remainder = requested_model.split(":", 1)

            if prefix.lower() == provider.lower():
                requested_model = remainder

        if not requested_model:
            requested_model = config.get("default_model", "")

        if not requested_model:

            return {
                "success": False,
                "complete": False,
                "model": f"{provider}:{model}",
                "text": "",
                "error": f"Не указана модель для {provider}.",
            }

        base_url = config.get("base_url")

        if not base_url:

            return {
                "success": False,
                "complete": False,
                "model": f"{provider}:{requested_model}",
                "text": "",
                "error": f"Не задан API URL для {provider}.",
            }

        compatible_messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        for message in messages:

            role = message.get("role", "user")

            if role not in (
                "user",
                "assistant",
                "system",
            ):
                continue

            content = message.get("content", "")

            compatible_messages.append({
                "role": role,
                "content": (
                    content
                    if isinstance(content, str)
                    else str(content)
                ),
            })

        payload = {
            "model": requested_model,
            "messages": compatible_messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        if provider == "openrouter":

            headers["HTTP-Referer"] = "http://localhost"
            headers["X-Title"] = "Armitage AI Core"

        started = time.time()

        try:

            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            elapsed = round(time.time() - started, 2)

            if not response.ok:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = response.text

                if isinstance(error_data, dict):

                    error = error_data.get("error")

                    if isinstance(error, dict):
                        error_message = error.get(
                            "message",
                            str(error),
                        )
                    else:
                        error_message = str(error or error_data)

                else:

                    error_message = str(error_data)

                self.last_errors[provider] = error_message

                return {
                    "success": False,
                    "complete": False,
                    "model": f"{provider}:{requested_model}",
                    "text": "",
                    "error": error_message,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                }

            data = response.json()

            choices = data.get("choices", [])

            output_text = ""

            if choices:

                message_data = choices[0].get("message", {})

                content = message_data.get("content", "")

                if isinstance(content, str):

                    output_text = content

                elif isinstance(content, list):

                    output_text = "\n".join(
                        str(item.get("text", ""))
                        for item in content
                        if isinstance(item, dict)
                    )

            usage = data.get("usage", {})

            self.last_usage[
                f"{provider}:{requested_model}"
            ] = usage

            finish_reason = (
                choices[0].get("finish_reason")
                if choices
                else None
            )

            complete = (
                bool(output_text.strip())
                and finish_reason not in (
                    "length",
                    "content_filter",
                )
            )

            return {
                "success": bool(output_text.strip()),
                "complete": complete,
                "model": f"{provider}:{requested_model}",
                "text": output_text.strip(),
                "error": None if output_text.strip() else (
                    "Провайдер вернул пустой ответ."
                ),
                "elapsed": elapsed,
                "usage": usage,
                "finish_reason": finish_reason,
            }

        except Exception as exc:

            self.last_errors[provider] = str(exc)

            return {
                "success": False,
                "complete": False,
                "model": f"{provider}:{model}",
                "text": "",
                "error": str(exc),
            }

    # =========================================================
    # GEMINI
    # =========================================================

    def _request_gemini_model(
        self,
        model: str,
        messages: list,
        system_prompt: str,
        max_tokens: int,
    ) -> dict:

        api_key = self._get_provider_key("gemini")

        if not api_key:

            return {
                "success": False,
                "complete": False,
                "model": f"gemini:{model}",
                "text": "",
                "error": "Ключ Gemini не найден.",
            }

        requested_model = model

        if requested_model.startswith("gemini:"):
            requested_model = requested_model.split(":", 1)[1]

        if not requested_model:
            requested_model = GEMINI_DEFAULT_MODEL

        contents = []

        for message in messages:

            role = message.get("role", "user")

            if role == "assistant":
                role = "model"

            elif role not in ("user", "model"):
                continue

            content = message.get("content", "")

            if not isinstance(content, str):
                content = str(content)

            contents.append({
                "role": role,
                "parts": [{"text": content}],
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.3,
            },
        }

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{requested_model}:generateContent"
        )

        started = time.time()

        try:

            response = requests.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )

            elapsed = round(time.time() - started, 2)

            if not response.ok:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = response.text

                error_message = (
                    error_data.get("error", {}).get(
                        "message",
                        str(error_data),
                    )
                    if isinstance(error_data, dict)
                    else str(error_data)
                )

                self.last_errors["gemini"] = error_message

                return {
                    "success": False,
                    "complete": False,
                    "model": f"gemini:{requested_model}",
                    "text": "",
                    "error": error_message,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                }

            data = response.json()

            candidates = data.get("candidates", [])

            output_text = ""

            if candidates:

                parts = (
                    candidates[0]
                    .get("content", {})
                    .get("parts", [])
                )

                output_text = "\n".join(
                    part.get("text", "")
                    for part in parts
                    if isinstance(part, dict)
                )

            usage = data.get("usageMetadata", {})

            self.last_usage[
                f"gemini:{requested_model}"
            ] = usage

            finish_reason = (
                candidates[0].get("finishReason")
                if candidates
                else None
            )

            return {
                "success": bool(output_text.strip()),
                "complete": (
                    bool(output_text.strip())
                    and finish_reason not in (
                        "MAX_TOKENS",
                        "SAFETY",
                        "RECITATION",
                    )
                ),
                "model": f"gemini:{requested_model}",
                "text": output_text.strip(),
                "error": None if output_text.strip() else (
                    "Gemini вернул пустой ответ."
                ),
                "elapsed": elapsed,
                "usage": usage,
                "finish_reason": finish_reason,
            }

        except Exception as exc:

            self.last_errors["gemini"] = str(exc)

            return {
                "success": False,
                "complete": False,
                "model": f"gemini:{requested_model}",
                "text": "",
                "error": str(exc),
            }

    def check_gemini_connection(self) -> dict:
        """
        Выполняет один короткий прямой запрос к Gemini API.
        Не запускает распределение моделей, Planner или Resolver.
        API-ключ не включается в возвращаемый результат.
        """
        result = self._request_gemini_model(
            model=GEMINI_DEFAULT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "Ответь одним словом: OK",
                }
            ],
            system_prompt=(
                "Это техническая проверка доступности API. "
                "Ответь одним словом: OK."
            ),
            max_tokens=8,
        )

        if result.get("success") and str(result.get("text", "")).strip():
            return {
                "success": True,
                "provider": "gemini",
                "model": result.get("model"),
                "message": "Подключение к Gemini API работает.",
                "response": result.get("text", "").strip(),
                "elapsed": result.get("elapsed"),
            }

        return {
            "success": False,
            "provider": "gemini",
            "model": result.get("model"),
            "message": "Не удалось проверить подключение к Gemini API.",
            "error": result.get("error") or "Gemini не вернул содержательный ответ.",
            "status_code": result.get("status_code"),
        }

    # =========================================================
    # ANTHROPIC
    # =========================================================

    def _request_anthropic_model(
        self,
        model: str,
        messages: list,
        system_prompt: str,
        max_tokens: int,
    ) -> dict:

        api_key = self._get_provider_key("anthropic")

        if not api_key:

            return {
                "success": False,
                "complete": False,
                "model": f"anthropic:{model}",
                "text": "",
                "error": "Ключ Anthropic не найден.",
            }

        requested_model = model

        if requested_model.startswith("anthropic:"):
            requested_model = requested_model.split(":", 1)[1]

        if not requested_model:
            requested_model = ANTHROPIC_DEFAULT_MODEL

        anthropic_messages = []

        for message in messages:

            role = message.get("role", "user")

            if role not in ("user", "assistant"):
                continue

            anthropic_messages.append({
                "role": role,
                "content": str(message.get("content", "")),
            })

        payload = {
            "model": requested_model,
            "system": system_prompt,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
        }

        started = time.time()

        try:

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )

            elapsed = round(time.time() - started, 2)

            if not response.ok:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = response.text

                error_message = (
                    error_data.get("error", {}).get(
                        "message",
                        str(error_data),
                    )
                    if isinstance(error_data, dict)
                    else str(error_data)
                )

                self.last_errors["anthropic"] = error_message

                return {
                    "success": False,
                    "complete": False,
                    "model": f"anthropic:{requested_model}",
                    "text": "",
                    "error": error_message,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                }

            data = response.json()

            output_text = "\n".join(
                item.get("text", "")
                for item in data.get("content", [])
                if isinstance(item, dict)
                and item.get("type") == "text"
            )

            usage = data.get("usage", {})

            self.last_usage[
                f"anthropic:{requested_model}"
            ] = usage

            stop_reason = data.get("stop_reason")

            return {
                "success": bool(output_text.strip()),
                "complete": (
                    bool(output_text.strip())
                    and stop_reason != "max_tokens"
                ),
                "model": f"anthropic:{requested_model}",
                "text": output_text.strip(),
                "error": None if output_text.strip() else (
                    "Anthropic вернул пустой ответ."
                ),
                "elapsed": elapsed,
                "usage": usage,
                "stop_reason": stop_reason,
            }

        except Exception as exc:

            self.last_errors["anthropic"] = str(exc)

            return {
                "success": False,
                "complete": False,
                "model": f"anthropic:{requested_model}",
                "text": "",
                "error": str(exc),
            }

    # =========================================================
    # MODEL REQUEST ROUTER
    # =========================================================

    def _request_model(
        self,
        model: str,
        messages: list,
        system_prompt: str,
        max_tokens: int,
    ) -> dict:

        if model.startswith("openai:"):

            return self._request_openai_model(
                model,
                messages,
                system_prompt,
                max_tokens,
            )

        if ":" in model:

            provider, model_name = model.split(":", 1)

            provider = provider.lower()

            if provider == "gemini":

                return self._request_gemini_model(
                    model,
                    messages,
                    system_prompt,
                    max_tokens,
                )

            if provider == "anthropic":

                return self._request_anthropic_model(
                    model,
                    messages,
                    system_prompt,
                    max_tokens,
                )

            compatible_providers = {
                "openrouter",
                "groq",
                "mistral",
                "deepseek",
                "together",
                "fireworks",
                "nvidia",
                "perplexity",
            }

            if provider in compatible_providers:

                return self._request_openai_compatible_model(
                    provider,
                    model_name,
                    messages,
                    system_prompt,
                    max_tokens,
                )

        return self._request_ollama_model(
            model,
            messages,
            system_prompt,
            max_tokens,
        )

    # =========================================================
    # OLLAMA REQUEST
    # =========================================================

    def _request_ollama_model(
        self,
        model: str,
        messages: list,
        system_prompt: str,
        max_tokens: int,
    ) -> dict:

        model_messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        model_messages.extend(messages)

        settings = MODEL_SETTINGS.get(
            model,
            {
                "num_ctx": DEFAULT_CONTEXT,
                "num_predict": max_tokens,
                "temperature": 0.3,
            },
        ).copy()

        settings["num_predict"] = max_tokens

        payload = {
            "model": model,
            "messages": model_messages,
            "stream": False,
            "think": False,
            "options": settings,
        }

        started = time.time()

        try:

            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout,
            )

            elapsed = round(time.time() - started, 2)

            if not response.ok:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = response.text

                error_message = (
                    error_data.get("error", str(error_data))
                    if isinstance(error_data, dict)
                    else str(error_data)
                )

                self.last_errors[model] = error_message

                return {
                    "success": False,
                    "complete": False,
                    "model": model,
                    "text": "",
                    "error": error_message,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                }

            data = response.json()

            message_data = data.get("message", {})

            if not isinstance(message_data, dict):
                message_data = {}

            output_text = message_data.get("content", "")

            if not isinstance(output_text, str):
                output_text = str(output_text or "")

            output_text = output_text.strip()

            thinking_received = bool(
                str(message_data.get("thinking", "") or "").strip()
            )

            complete = (
                bool(output_text)
                and data.get("done_reason") != "length"
                and data.get("done", True)
            )

            usage = {
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
            }

            self.last_usage[model] = usage

            if output_text:

                error_message = None

            elif thinking_received:

                error_message = (
                    "Ollama вернула thinking, но не вернула обычный "
                    "текст ответа."
                )

            else:

                error_message = "Ollama вернула пустой ответ."

            return {
                "success": bool(output_text),
                "complete": bool(complete),
                "model": model,
                "text": output_text,
                "error": error_message,
                "elapsed": elapsed,
                "usage": usage,
                "done_reason": data.get("done_reason"),
                "thinking_received": thinking_received,
            }

        except Exception as exc:

            self.last_errors[model] = str(exc)

            return {
                "success": False,
                "complete": False,
                "model": model,
                "text": "",
                "error": str(exc),
            }

    # =========================================================
    # GENERATION WITH RETRY
    # =========================================================

    def ask_model(
        self,
        model: str,
        prompt: str,
        context=None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:

        task_type = self.classify_task(prompt)

        if system_prompt is None:
            system_prompt = self.build_system_prompt(task_type)

        messages = self.clean_context(context)

        messages.append({
            "role": "user",
            "content": prompt,
        })

        token_limit = max_tokens or DEFAULT_NUM_PREDICT

        result = self._request_model(
            model,
            messages,
            system_prompt,
            token_limit,
        )

        should_retry = (
            not result.get("success")
            or not result.get("complete")
        )

        if should_retry and token_limit < RETRY_NUM_PREDICT:

            retry = self._request_model(
                model,
                messages,
                system_prompt,
                RETRY_NUM_PREDICT,
            )

            if retry.get("success"):

                retry["retried"] = True
                retry["initial_error"] = result.get("error")

                return retry

            result["retry_attempted"] = True
            result["retry_error"] = retry.get("error")

        return result

    # =========================================================
    # COMPARISON AND SYNTHESIS
    # =========================================================

    def compare_answers(
        self,
        prompt: str,
        answers: list,
        comparison_model: Optional[str] = None,
    ) -> dict:

        if not answers:

            return {
                "success": False,
                "complete": False,
                "text": "",
                "error": "Нет ответов для сравнения.",
            }

        comparison_model = (
            comparison_model or DEFAULT_COMPARISON_MODEL
        )

        formatted_answers = []

        for index, answer in enumerate(answers, start=1):

            if not isinstance(answer, dict):
                continue

            formatted_answers.append(
                f"Ответ {index} — модель "
                f"{answer.get('model', 'unknown')}:\n"
                f"{answer.get('text', '')}"
            )

        comparison_prompt = f"""
Ты выполняешь этап коллективного анализа и синтеза Armitage.

Исходный запрос:
{prompt}

Результаты отдельных моделей:
{chr(10).join(formatted_answers)}

Твоя задача — не просто выбрать один ответ.

Проведи анализ:

1. Определи, какие выводы совпадают.
2. Найди противоречия между моделями.
3. Выдели полезную информацию, присутствующую только в отдельных ответах.
4. Определи ошибки и необоснованные утверждения.
5. Выдели сведения, которые требуют дополнительной проверки.
6. Объедини лучшие части ответов.
7. Не теряй важные детали исходной задачи.
8. Не выдумывай источники, факты и результаты проверок.

Подготовь единый итоговый ответ.

Если модели расходятся во мнениях, укажи это явно.
Совпадение нескольких моделей не является доказательством истины.

В результате отдели:
- общий подтверждённый вывод;
- полезные дополнительные сведения;
- разногласия;
- вопросы, требующие проверки.
""".strip()

        return self.ask_model(
            comparison_model,
            comparison_prompt,
            system_prompt=self.build_system_prompt(
                "complex",
                "Ты являешься синтезатором результатов нескольких моделей.",
            ),
            max_tokens=COMPARISON_NUM_PREDICT,
        )

    # =========================================================
    # RESULT VERIFICATION
    # =========================================================

    def verify_result(
        self,
        result,
        verification_callback: Optional[Callable] = None,
    ) -> dict:

        if not isinstance(result, dict):

            return {
                "verified": False,
                "evidence": [],
                "reason": "Результат имеет неверный формат.",
            }

        if not result.get("success"):

            return {
                "verified": False,
                "evidence": [],
                "reason": "Модель не вернула успешный результат.",
            }

        if verification_callback is None:

            return {
                "verified": False,
                "evidence": [],
                "reason": (
                    "Проверка не выполнена: отсутствует "
                    "verification_callback."
                ),
            }

        try:

            verification = verification_callback(result)

            if isinstance(verification, dict):

                evidence = verification.get("evidence", [])

                verified = (
                    bool(verification.get("verified"))
                    and isinstance(evidence, list)
                    and bool(evidence)
                )

                return {
                    "verified": verified,
                    "evidence": (
                        evidence
                        if isinstance(evidence, list)
                        else []
                    ),
                    "reason": verification.get("reason"),
                }

            if isinstance(verification, bool):

                return {
                    "verified": False,
                    "evidence": [],
                    "reason": (
                        "Проверка вернула только логический результат "
                        "без подтверждающих данных."
                    ),
                }

            return {
                "verified": False,
                "evidence": [],
                "reason": "Неизвестный формат результата проверки.",
            }

        except Exception as exc:

            return {
                "verified": False,
                "evidence": [],
                "reason": str(exc),
            }

    # =========================================================
    # PARALLEL MODEL RESPONSE
    # =========================================================

    def _ask_model_safe(
        self,
        model: str,
        prompt: str,
        context,
        system_prompt: str,
    ) -> dict:
        """
        Безопасный вызов одной модели из отдельного потока.

        Ошибка одной модели не прерывает работу остальных.
        """

        try:

            result = self.ask_model(
                model=model,
                prompt=prompt,
                context=context,
                system_prompt=system_prompt,
            )

            if not isinstance(result, dict):

                return {
                    "success": False,
                    "complete": False,
                    "model": model,
                    "text": "",
                    "error": "Модель вернула результат неверного формата.",
                }

            result.setdefault("model", model)
            result.setdefault("success", False)
            result.setdefault("complete", False)
            result.setdefault("text", "")

            return result

        except Exception as exc:

            error = str(exc)

            self.last_errors[model] = error

            return {
                "success": False,
                "complete": False,
                "model": model,
                "text": "",
                "error": error,
            }

    # =========================================================
    # COORDINATION
    # =========================================================

    def coordinate(
        self,
        prompt: str,
        context=None,
        compare: bool = True,
        verify: bool = False,
        verification_callback: Optional[Callable] = None,
        max_models: int = 0,
    ) -> dict:

        started = time.time()

        task_type = self.classify_task(prompt)

        available = self.get_available_model_names()

        selected = self.select_models(task_type)

        if max_models and max_models > 0:
            selected = selected[:max_models]

        if not selected:

            return {
                "success": False,
                "complete": False,
                "verified": False,
                "task_type": task_type,
                "models_used": [],
                "responses": [],
                "answer": "",
                "comparison": None,
                "verification": {
                    "verified": False,
                    "evidence": [],
                    "reason": "Нет доступных моделей.",
                },
                "error": "Нет доступных моделей.",
                "elapsed": round(time.time() - started, 2),
            }

        system_prompt = self.build_system_prompt(task_type)

        responses_by_model = {}

        # Количество потоков ограничено настройкой,
        # чтобы не создавать неограниченную нагрузку на систему.
        worker_count = min(
            len(selected),
            MAX_PARALLEL_MODELS,
        )

        # -----------------------------------------------------
        # ЭТАП 1. ПАРАЛЛЕЛЬНЫЙ СБОР ОТВЕТОВ
        # -----------------------------------------------------

        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="ArmitageModel",
        ) as executor:

            future_to_model = {
                executor.submit(
                    self._ask_model_safe,
                    model,
                    prompt,
                    context,
                    system_prompt,
                ): model
                for model in selected
            }

            # Результаты принимаются по мере завершения моделей.
            # Порядок итогового списка ниже будет восстановлен
            # согласно исходному порядку selected.
            for future in as_completed(future_to_model):

                model = future_to_model[future]

                try:

                    result = future.result()

                except Exception as exc:

                    result = {
                        "success": False,
                        "complete": False,
                        "model": model,
                        "text": "",
                        "error": str(exc),
                    }

                    self.last_errors[model] = str(exc)

                responses_by_model[model] = result

        # Сохраняем исходный порядок выбора моделей,
        # независимо от того, какая модель ответила первой.
        responses = [
            responses_by_model[model]
            for model in selected
            if model in responses_by_model
        ]

        successful = [
            item
            for item in responses
            if item.get("success")
        ]

        # -----------------------------------------------------
        # ЭТАП 2. КОЛЛЕКТИВНЫЙ АНАЛИЗ И СИНТЕЗ
        # -----------------------------------------------------

        comparison = None

        if compare and successful:

            comparison_model = DEFAULT_COMPARISON_MODEL

            if comparison_model not in available:

                comparison_model = successful[0]["model"]

            comparison = self.compare_answers(
                prompt,
                successful,
                comparison_model,
            )

        # -----------------------------------------------------
        # ЭТАП 3. ФОРМИРОВАНИЕ ИТОГА
        # -----------------------------------------------------

        if comparison and comparison.get("success"):

            answer = comparison.get("text", "")
            final_model = comparison.get("model")
            complete = comparison.get("complete", False)

        elif successful:

            best = next(
                (
                    item
                    for item in successful
                    if item.get("complete")
                ),
                successful[0],
            )

            answer = best.get("text", "")
            final_model = best.get("model")
            complete = best.get("complete", False)

        else:

            answer = ""
            final_model = None
            complete = False

        # -----------------------------------------------------
        # ЭТАП 4. ПРОВЕРКА РЕЗУЛЬТАТА
        # -----------------------------------------------------

        verification_result = {
            "verified": False,
            "evidence": [],
            "reason": "Проверка не запрашивалась.",
        }

        if verify:

            source_result = {
                "success": bool(answer),
                "complete": complete,
                "model": final_model,
                "text": answer,
            }

            verification_result = self.verify_result(
                source_result,
                verification_callback,
            )

        # -----------------------------------------------------
        # ЭТАП 5. ФОРМИРОВАНИЕ ОТЧЁТА
        # -----------------------------------------------------

        return {
            "success": bool(answer),
            "complete": complete,
            "verified": verification_result.get("verified", False),

            "task_type": task_type,

            "available_models": available,

            "selected_models": selected,

            "models_used": [
                item.get("model")
                for item in responses
                if item.get("success")
            ],

            "responses": responses,

            "successful_models_count": len(successful),

            "failed_models_count": (
                len(responses) - len(successful)
            ),

            "answer": answer,

            "final_model": final_model,

            "comparison": comparison,

            "verification": verification_result,

            "errors": {
                **self.last_errors,
            },

            "usage": {
                **self.last_usage,
            },

            "parallel_execution": True,

            "parallel_workers": worker_count,

            "elapsed": round(time.time() - started, 2),

            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
        }

    # =========================================================
    # STATUS / DIAGNOSTICS
    # =========================================================

    def status(self) -> dict:

        ollama = self.list_models()

        provider_status = {}

        providers = (
            "openai",
            "openrouter",
            "groq",
            "gemini",
            "anthropic",
            "mistral",
            "deepseek",
            "cohere",
            "huggingface",
            "cloudflare",
            "nvidia",
            "replicate",
            "together",
            "fireworks",
            "perplexity",
        )

        for provider in providers:

            provider_status[provider] = {
                "has_key": self._provider_has_key(provider),
            }

        try:

            configured_providers = self.key_manager.list_providers()

            if isinstance(configured_providers, list):

                for item in configured_providers:

                    if not isinstance(item, dict):
                        continue

                    name = str(
                        item.get("provider") or ""
                    ).strip().lower()

                    if name in provider_status:

                        provider_status[name]["configured"] = bool(
                            item.get("configured")
                        )

                        provider_status[name]["credentials_count"] = (
                            item.get("credentials_count", 0)
                        )

            elif isinstance(configured_providers, dict):

                for name, item in configured_providers.items():

                    if (
                        name in provider_status
                        and isinstance(item, dict)
                    ):

                        provider_status[name]["configured"] = bool(
                            item.get("configured", True)
                        )

        except Exception as exc:

            self.last_errors["key_manager_status"] = str(exc)

        for provider in provider_status:

            provider_status[provider]["has_key"] = (
                self._provider_has_key(provider)
            )

        return {
            "ollama": ollama,
            "providers": provider_status,
            "available_models": self.get_available_model_names(),
            "parallel_execution": True,
            "max_parallel_models": MAX_PARALLEL_MODELS,
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
        }

    def test_classifier(self) -> list:

        tests = [
            ("Привет, как дела?", "simple"),
            ("Проанализируй архитектуру AI Core", "complex"),
            ("Напиши Python функцию", "code"),
            ("Проанализируй изображение", "vision"),
            ("Подключи микрофон и распознавание речи", "audio"),
            ("Проанализируй сложную задачу", "complex"),
        ]

        results = []

        for text, expected in tests:

            actual = self.classify_task(text)

            results.append({
                "input": text,
                "expected": expected,
                "actual": actual,
                "passed": expected == actual,
            })

        return results


# =============================================================
# PUBLIC API
# =============================================================

_default_coordinator = None


def get_coordinator() -> ModelCoordinator:

    global _default_coordinator

    if _default_coordinator is None:
        _default_coordinator = ModelCoordinator()

    return _default_coordinator


def check_gemini_connection() -> dict:
    """Проверяет Gemini напрямую, минуя общий координатор моделей."""
    return get_coordinator().check_gemini_connection()


def coordinate(
    prompt: str,
    context=None,
    compare: bool = True,
    verify: bool = False,
    verification_callback: Optional[Callable] = None,
    max_models: int = 0,
) -> dict:

    return get_coordinator().coordinate(
        prompt=prompt,
        context=context,
        compare=compare,
        verify=verify,
        verification_callback=verification_callback,
        max_models=max_models,
    )


def ask_model(
    model: str,
    prompt: str,
    context=None,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> dict:

    return get_coordinator().ask_model(
        model=model,
        prompt=prompt,
        context=context,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
    )


def get_available_model_names() -> list:

    return get_coordinator().get_available_model_names()


def get_status() -> dict:

    return get_coordinator().status()


# =============================================================
# CLI
# =============================================================

def main():

    coordinator = ModelCoordinator()

    print("=" * 60)
    print("ARMITAGE MODEL COORDINATOR")
    print("=" * 60)

    status = coordinator.status()

    print("\nOllama:")

    print(
        json.dumps(
            status["ollama"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\nПровайдеры:")

    print(
        json.dumps(
            status["providers"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\nДоступные модели:")

    print(
        json.dumps(
            status["available_models"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\nТест классификатора:")

    print(
        json.dumps(
            coordinator.test_classifier(),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\nВведите запрос. Для выхода введите exit.")

    while True:

        try:

            prompt = input("\nВы: ").strip()

        except (EOFError, KeyboardInterrupt):

            print()
            break

        if prompt.lower() in (
            "exit",
            "quit",
            "выход",
        ):
            break

        if not prompt:
            continue

        result = coordinator.coordinate(prompt)

        print("\nАрмитаж:")

        if result.get("success"):

            print(result.get("answer", ""))

            print(
                f"\nМодель синтеза: "
                f"{result.get('final_model')}"
            )

            print(
                f"Успешных моделей: "
                f"{result.get('successful_models_count')}"
            )

            print(
                f"Ошибок моделей: "
                f"{result.get('failed_models_count')}"
            )

            print(
                f"Параллельных потоков: "
                f"{result.get('parallel_workers')}"
            )

            print(
                f"Время: {result.get('elapsed')} сек."
            )

            print("\nИспользованные модели:")

            for model in result.get("models_used", []):
                print(f"- {model}")

        else:

            print("Не удалось получить ответ.")

            if result.get("error"):
                print(result["error"])

            for item in result.get("responses", []):

                if item.get("error"):

                    print(
                        f"{item.get('model')}: "
                        f"{item.get('error')}"
                    )


if __name__ == "__main__":
    main()