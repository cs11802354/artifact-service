"""Canonical-representation compiler.

A validated ArtifactSpec is the canonical representation. Each renderer turns
it into bytes for one output format. Only html/markdown are real; pdf/docx/
pptx are stubbed the same way the finance tools in ai-workforce are stubbed —
the dispatch path is real, the adapter body is not, so swapping in a real
renderer later is a one-function change.
"""

from __future__ import annotations

import html as html_escape

import bleach
import mistune

from app.models import ArtifactSpec

THEMES = {
    "default": {"accent": "#2563eb", "bg": "#ffffff", "fg": "#111827"},
    "dark": {"accent": "#60a5fa", "bg": "#0b0f19", "fg": "#e5e7eb"},
}

# escape=True (mistune's default) turns any raw HTML in the source into
# escaped text rather than passing it through — so `<script>` in a section
# renders as the literal string, never as a live tag. bleach.clean is a
# second, independent pass on top of that: it strips anything outside this
# allowlist and drops disallowed URL schemes (e.g. `javascript:` links)
# regardless of what mistune produced, so one library's bug isn't the only
# thing standing between agent-supplied content and the rendered page.
_markdown = mistune.create_markdown(escape=True)

_ALLOWED_TAGS = [
    "p", "strong", "em", "b", "i", "ul", "ol", "li", "a", "code", "pre",
    "blockquote", "br", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
]
_ALLOWED_ATTRS = {"a": ["href", "title"]}
_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def _render_content(content: str) -> str:
    rendered = _markdown(content)
    return bleach.clean(
        rendered,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )


def compile_html(spec: ArtifactSpec) -> bytes:
    theme = THEMES.get(spec.theme, THEMES["default"])
    title = html_escape.escape(spec.title)

    body_parts = []
    for section in spec.sections:
        heading = html_escape.escape(section.heading)
        content = _render_content(section.content)
        body_parts.append(f"<section><h2>{heading}</h2>{content}</section>")

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: {theme['bg']}; color: {theme['fg']}; \
max-width: 760px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
  h1 {{ color: {theme['accent']}; }}
  h2 {{ color: {theme['accent']}; font-size: 1.15rem; margin-top: 2rem; }}
  section {{ margin-bottom: 1rem; }}
</style>
</head>
<body>
<h1>{title}</h1>
{"".join(body_parts)}
</body>
</html>
"""
    return doc.encode("utf-8")


def compile_markdown(spec: ArtifactSpec) -> bytes:
    lines = [f"# {spec.title}", ""]
    for section in spec.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        lines.append(section.content)
        lines.append("")
    return "\n".join(lines).encode("utf-8")


RENDERERS = {
    "html": compile_html,
    "markdown": compile_markdown,
}


def compile_artifact(spec: ArtifactSpec) -> bytes:
    """Raises KeyError for formats with no renderer — callers check
    `spec.format in RENDERERS` first via STUB_FORMATS."""
    return RENDERERS[spec.format.value](spec)
