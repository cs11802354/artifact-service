"""Structural QA — the only QA tier that's real for v1.

Semantic and visual QA (does the content make sense, does it look right
rendered) are not implemented; a request for them should be answered
honestly rather than faked, same as the finance-tool stubs.
"""

from __future__ import annotations

from html.parser import HTMLParser

from app.models import ArtifactFormat, ArtifactSpec, QAReport


class _BalancedTagChecker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []
        # Tags that legitimately have no closing tag.
        self._void = {"meta", "br", "hr", "img", "link", "input"}

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag not in self._void:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._void:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unbalanced tag: </{tag}>")
            return
        self.stack.pop()


def check_html(spec: ArtifactSpec, rendered: bytes) -> QAReport:
    checks = ["title-present", "balanced-tags", "sections-rendered"]
    failures = []

    text = rendered.decode("utf-8")

    if f"<title>{_esc(spec.title)}</title>" not in text:
        failures.append("rendered document is missing the expected <title>")

    parser = _BalancedTagChecker()
    parser.feed(text)
    if parser.stack:
        failures.append(f"unclosed tags: {parser.stack}")
    failures.extend(parser.errors)

    for section in spec.sections:
        if _esc(section.heading) not in text:
            failures.append(f"section heading missing from output: {section.heading!r}")

    return QAReport(passed=not failures, checks=checks, failures=failures)


def check_markdown(spec: ArtifactSpec, rendered: bytes) -> QAReport:
    checks = ["title-present", "sections-rendered", "non-empty"]
    failures = []

    text = rendered.decode("utf-8")

    if not text.strip():
        failures.append("rendered document is empty")
    if f"# {spec.title}" not in text:
        failures.append("rendered document is missing the expected H1 title")
    for section in spec.sections:
        if f"## {section.heading}" not in text:
            failures.append(f"section heading missing from output: {section.heading!r}")

    return QAReport(passed=not failures, checks=checks, failures=failures)


CHECKERS = {
    "html": check_html,
    "markdown": check_markdown,
}


def run_structural_qa(spec: ArtifactSpec, rendered: bytes) -> QAReport:
    return CHECKERS[spec.format.value](spec, rendered)


def _esc(s: str) -> str:
    import html as html_escape

    return html_escape.escape(s)
