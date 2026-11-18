# key_manager.py
# AI Core / Armitage
# Менеджер API-ключей, учётных данных и подключений к ИИ.
# Хранилище использует Windows DPAPI для защиты секретов.
# Файл: C:\AI_Core\key_manager.py

import os
import re
import json
import ctypes
import getpass
import secrets
import tempfile
import threading

from pathlib import Path
from typing import Optional


class KeyManager:
    """Управление ключами, учётными данными и разрешениями AI Core."""

    VERSION = 2

    PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "env": "OPENAI_API_KEY",
            "free": False,
            "url": "https://platform.openai.com/api-keys",
        },
        "gemini": {
            "name": "Google Gemini",
            "env": "GEMINI_API_KEY",
            "free": True,
            "url": "https://aistudio.google.com/apikey",
        },
        "anthropic": {
            "name": "Anthropic Claude",
            "env": "ANTHROPIC_API_KEY",
            "free": False,
            "url": "https://console.anthropic.com/",
        },
        "openrouter": {
            "name": "OpenRouter",
            "env": "OPENROUTER_API_KEY",
            "free": True,
            "url": "https://openrouter.ai/keys",
        },
        "groq": {
            "name": "Groq",
            "env": "GROQ_API_KEY",
            "free": True,
            "url": "https://console.groq.com/keys",
        },
        "mistral": {
            "name": "Mistral",
            "env": "MISTRAL_API_KEY",
            "free": True,
            "url": "https://console.mistral.ai/",
        },
        "deepseek": {
            "name": "DeepSeek",
            "env": "DEEPSEEK_API_KEY",
            "free": False,
            "url": "https://platform.deepseek.com/",
        },
        "cohere": {
            "name": "Cohere",
            "env": "COHERE_API_KEY",
            "free": True,
            "url": "https://dashboard.cohere.com/api-keys",
        },
        "huggingface": {
            "name": "Hugging Face",
            "env": "HF_TOKEN",
            "free": True,
            "url": "https://huggingface.co/settings/tokens",
        },
        "cloudflare": {
            "name": "Cloudflare Workers AI",
            "env": "CLOUDFLARE_API_TOKEN",
            "free": True,
            "url": "https://dash.cloudflare.com/",
        },
        "nvidia": {
            "name": "NVIDIA",
            "env": "NVIDIA_API_KEY",
            "free": True,
            "url": "https://build.nvidia.com/",
        },
        "replicate": {
            "name": "Replicate",
            "env": "REPLICATE_API_TOKEN",
            "free": False,
            "url": "https://replicate.com/account/api-tokens",
        },
        "together": {
            "name": "Together AI",
            "env": "TOGETHER_API_KEY",
            "free": False,
            "url": "https://api.together.ai/",
        },
        "fireworks": {
            "name": "Fireworks AI",
            "env": "FIREWORKS_API_KEY",
            "free": False,
            "url": "https://fireworks.ai/",
        },
        "perplexity": {
            "name": "Perplexity",
            "env": "PERPLEXITY_API_KEY",
            "free": False,
            "url": "https://www.perplexity.ai/",
        },
        "custom": {
            "name": "Пользовательский провайдер",
            "env": "",
            "free": False,
            "url": "",
        },
    }

    ENV_ALIASES = {
        "google": "GEMINI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "hf": "HF_TOKEN",
        "huggingface": "HF_TOKEN",
        "cloudflare": "CLOUDFLARE_API_TOKEN",
        "nvidia": "NVIDIA_API_KEY",
        "replicate": "REPLICATE_API_TOKEN",
        "together": "TOGETHER_API_KEY",
        "fireworks": "FIREWORKS_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
    }

    _lock = threading.RLock()

    def __init__(self, storage_path: Optional[str] = None):
        default_dir = Path.home() / ".armitage"
        default_dir.mkdir(parents=True, exist_ok=True)

        self.storage_path = Path(
            storage_path
            if storage_path
            else default_dir / "credentials.dat"
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =========================================================
    # WINDOWS DPAPI
    # =========================================================

    @staticmethod
    def _protect(data: bytes) -> bytes:
        if os.name != "nt":
            raise RuntimeError(
                "Защищённое хранилище поддерживается только Windows."
            )

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ("cbData", ctypes.c_ulong),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        buffer = ctypes.create_string_buffer(data)

        source = DATA_BLOB(
            len(data),
            ctypes.cast(
                buffer,
                ctypes.POINTER(ctypes.c_char),
            ),
        )

        destination = DATA_BLOB()

        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(DATA_BLOB),
            ctypes.c_wchar_p,
            ctypes.POINTER(DATA_BLOB),
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(DATA_BLOB),
        ]

        crypt32.CryptProtectData.restype = ctypes.c_int

        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p

        if not crypt32.CryptProtectData(
            ctypes.byref(source),
            "Armitage credentials",
            None,
            None,
            None,
            0,
            ctypes.byref(destination),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            return ctypes.string_at(
                destination.pbData,
                destination.cbData,
            )
        finally:
            kernel32.LocalFree(
                ctypes.cast(destination.pbData, ctypes.c_void_p)
            )

    @staticmethod
    def _unprotect(data: bytes) -> bytes:
        if os.name != "nt":
            raise RuntimeError(
                "Расшифровка хранилища поддерживается только Windows."
            )

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ("cbData", ctypes.c_ulong),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        buffer = ctypes.create_string_buffer(data)

        source = DATA_BLOB(
            len(data),
            ctypes.cast(
                buffer,
                ctypes.POINTER(ctypes.c_char),
            ),
        )

        destination = DATA_BLOB()

        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(DATA_BLOB),
            ctypes.POINTER(ctypes.c_wchar_p),
            ctypes.POINTER(DATA_BLOB),
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(DATA_BLOB),
        ]

        crypt32.CryptUnprotectData.restype = ctypes.c_int

        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p

        if not crypt32.CryptUnprotectData(
            ctypes.byref(source),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(destination),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            return ctypes.string_at(
                destination.pbData,
                destination.cbData,
            )
        finally:
            kernel32.LocalFree(
                ctypes.cast(destination.pbData, ctypes.c_void_p)
            )

    # =========================================================
    # STORAGE
    # =========================================================

    def _empty_store(self) -> dict:
        return {
            "version": self.VERSION,
            "providers": {},
            "permissions": {},
        }

    def _load(self) -> dict:
        with self._lock:
            if not self.storage_path.exists():
                return self._empty_store()

            try:
                encrypted = self.storage_path.read_bytes()
                raw = self._unprotect(encrypted)
                data = json.loads(raw.decode("utf-8"))

                if not isinstance(data, dict):
                    raise ValueError("Некорректный формат хранилища.")

                if "providers" not in data:
                    data = {
                        "version": self.VERSION,
                        "providers": data,
                        "permissions": {},
                    }

                if not isinstance(data["providers"], dict):
                    raise ValueError("Некорректный список провайдеров.")

                data.setdefault("version", self.VERSION)

                # Совместимость со старым хранилищем.
                if "permissions" not in data:
                    data["permissions"] = {}

                if not isinstance(data["permissions"], dict):
                    raise ValueError(
                        "Некорректный список разрешений провайдеров."
                    )

                return data

            except Exception as exc:
                raise RuntimeError(
                    "Не удалось прочитать защищённое хранилище. "
                    "Исходный файл не изменён."
                ) from exc

    def _save(self, data: dict) -> None:
        if os.name != "nt":
            raise RuntimeError(
                "Запись защищённого хранилища поддерживается только Windows."
            )

        with self._lock:
            raw = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")

            encrypted = self._protect(raw)

            self.storage_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=str(self.storage_path.parent),
                    prefix="armitage_",
                    suffix=".tmp",
                    delete=False,
                ) as temporary:
                    temporary_path = Path(temporary.name)
                    temporary.write(encrypted)
                    temporary.flush()
                    os.fsync(temporary.fileno())

                os.replace(
                    str(temporary_path),
                    str(self.storage_path),
                )

            finally:
                if (
                    temporary_path is not None
                    and temporary_path.exists()
                ):
                    try:
                        temporary_path.unlink()
                    except OSError:
                        pass

    # =========================================================
    # PROVIDER PERMISSIONS
    # =========================================================

    def get_provider_permission(self, provider: str) -> bool:
        """
        Проверяет постоянное разрешение на использование провайдера.

        По умолчанию разрешение отсутствует.
        """

        provider = self._normalize_provider(provider)
        data = self._load()

        permissions = data.get("permissions", {})

        return permissions.get(provider) is True

    def set_provider_permission(
        self,
        provider: str,
        allowed: bool = True,
    ) -> bool:
        """
        Сохраняет или отзывает разрешение на использование провайдера.

        Разрешение хранится в том же защищённом DPAPI-хранилище,
        отдельно от API-ключей.
        """

        provider = self._normalize_provider(provider)

        if not isinstance(allowed, bool):
            raise TypeError(
                "Значение разрешения должно быть True или False."
            )

        data = self._load()

        permissions = data.setdefault("permissions", {})
        permissions[provider] = allowed

        self._save(data)

        return allowed

    def revoke_provider_permission(self, provider: str) -> bool:
        """Отзывает ранее выданное разрешение."""

        provider = self._normalize_provider(provider)
        data = self._load()

        permissions = data.setdefault("permissions", {})

        was_allowed = permissions.get(provider) is True

        permissions[provider] = False

        self._save(data)

        return was_allowed

    def list_provider_permissions(self) -> dict:
        """Возвращает сохранённые разрешения без секретных данных."""

        data = self._load()

        return {
            provider: allowed is True
            for provider, allowed in data.get("permissions", {}).items()
        }

    # =========================================================
    # PROVIDERS
    # =========================================================

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        if not isinstance(provider, str):
            raise TypeError("Название провайдера должно быть строкой.")

        provider = provider.strip().lower()

        aliases = {
            "google": "gemini",
            "google gemini": "gemini",
            "claude": "anthropic",
            "hugging face": "huggingface",
            "hf": "huggingface",
            "cloudflare workers ai": "cloudflare",
            "together ai": "together",
            "fireworks ai": "fireworks",
            "nvidia nim": "nvidia",
        }

        provider = aliases.get(provider, provider)

        if not provider:
            raise ValueError("Название провайдера не может быть пустым.")

        if not re.fullmatch(r"[a-z0-9_.-]+", provider):
            raise ValueError(
                "Название провайдера содержит недопустимые символы."
            )

        return provider

    def list_catalog(self) -> list:
        result = []

        for provider_id, info in self.PROVIDERS.items():
            result.append({
                "provider": provider_id,
                "name": info["name"],
                "free_tier_candidate": info["free"],
                "url": info["url"],
                "configured": self.has_key(provider_id),
            })

        return result

    def add_provider(
        self,
        provider: str,
        name: str,
        base_url: str = "",
        free_tier_candidate: bool = False,
    ) -> None:
        provider = self._normalize_provider(provider)
        name = str(name).strip()

        if not name:
            raise ValueError("Укажи название провайдера.")

        if base_url:
            if not base_url.startswith(("https://", "http://")):
                raise ValueError(
                    "Адрес API должен начинаться с https:// или http://."
                )

        data = self._load()
        providers = data["providers"]

        entry = providers.get(provider, {})

        entry.setdefault("credentials", [])

        entry["name"] = name
        entry["base_url"] = base_url
        entry["free_tier_candidate"] = bool(free_tier_candidate)
        entry.setdefault("models", [])
        entry.setdefault("auth_type", "api_key")

        providers[provider] = entry

        self._save(data)

    def add_model(
        self,
        provider: str,
        model: str,
        free_tier_candidate: bool = False,
    ) -> None:
        provider = self._normalize_provider(provider)
        model = str(model).strip()

        if not model:
            raise ValueError("Название модели не может быть пустым.")

        data = self._load()
        entry = data["providers"].get(provider)

        if not entry:
            info = self.PROVIDERS.get(provider)

            if not info:
                raise ValueError(
                    "Сначала зарегистрируй пользовательского провайдера."
                )

            entry = {
                "name": info["name"],
                "base_url": "",
                "free_tier_candidate": info["free"],
                "credentials": [],
                "models": [],
                "auth_type": "api_key",
            }

            data["providers"][provider] = entry

        models = entry.setdefault("models", [])

        for item in models:
            if item.get("id") == model:
                item["free_tier_candidate"] = bool(free_tier_candidate)
                self._save(data)
                return

        models.append({
            "id": model,
            "free_tier_candidate": bool(free_tier_candidate),
        })

        self._save(data)

    # =========================================================
    # CREDENTIALS
    # =========================================================

    def add_key(
        self,
        provider: str,
        api_key: str,
        name: Optional[str] = None,
        key_id: Optional[str] = None,
    ) -> str:
        provider = self._normalize_provider(provider)

        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("API-ключ не может быть пустым.")

        api_key = api_key.strip()

        if len(api_key) > 10000:
            raise ValueError("Ключ имеет недопустимую длину.")

        data = self._load()
        providers = data["providers"]

        if provider not in providers:
            info = self.PROVIDERS.get(provider)

            if not info:
                raise ValueError(
                    "Неизвестный провайдер. "
                    "Сначала зарегистрируй его через add_provider()."
                )

            providers[provider] = {
                "name": info["name"],
                "base_url": "",
                "free_tier_candidate": info["free"],
                "credentials": [],
                "models": [],
                "auth_type": "api_key",
            }

        entry = providers[provider]
        credentials = entry.setdefault("credentials", [])

        if key_id:
            for credential in credentials:
                if credential.get("id") == key_id:
                    credential["secret"] = api_key
                    credential["name"] = (
                        name or credential.get("name") or "Основной ключ"
                    )
                    self._save(data)
                    return key_id

        credential_id = key_id or secrets.token_hex(8)

        credentials.append({
            "id": credential_id,
            "name": name or f"Ключ {len(credentials) + 1}",
            "secret": api_key,
            "type": "api_key",
            "enabled": True,
        })

        self._save(data)

        return credential_id

    def add_credential(
        self,
        provider: str,
        credential_type: str,
        values: dict,
        name: Optional[str] = None,
    ) -> str:
        provider = self._normalize_provider(provider)

        allowed_types = {
            "api_key",
            "oauth_token",
            "access_token",
            "username_password",
            "custom",
        }

        if credential_type not in allowed_types:
            raise ValueError("Неподдерживаемый тип учётных данных.")

        if not isinstance(values, dict) or not values:
            raise ValueError("Учётные данные должны быть словарём.")

        for key, value in values.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    "Названия полей и значения должны быть строками."
                )

        data = self._load()
        providers = data["providers"]

        if provider not in providers:
            info = self.PROVIDERS.get(provider)

            if not info:
                raise ValueError(
                    "Неизвестный провайдер. "
                    "Сначала зарегистрируй его через add_provider()."
                )

            providers[provider] = {
                "name": info["name"],
                "base_url": "",
                "free_tier_candidate": info["free"],
                "credentials": [],
                "models": [],
                "auth_type": credential_type,
            }

        credential_id = secrets.token_hex(8)

        providers[provider].setdefault("credentials", []).append({
            "id": credential_id,
            "name": name or credential_type,
            "type": credential_type,
            "values": values,
            "enabled": True,
        })

        self._save(data)

        return credential_id

    def get_key(self, provider: str, key_id: Optional[str] = None):
        provider = self._normalize_provider(provider)

        info = self.PROVIDERS.get(provider, {})
        env_name = info.get("env") or self.ENV_ALIASES.get(provider)

        if env_name:
            env_value = os.getenv(env_name, "").strip()

            if env_value and key_id is None:
                return env_value

        data = self._load()
        entry = data["providers"].get(provider, {})

        for credential in entry.get("credentials", []):
            if not credential.get("enabled", True):
                continue

            if credential.get("type") != "api_key":
                continue

            if key_id and credential.get("id") != key_id:
                continue

            secret = credential.get("secret")

            if secret:
                return secret

        return None

    def get_credential(
        self,
        provider: str,
        credential_id: str,
    ) -> Optional[dict]:
        provider = self._normalize_provider(provider)
        data = self._load()

        entry = data["providers"].get(provider, {})

        for credential in entry.get("credentials", []):
            if credential.get("id") != credential_id:
                continue

            if not credential.get("enabled", True):
                return None

            result = dict(credential)
            result.pop("id", None)

            return result

        return None

    def list_credentials(self, provider: Optional[str] = None) -> list:
        data = self._load()
        result = []

        providers = data["providers"]

        if provider is not None:
            provider = self._normalize_provider(provider)
            providers = {
                provider: providers.get(provider, {})
            }

        for provider_id, entry in providers.items():
            for credential in entry.get("credentials", []):
                secret = credential.get("secret", "")
                values = credential.get("values", {})

                result.append({
                    "provider": provider_id,
                    "provider_name": entry.get("name", provider_id),
                    "id": credential.get("id"),
                    "name": credential.get("name", "Подключение"),
                    "type": credential.get("type", "api_key"),
                    "enabled": credential.get("enabled", True),
                    "configured": bool(secret or values),
                    "masked": (
                        "*" * min(len(secret), 12)
                        if secret else (
                            "настроено" if values else ""
                        )
                    ),
                })

        return result

    def remove_key(
        self,
        provider: str,
        key_id: Optional[str] = None,
    ) -> bool:
        provider = self._normalize_provider(provider)
        data = self._load()

        entry = data["providers"].get(provider)

        if not entry:
            return False

        credentials = entry.get("credentials", [])

        if key_id is None:
            new_credentials = [
                item for item in credentials
                if item.get("type") != "api_key"
            ]
        else:
            new_credentials = [
                item for item in credentials
                if item.get("id") != key_id
            ]

        if len(new_credentials) == len(credentials):
            return False

        entry["credentials"] = new_credentials

        self._save(data)

        return True

    def remove_provider(self, provider: str) -> bool:
        provider = self._normalize_provider(provider)
        data = self._load()

        if provider not in data["providers"]:
            return False

        del data["providers"][provider]

        self._save(data)

        return True

    def set_credential_enabled(
        self,
        provider: str,
        credential_id: str,
        enabled: bool,
    ) -> bool:
        provider = self._normalize_provider(provider)
        data = self._load()

        entry = data["providers"].get(provider, {})

        for credential in entry.get("credentials", []):
            if credential.get("id") == credential_id:
                credential["enabled"] = bool(enabled)
                self._save(data)
                return True

        return False

    def has_key(self, provider: str) -> bool:
        return bool(self.get_key(provider))

    # =========================================================
    # STATUS
    # =========================================================

    def list_providers(self) -> list:
        data = self._load()
        result = []

        for provider_id, entry in data["providers"].items():
            credentials = entry.get("credentials", [])

            configured = any(
                credential.get("enabled", True)
                and (
                    credential.get("secret")
                    or credential.get("values")
                )
                for credential in credentials
            )

            info = self.PROVIDERS.get(provider_id, {})

            env_name = info.get("env") or self.ENV_ALIASES.get(
                provider_id
            )

            if env_name and os.getenv(env_name, "").strip():
                configured = True

            result.append({
                "provider": provider_id,
                "name": entry.get("name", provider_id),
                "configured": configured,
                "credentials_count": len(credentials),
                "models_count": len(entry.get("models", [])),
                "base_url": entry.get("base_url", ""),
                "free_tier_candidate": entry.get(
                    "free_tier_candidate",
                    info.get("free", False),
                ),
            })

        return result

    def status(self) -> dict:
        return {
            "version": self.VERSION,
            "storage_exists": self.storage_path.exists(),
            "storage_path": str(self.storage_path),
            "storage_protected": os.name == "nt",
            "providers": self.list_providers(),
            "credentials": self.list_credentials(),
            "permissions": self.list_provider_permissions(),
        }

    def get_provider_config(self, provider: str) -> Optional[dict]:
        provider = self._normalize_provider(provider)
        data = self._load()

        entry = data["providers"].get(provider)

        if entry is None:
            return None

        result = dict(entry)
        result.pop("credentials", None)

        return result

    # =========================================================
    # CLI
    # =========================================================

    def run_cli(self):
        while True:
            print()
            print("=" * 48)
            print("ARMITAGE — KEY MANAGER")
            print("=" * 48)
            print("1 — Добавить API-ключ")
            print("2 — Список провайдеров")
            print("3 — Список подключений")
            print("4 — Удалить ключ")
            print("5 — Добавить пользовательского провайдера")
            print("6 — Добавить модель")
            print("7 — Проверить наличие ключа")
            print("8 — Включить или отключить ключ")
            print("9 — Показать каталог провайдеров")
            print("10 — Проверить разрешение OpenAI")
            print("11 — Отозвать разрешение OpenAI")
            print("0 — Выход")

            choice = input("\nВыбери действие: ").strip()

            try:
                if choice == "0":
                    break

                elif choice == "1":
                    provider = input(
                        "Провайдер (например, gemini): "
                    ).strip()

                    name = input(
                        "Название ключа: "
                    ).strip()

                    api_key = getpass.getpass(
                        "API-ключ (ввод скрыт): "
                    )

                    credential_id = self.add_key(
                        provider,
                        api_key,
                        name or None,
                    )

                    print("Ключ сохранён.")
                    print("ID подключения:", credential_id)

                elif choice == "2":
                    providers = self.list_providers()

                    if not providers:
                        print("Провайдеров пока нет.")
                    else:
                        for item in providers:
                            print(
                                f"{item['provider']} — "
                                f"{item['name']} | "
                                f"ключей: {item['credentials_count']} | "
                                f"моделей: {item['models_count']}"
                            )

                elif choice == "3":
                    credentials = self.list_credentials()

                    if not credentials:
                        print("Подключений пока нет.")
                    else:
                        for item in credentials:
                            print(
                                f"{item['provider']} | "
                                f"{item['name']} | "
                                f"{item['type']} | "
                                f"{'включено' if item['enabled'] else 'выключено'} | "
                                f"{item['masked']}"
                            )

                elif choice == "4":
                    provider = input("Провайдер: ").strip()
                    key_id = input(
                        "ID ключа (Enter — удалить все API-ключи): "
                    ).strip()

                    if self.remove_key(provider, key_id or None):
                        print("Ключ удалён.")
                    else:
                        print("Ключ не найден.")

                elif choice == "5":
                    provider = input(
                        "ID провайдера (например, my_ai): "
                    ).strip()

                    name = input(
                        "Название провайдера: "
                    ).strip()

                    base_url = input(
                        "Базовый URL API (можно оставить пустым): "
                    ).strip()

                    free = input(
                        "Есть бесплатный уровень? (y/n): "
                    ).strip().lower() in ("y", "yes", "д", "да")

                    self.add_provider(
                        provider,
                        name,
                        base_url,
                        free,
                    )

                    print("Провайдер добавлен.")

                elif choice == "6":
                    provider = input("Провайдер: ").strip()
                    model = input("ID модели: ").strip()

                    free = input(
                        "Бесплатный уровень? (y/n): "
                    ).strip().lower() in ("y", "yes", "д", "да")

                    self.add_model(provider, model, free)

                    print("Модель добавлена.")

                elif choice == "7":
                    provider = input("Провайдер: ").strip()

                    print(
                        "Ключ найден."
                        if self.has_key(provider)
                        else "Ключ не найден."
                    )

                elif choice == "8":
                    provider = input("Провайдер: ").strip()
                    key_id = input("ID подключения: ").strip()

                    enabled = input(
                        "Включить? (y/n): "
                    ).strip().lower() in ("y", "yes", "д", "да")

                    if self.set_credential_enabled(
                        provider,
                        key_id,
                        enabled,
                    ):
                        print("Статус подключения изменён.")
                    else:
                        print("Подключение не найдено.")

                elif choice == "9":
                    for item in self.list_catalog():
                        print(
                            f"{item['provider']} — {item['name']} | "
                            f"кандидат на бесплатный уровень: "
                            f"{'да' if item['free_tier_candidate'] else 'нет'}"
                        )
                        if item["url"]:
                            print("  Сайт:", item["url"])

                elif choice == "10":
                    allowed = self.get_provider_permission("openai")

                    print(
                        "Постоянное разрешение OpenAI: "
                        + ("ВКЛЮЧЕНО" if allowed else "ОТКЛЮЧЕНО")
                    )

                elif choice == "11":
                    revoked = self.revoke_provider_permission("openai")

                    if revoked:
                        print("Разрешение OpenAI отозвано.")
                    else:
                        print("Разрешение OpenAI уже было отключено.")

                else:
                    print("Неизвестная команда.")

            except (ValueError, TypeError, RuntimeError, OSError) as exc:
                print("Ошибка:", exc)


def main():
    if os.name != "nt":
        print(
            "Защищённое хранилище требует Windows и DPAPI."
        )
        return

    try:
        manager = KeyManager()
        manager.run_cli()
    except Exception as exc:
        print("Не удалось запустить менеджер ключей:", exc)


if __name__ == "__main__":
    main()