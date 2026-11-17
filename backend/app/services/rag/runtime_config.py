from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List

from app.services.rag.config import get_rag_settings

logger = logging.getLogger(__name__)

_CONFIG_LOCK = threading.Lock()

VALID_OUT_OF_SCOPE_MODES = ("strict", "general_travel", "open_ai")

PROVIDER_PRESETS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
        "supports_embeddings": True,
    },
    "groq": {
        "label": "Groq (Llama / Mixtral)",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "supports_embeddings": False,
    },
    "gemini": {
        "label": "Google Gemini (OpenAI-compatible)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "supports_embeddings": False,
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.3-70b-instruct",
        ],
        "supports_embeddings": False,
    },
    "custom": {
        "label": "Custom OpenAI-Compatible Endpoint",
        "base_url": "",
        "models": [],
        "supports_embeddings": False,
    },
    "local_fallback": {
        "label": "Local Fallback (Không gọi LLM ngoài)",
        "base_url": "",
        "models": ["local-template"],
        "supports_embeddings": False,
    },
}

DEFAULT_OUT_OF_SCOPE_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI du lịch thông minh và lịch sự của hệ thống đặt tour. "
    "Câu hỏi hiện tại của khách nằm ngoài danh mục tour hoặc dữ liệu có sẵn trong hệ thống. "
    "Hãy trả lời ngắn gọn, hữu ích bằng tiếng Việt, không bịa đặt các tour hay mức giá không tồn tại trong dữ liệu hệ thống, "
    "và khéo léo hỗ trợ khách quay lại khám phá các tour phù hợp nếu cần."
)

DEFAULT_OUT_OF_SCOPE_FALLBACK_MESSAGE = (
    "Hiện tại hệ thống chưa có tour hoặc thông tin chi tiết khớp trực tiếp với yêu cầu này trong danh mục. "
    "Bạn có thể hỏi rõ hơn về điểm đến, ngân sách hoặc tham khảo một số tour nổi bật dưới đây."
)


def _infer_provider_from_base_url(base_url: str) -> str:
    lowered = str(base_url or "").lower()
    if "groq.com" in lowered:
        return "groq"
    if "generativelanguage.googleapis.com" in lowered:
        return "gemini"
    if "openrouter.ai" in lowered:
        return "openrouter"
    if "api.openai.com" in lowered or not lowered:
        return "openai"
    return "custom"


def _config_file_path() -> Path:
    settings = get_rag_settings()
    return settings.rag_dir / "runtime_config.json"


def _default_runtime_config() -> Dict[str, Any]:
    settings = get_rag_settings()
    env_base_url = os.getenv("OPENAI_BASE_URL", settings.openai_base_url).rstrip("/")
    env_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    env_chat_model = os.getenv("OPENAI_MODEL", settings.default_chat_model).strip() or "gpt-4o-mini"
    env_embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", settings.default_embedding_model).strip() or "text-embedding-3-small"

    return {
        "llm_provider": _infer_provider_from_base_url(env_base_url),
        "openai_base_url": env_base_url,
        "openai_api_key": env_api_key,
        "chat_model": env_chat_model,
        "embedding_model": env_embedding_model,
        "temperature": float(settings.answer_temperature),
        "max_tokens": int(settings.answer_max_tokens),
        "top_k_default": 4,
        "hybrid_dense_weight": float(settings.hybrid_dense_weight),
        "hybrid_lexical_weight": float(settings.hybrid_lexical_weight),
        "reranker_enabled": bool(settings.reranker_enabled),
        "reranker_model": str(settings.reranker_model),
        "knowledge_base_enabled": bool(settings.knowledge_base_enabled),
        "custom_system_prompt_addon": "",
        "out_of_scope_mode": "general_travel",
        "out_of_scope_model": "",
        "out_of_scope_temperature": 0.5,
        "out_of_scope_max_tokens": 400,
        "similarity_threshold": 0.22,
        "suggest_popular_tours_on_oos": True,
        "out_of_scope_system_prompt": DEFAULT_OUT_OF_SCOPE_SYSTEM_PROMPT,
        "out_of_scope_fallback_message": DEFAULT_OUT_OF_SCOPE_FALLBACK_MESSAGE,
    }


def _clamp_float(value: Any, low: float, high: float, default: float) -> float:
    try:
        num = float(value)
    except Exception:
        return default
    return max(low, min(high, num))


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        num = int(value)
    except Exception:
        return default
    return max(low, min(high, num))


def _mask_api_key(api_key: str) -> str:
    cleaned = str(api_key or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) <= 8:
        return "*" * len(cleaned)
    return f"{cleaned[:4]}****{cleaned[-4:]}"


def _sanitize_config(raw: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(defaults)
    merged.update(raw or {})

    provider = str(merged.get("llm_provider") or defaults["llm_provider"]).strip().lower()
    if provider not in PROVIDER_PRESETS:
        provider = "custom"

    oos_mode = str(merged.get("out_of_scope_mode") or "general_travel").strip().lower()
    if oos_mode not in VALID_OUT_OF_SCOPE_MODES:
        oos_mode = "general_travel"

    dense_w = _clamp_float(merged.get("hybrid_dense_weight"), 0.0, 1.0, defaults["hybrid_dense_weight"])
    lexical_w = _clamp_float(merged.get("hybrid_lexical_weight"), 0.0, 1.0, defaults["hybrid_lexical_weight"])
    if dense_w + lexical_w <= 0:
        dense_w, lexical_w = defaults["hybrid_dense_weight"], defaults["hybrid_lexical_weight"]

    return {
        "llm_provider": provider,
        "openai_base_url": str(merged.get("openai_base_url") or defaults["openai_base_url"]).strip().rstrip("/"),
        "openai_api_key": str(merged.get("openai_api_key") or "").strip(),
        "chat_model": str(merged.get("chat_model") or defaults["chat_model"]).strip() or defaults["chat_model"],
        "embedding_model": str(merged.get("embedding_model") or defaults["embedding_model"]).strip() or defaults["embedding_model"],
        "temperature": round(_clamp_float(merged.get("temperature"), 0.0, 2.0, defaults["temperature"]), 2),
        "max_tokens": _clamp_int(merged.get("max_tokens"), 50, 4096, defaults["max_tokens"]),
        "top_k_default": _clamp_int(merged.get("top_k_default"), 1, 8, defaults["top_k_default"]),
        "hybrid_dense_weight": round(dense_w, 2),
        "hybrid_lexical_weight": round(lexical_w, 2),
        "reranker_enabled": bool(merged.get("reranker_enabled")),
        "reranker_model": str(merged.get("reranker_model") or defaults["reranker_model"]).strip() or defaults["reranker_model"],
        "knowledge_base_enabled": bool(merged.get("knowledge_base_enabled")),
        "custom_system_prompt_addon": str(merged.get("custom_system_prompt_addon") or "").strip(),
        "out_of_scope_mode": oos_mode,
        "out_of_scope_model": str(merged.get("out_of_scope_model") or "").strip(),
        "out_of_scope_temperature": round(_clamp_float(merged.get("out_of_scope_temperature"), 0.0, 2.0, defaults["out_of_scope_temperature"]), 2),
        "out_of_scope_max_tokens": _clamp_int(merged.get("out_of_scope_max_tokens"), 50, 4096, defaults["out_of_scope_max_tokens"]),
        "similarity_threshold": round(_clamp_float(merged.get("similarity_threshold"), 0.0, 1.0, defaults["similarity_threshold"]), 2),
        "suggest_popular_tours_on_oos": bool(merged.get("suggest_popular_tours_on_oos")),
        "out_of_scope_system_prompt": str(merged.get("out_of_scope_system_prompt") or DEFAULT_OUT_OF_SCOPE_SYSTEM_PROMPT).strip(),
        "out_of_scope_fallback_message": str(merged.get("out_of_scope_fallback_message") or DEFAULT_OUT_OF_SCOPE_FALLBACK_MESSAGE).strip(),
    }


def get_runtime_config() -> Dict[str, Any]:
    defaults = _default_runtime_config()
    path = _config_file_path()
    with _CONFIG_LOCK:
        if path.exists():
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    # Respect env OPENAI_API_KEY if saved key is empty
                    if not saved.get("openai_api_key") and defaults.get("openai_api_key"):
                        saved["openai_api_key"] = defaults["openai_api_key"]
                    return _sanitize_config(saved, defaults)
            except Exception:
                logger.warning("Failed to parse runtime_config.json, using defaults", exc_info=False)
        return _sanitize_config({}, defaults)


def apply_runtime_override(base_config: Dict[str, Any], override: Dict[str, Any] | None) -> Dict[str, Any]:
    if not override:
        return dict(base_config)
    defaults = _default_runtime_config()
    merged = dict(base_config)
    for key, value in override.items():
        if value is None:
            continue
        if key == "openai_api_key":
            text = str(value).strip()
            if not text or "****" in text:
                continue
            merged[key] = text
        else:
            merged[key] = value
    return _sanitize_config(merged, defaults)


def get_public_runtime_config() -> Dict[str, Any]:
    cfg = get_runtime_config()
    raw_key = cfg.get("openai_api_key") or ""
    public_cfg = dict(cfg)
    public_cfg["openai_api_key"] = _mask_api_key(raw_key)
    public_cfg["has_api_key"] = bool(raw_key)
    public_cfg["effective_out_of_scope_model"] = (
        cfg.get("out_of_scope_model") or cfg.get("chat_model") or "gpt-4o-mini"
    )
    public_cfg["provider_presets"] = PROVIDER_PRESETS
    public_cfg["out_of_scope_modes"] = [
        {
            "value": "strict",
            "label": "Strict — Chỉ trả lời dữ liệu trong danh mục",
            "description": "Từ chối lịch sự theo mẫu câu cài đặt khi câu hỏi không nằm trong dữ liệu tour/du lịch.",
        },
        {
            "value": "general_travel",
            "label": "General Travel — Dùng Model riêng tư vấn du lịch mở rộng",
            "description": "Gọi Model Out-of-Scope giải đáp kiến thức du lịch hữu ích, báo rõ chưa có tour khớp và gợi ý tour nổi bật.",
        },
        {
            "value": "open_ai",
            "label": "Open AI — Dùng Model riêng trả lời linh hoạt mọi chủ đề",
            "description": "Cho phép Model Out-of-Scope trả lời tự nhiên câu hỏi ngoài lề theo System Prompt tùy chỉnh.",
        },
    ]
    return public_cfg


def update_runtime_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    defaults = _default_runtime_config()
    path = _config_file_path()
    with _CONFIG_LOCK:
        current = {}
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    current = loaded
            except Exception:
                current = {}

        base = _sanitize_config(current, defaults)
        incoming = dict(updates or {})
        clear_api_key = bool(incoming.pop("clear_api_key", False))

        if clear_api_key:
            incoming["openai_api_key"] = ""
        elif "openai_api_key" in incoming:
            raw_incoming_key = incoming.get("openai_api_key")
            masked_existing = _mask_api_key(base.get("openai_api_key", ""))
            if raw_incoming_key is None:
                incoming.pop("openai_api_key", None)
            else:
                text_key = str(raw_incoming_key).strip()
                if not text_key or "****" in text_key or text_key == masked_existing:
                    incoming["openai_api_key"] = base.get("openai_api_key", "")
                else:
                    incoming["openai_api_key"] = text_key

        merged = dict(base)
        for key, value in incoming.items():
            if value is not None:
                merged[key] = value

        sanitized = _sanitize_config(merged, defaults)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2), encoding="utf-8")

    return get_public_runtime_config()
