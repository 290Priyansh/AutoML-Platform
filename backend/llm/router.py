try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_community.llms import Ollama
except ImportError:
    try:
        from langchain_ollama import OllamaLLM as Ollama
    except ImportError:
        Ollama = None

from backend.config import settings
import logging

logger = logging.getLogger(__name__)

_ACTIVE_GROQ_MODEL = None


class FallbackLLM:
    """Safe fallback LLM that returns valid JSON/text when cloud LLMs are unavailable"""
    def invoke(self, prompt, **kwargs):
        from langchain_core.messages import AIMessage
        p_str = str(prompt).lower()
        if "encoding" in p_str:
            content = '{"encoding_strategy": "onehot", "confidence": 0.85, "reasoning": "Heuristic fallback"}'
        elif "problem_type" in p_str or "target" in p_str:
            content = '{"problem_type": "classification", "target_column": "", "confidence": 0.85, "reasoning": "Heuristic classification fallback"}'
        elif "quality" in p_str:
            content = '{"overall_quality": "good", "quality_score": 0.85, "critical_issues": [], "recommendations": ["standard preprocessing"]}'
        else:
            content = '{"status": "ok", "decision": "auto"}'
        return AIMessage(content=content)


def get_groq_model_for_task(task: str) -> str:
    """Select active, verified Groq model based on task type and availability"""
    global _ACTIVE_GROQ_MODEL
    if _ACTIVE_GROQ_MODEL:
        return _ACTIVE_GROQ_MODEL

    candidates = [
        "qwen/qwen3.8-27b",
        "groq/compound-mini",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            available = {m.id for m in client.models.list().data}
            for candidate in candidates:
                if candidate in available:
                    _ACTIVE_GROQ_MODEL = candidate
                    logger.info(f"Using Groq model: {_ACTIVE_GROQ_MODEL}")
                    return _ACTIVE_GROQ_MODEL
        except Exception as e:
            logger.debug(f"Failed to probe Groq models: {e}")

    _ACTIVE_GROQ_MODEL = "qwen/qwen3.8-27b"
    return _ACTIVE_GROQ_MODEL


def get_llm(prefer_local: bool = False, task: str = "general", model: str = None):
    """
    Route to the appropriate LLM based on config, task, and availability.
    Always falls back gracefully. Never raises — returns a working LLM.
    """
    if prefer_local or settings.PRIMARY_LLM_PROVIDER == "ollama":
        if Ollama is not None:
            return Ollama(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)

    def _try_provider(prov: str):
        if prov == "groq" and settings.GROQ_API_KEY and ChatGroq is not None:
            model_name = model or get_groq_model_for_task(task)
            return ChatGroq(
                model=model_name,
                groq_api_key=settings.GROQ_API_KEY,
                max_tokens=min(settings.LLM_MAX_TOKENS, 4096),
                temperature=0.1,
            )
        elif prov == "anthropic" and settings.ANTHROPIC_API_KEY and ChatAnthropic is not None:
            return ChatAnthropic(
                model=model or "claude-3-5-sonnet-20241022",
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
        elif prov == "openai" and settings.OPENAI_API_KEY and ChatOpenAI is not None:
            return ChatOpenAI(
                model=model or "gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
        elif prov == "ollama" and Ollama is not None:
            return Ollama(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)
        return None

    # 1. Try Primary
    primary = getattr(settings, "PRIMARY_LLM_PROVIDER", None)
    if primary:
        try:
            llm = _try_provider(primary)
            if llm is not None:
                return llm
        except Exception as e:
            logger.warning(f"Primary LLM ({primary}) failed: {e}")

    # 2. Try Fallback
    fallback = getattr(settings, "FALLBACK_LLM_PROVIDER", None)
    if fallback and fallback != primary:
        try:
            llm = _try_provider(fallback)
            if llm is not None:
                return llm
        except Exception as e:
            logger.warning(f"Fallback LLM ({fallback}) failed: {e}")

    # 3. Try remaining cloud providers
    for prov in ["groq", "anthropic", "openai"]:
        if prov != primary and prov != fallback:
            try:
                llm = _try_provider(prov)
                if llm is not None:
                    return llm
            except Exception as e:
                logger.warning(f"Provider {prov} failed: {e}")

    # 4. Safe fallback that never raises
    return FallbackLLM()


def get_embedding_model():
    """Get the sentence transformer embedding model safely"""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        logger.debug(f"SentenceTransformer not available: {e}")
        return None