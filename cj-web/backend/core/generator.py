"""
Converts RAG search results into a well-formatted markdown response.
No LLM required — uses the retrieved content directly.
"""

from utils.text import is_arabic
import config

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


def _source_badge(meta: dict) -> str:
    src = meta.get("source_name") or meta.get("source", "")
    url = meta.get("url") or meta.get("link") or ""
    if url:
        return f"[{src or 'Source'}]({url})"
    return src or ""


def build_response(query: str, hits: list[dict]) -> tuple[str, str, list[str]]:
    """
    Returns (markdown_text, confidence_level, source_list).
    confidence: 'high' | 'medium' | 'low'
    """
    if not hits:
        arabic = is_arabic(query)
        return (NO_ANSWER_AR if arabic else NO_ANSWER_EN), "low", []

    best = hits[0]
    dist = best["distance"]
    meta = best["metadata"]
    doc  = best["document"]

    sources: list[str] = []

    # ── High-confidence Q&A from knowledge base ──────────────────────────────
    if dist <= config.DIST_HIGH and meta.get("type") == "qa":
        answer = meta.get("answer", doc)
        badge = _source_badge(meta)
        if badge:
            sources.append(badge)
        return answer, "high", sources

    # ── High-confidence scraped article ──────────────────────────────────────
    if dist <= config.DIST_HIGH and meta.get("type") == "article":
        title = meta.get("title", "")
        lines = []
        if title:
            lines.append(f"### {title}")
        lines.append(doc[:1200])  # trim very long articles
        published = meta.get("published", "")
        if published:
            lines.append(f"\n*Published: {published}*")
        badge = _source_badge(meta)
        if badge:
            lines.append(f"\n📰 {badge}")
            sources.append(badge)
        return "\n\n".join(lines), "high", sources

    # ── Medium-confidence — show top results with labels ─────────────────────
    if dist <= config.DIST_MED:
        arabic = is_arabic(query)
        intro = (
            "وجدت معلومات ذات صلة قد تفيدك:\n\n"
            if arabic else
            "Here's the most relevant information I found:\n\n"
        )
        parts = [intro]
        for i, hit in enumerate(hits[:3]):
            h_meta = hit["metadata"]
            h_doc  = hit["document"]
            h_title = h_meta.get("title") or h_meta.get("question") or ""
            if h_title:
                parts.append(f"**{h_title}**\n")
            parts.append(h_doc[:600])
            badge = _source_badge(h_meta)
            if badge and badge not in sources:
                sources.append(badge)
                parts.append(f"\n📰 {badge}\n")
            parts.append("\n---\n")
        return "".join(parts).rstrip("---\n"), "medium", sources

    # ── Low confidence ────────────────────────────────────────────────────────
    arabic = is_arabic(query)
    return (NO_ANSWER_AR if arabic else NO_ANSWER_EN), "low", []
