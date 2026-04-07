"""Convert agent Markdown responses to Telegram-safe HTML.

Telegram sendMessage with parse_mode=HTML accepts a small whitelist of tags:
<b>, <i>, <u>, <s>, <code>, <pre>, <a href>, <blockquote>.
Stray <, >, & must be escaped or Telegram returns HTTP 400.
"""

from __future__ import annotations

import re

TELEGRAM_MAX_LEN = 4096
_TRUNCATION_SUFFIX = "\n\n... (tronque)"


def md_to_telegram_html(text: str) -> str:
    """Convert common Markdown patterns to Telegram HTML."""
    # Code blocks (```lang\n...\n```) -> <pre>
    text = re.sub(
        r"```(?:\w+)?\n(.*?)```",
        r"<pre>\1</pre>",
        text,
        flags=re.DOTALL,
    )
    # Inline code (`...`) -> <code>
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Bold (**...**) -> <b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic (*...*) -> <i>
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Strikethrough (~~...~~) -> <s>
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    # Links [text](url) -> <a href="url">text</a>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Headers (### ... ) -> <b>
    text = re.sub(r"^#{1,6}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    return text


# Tags Telegram accepts in HTML parse mode.
_ALLOWED_TAGS = {
    "b", "strong",
    "i", "em",
    "u", "ins",
    "s", "strike", "del",
    "code", "pre",
    "a",
    "blockquote",
    "tg-spoiler",
}

_TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)(\s[^>]*)?>")
_BARE_AMP_RE = re.compile(r"&(?!(?:amp|lt|gt|quot|#\d+|#x[0-9a-fA-F]+);)")


def _sanitize_html(text: str) -> str:
    """Escape stray HTML metacharacters, preserving allowed tags."""
    text = _BARE_AMP_RE.sub("&amp;", text)

    out: list[str] = []
    pos = 0
    for match in _TAG_RE.finditer(text):
        out.append(text[pos:match.start()].replace("<", "&lt;").replace(">", "&gt;"))
        tag_name = match.group(2).lower()
        if tag_name in _ALLOWED_TAGS:
            out.append(match.group(0))
        else:
            out.append(match.group(0).replace("<", "&lt;").replace(">", "&gt;"))
        pos = match.end()
    out.append(text[pos:].replace("<", "&lt;").replace(">", "&gt;"))
    return "".join(out)


def format_for_telegram(text: str) -> str:
    """Convert Markdown to Telegram HTML, sanitize, and truncate."""
    text = md_to_telegram_html(text.strip())
    text = _sanitize_html(text)
    if len(text) <= TELEGRAM_MAX_LEN:
        return text
    keep = TELEGRAM_MAX_LEN - len(_TRUNCATION_SUFFIX)
    return text[:keep] + _TRUNCATION_SUFFIX
