"""
Generates responses using Groq LLM with RAG context.
Falls back to direct chunk formatting if Groq is unavailable.
"""

import os
import groq as _groq_module
from utils.text import is_arabic
import config
from utils.logger import get_logger

logger = get_logger()

# ── Fallback strings (used when LLM unavailable) ─────────────────────────────

NO_ANSWER_EN = (
    "I don't have a confident answer for that in my knowledge base right now.\n\n"
    "Your question has been recorded. As I learn from new sources it will be answered "
    "in a future update.\n\n"
    "💡 **Tip:** Try rephrasing, or ask about a specific tool (e.g. *nmap*, *wireshark*)."
)

NO_ANSWER_AR = (
    "لا أملك إجابة مؤكدة لهذا السؤال في قاعدة معرفتي حالياً.\n\n"
    "تم تسجيل سؤالك وسيُجاب عليه مستقبلاً مع تعلم المزيد من المصادر.\n\n"
    "💡 **تلميح:** حاول إعادة الصياغة، أو اسأل عن أداة محددة مثل *nmap* أو *wireshark*."
)

# ── System prompts ────────────────────────────────────────────────────────────

SYSTEM_EN = """\
You are CJ-AI, an expert cybersecurity assistant specializing in information security, \
network security, penetration testing, malware analysis, CTF challenges, Linux, \
cryptography, OWASP, and related topics.

Answer only cybersecurity-related questions. Be concise, accurate, and practical. \
Use markdown formatting (code blocks for commands/code, bullet points for lists). \
Always respond in the same language as the user's question.

You have access to a knowledge base. Use the provided CONTEXT to ground your answer. \
If the context is relevant, prioritize it. If it is not sufficient, use your own expertise \
but stay factual. Cite sources from the context when available using their titles or URLs.\
"""

SYSTEM_AR = """\
أنت CJ-AI، مساعد متخصص في الأمن السيبراني وأمن المعلومات، خبير في: \
اختبار الاختراق، تحليل البرمجيات الخبيثة، أمن الشبكات، التشفير، CTF، \
Linux، OWASP، Kali Linux، وكل ما يتعلق بمجال الأمن.

أجب فقط على الأسئلة المتعلقة بالأمن السيبراني. كن دقيقاً وعملياً وموجزاً. \
استخدم تنسيق markdown (مربعات الكود للأوامر والكود، النقاط للقوائم). \
أجب دائماً بنفس لغة سؤال المستخدم.

لديك قاعدة معرفة. استخدم السياق المُقدَّم لتعزيز إجابتك. \
أعطِ الأولوية للسياق إن كان وثيق الصلة. اذكر المصادر إن توفرت.\
"""


def _get_client():
    """Return a Groq client, or None if no key configured."""
    key = config.GROQ_API_KEY
    if not key:
        return None
    return _groq_module.Groq(api_key=key)


def _source_badge(meta: dict) -> str:
    src = meta.get("source_name") or meta.get("source", "")
    url = meta.get("url") or meta.get("link") or ""
    if url:
        return f"[{src or 'Source'}]({url})"
    return src or ""


def _build_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    if not hits:
        return ""
    parts = []
    for i, hit in enumerate(hits[:5], 1):
        meta  = hit["metadata"]
        doc   = hit["document"]
        title = meta.get("title") or meta.get("question") or ""
        src   = meta.get("source_name") or meta.get("source", "")
        url   = meta.get("url") or meta.get("link") or ""

        header = f"[{i}]"
        if title:
            header += f" {title}"
        if src:
            header += f" — {src}"
        if url:
            header += f" ({url})"

        parts.append(f"{header}\n{doc[:800]}")
    return "\n\n---\n\n".join(parts)


def _extract_sources(hits: list[dict]) -> list[str]:
    sources = []
    for hit in hits[:5]:
        badge = _source_badge(hit["metadata"])
        if badge and badge not in sources:
            sources.append(badge)
    return sources


# ── Public API ────────────────────────────────────────────────────────────────

def build_response(
    query: str,
    hits: list[dict],
    history: list[dict] | None = None,
) -> tuple[str, str, list[str]]:
    """
    Returns (markdown_text, confidence_level, source_list).
    confidence: 'high' | 'medium' | 'low'

    Tries Groq LLM first; falls back to direct chunk formatting.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    arabic   = is_arabic(query)
    sources  = _extract_sources(hits)
    context  = _build_context(hits)
    client   = _get_client()

    # ── LLM path ─────────────────────────────────────────────────────────────
    if client:
        try:
            system = SYSTEM_AR if arabic else SYSTEM_EN
            if context:
                system += f"\n\n## CONTEXT\n\n{context}"

            messages = [{"role": "system", "content": system}]

            # Add last few conversation turns for context
            if history:
                for turn in history[-6:]:
                    role = turn.get("role")
                    content = turn.get("content", "")
                    if role in ("user", "assistant") and content:
                        messages.append({"role": role, "content": content})

            messages.append({"role": "user", "content": query})

            resp = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=config.LLM_TEMPERATURE,
            )
            text       = resp.choices[0].message.content.strip()
            confidence = "high" if hits else "medium"
            logger.debug("Groq answered (tokens: %d)", resp.usage.total_tokens)
            return text, confidence, sources

        except Exception as exc:
            logger.warning("Groq call failed (%s) — falling back to chunks.", exc)

    # ── Fallback: direct chunk formatting ────────────────────────────────────
    if not hits:
        return (NO_ANSWER_AR if arabic else NO_ANSWER_EN), "low", []

    best = hits[0]
    dist = best["distance"]
    meta = best["metadata"]
    doc  = best["document"]

    if dist <= config.DIST_HIGH and meta.get("type") == "qa":
        answer = meta.get("answer", doc)
        return answer, "high", sources

    if dist <= config.DIST_HIGH and meta.get("type") == "article":
        title = meta.get("title", "")
        lines = []
        if title:
            lines.append(f"### {title}")
        lines.append(doc[:1200])
        published = meta.get("published", "")
        if published:
            lines.append(f"\n*Published: {published}*")
        badge = _source_badge(meta)
        if badge:
            lines.append(f"\n📰 {badge}")
        return "\n\n".join(lines), "high", sources

    if dist <= config.DIST_MED:
        intro = "وجدت معلومات ذات صلة:\n\n" if arabic else "Here's the most relevant information I found:\n\n"
        parts = [intro]
        for hit in hits[:3]:
            h_meta  = hit["metadata"]
            h_doc   = hit["document"]
            h_title = h_meta.get("title") or h_meta.get("question") or ""
            if h_title:
                parts.append(f"**{h_title}**\n")
            parts.append(h_doc[:600])
            parts.append("\n---\n")
        return "".join(parts).rstrip("---\n"), "medium", sources

    return (NO_ANSWER_AR if arabic else NO_ANSWER_EN), "low", []
