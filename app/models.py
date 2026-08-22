"""Wire types for the Artifact API.

An ArtifactSpec is the canonical input: a title, an output format, and an
ordered list of sections. The compiler turns a validated spec into rendered
bytes; nothing downstream ever sees an unvalidated spec.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

SUPPORTED_FORMATS = {"html", "markdown"}
STUB_FORMATS = {"pdf", "docx", "pptx"}


class ArtifactFormat(str, Enum):
    html = "html"
    markdown = "markdown"
    pdf = "pdf"
    docx = "docx"
    pptx = "pptx"


class ArtifactSection(BaseModel):
    heading: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)


class ArtifactSpec(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    format: ArtifactFormat
    sections: list[ArtifactSection] = Field(min_length=1, max_length=50)
    theme: str = "default"

    @field_validator("sections")
    @classmethod
    def unique_headings(cls, sections: list[ArtifactSection]) -> list[ArtifactSection]:
        seen = set()
        for s in sections:
            if s.heading in seen:
                raise ValueError(f"duplicate section heading: {s.heading!r}")
            seen.add(s.heading)
        return sections


class QAReport(BaseModel):
    passed: bool
    checks: list[str]
    failures: list[str]


class ArtifactResult(BaseModel):
    id: str
    status: str  # "stored" | "stub_not_connected" | "qa_failed"
    format: ArtifactFormat
    url: str | None = None
    qa: QAReport | None = None
    message: str | None = None
