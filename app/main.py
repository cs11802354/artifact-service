"""Artifact API + orchestrator.

Pipeline: validate spec -> compile to canonical bytes -> structural QA ->
store -> stable URL. Unsupported formats (pdf/docx/pptx) and the repair loop
are stubbed: the dispatch path below is real for every format, only those
adapter bodies say "not connected" instead of faking output, mirroring how
the finance tools are stubbed in ai-workforce.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.auth import AuthDep, auth_enabled
from app.compiler import compile_artifact
from app.config import settings
from app.models import ArtifactResult, ArtifactSpec, STUB_FORMATS
from app.qa import run_structural_qa
from app.storage import new_id, save, url_for

app = FastAPI(title="Artifact Service")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/auth/status")
def auth_status():
    return {"required": auth_enabled()}


@app.post("/v1/artifacts", response_model=ArtifactResult, dependencies=[AuthDep])
def create_artifact(spec: ArtifactSpec) -> ArtifactResult:
    artifact_id = new_id()

    if spec.format.value in STUB_FORMATS:
        return ArtifactResult(
            id=artifact_id,
            status="stub_not_connected",
            format=spec.format,
            message=(
                f"{spec.format.value} rendering is not connected in this "
                "environment. Only html and markdown are live; tell the "
                "caller that rather than fabricating a document."
            ),
        )

    rendered = compile_artifact(spec)
    qa = run_structural_qa(spec, rendered)

    if not qa.passed:
        # The repair loop is stubbed too: report the QA failure honestly
        # instead of silently patching the document and re-checking.
        return ArtifactResult(
            id=artifact_id,
            status="qa_failed",
            format=spec.format,
            qa=qa,
            message="Structural QA failed and the repair loop is not connected yet.",
        )

    save(artifact_id, spec.format.value, rendered)
    url = url_for(artifact_id, spec.format.value, settings.base_url)

    return ArtifactResult(
        id=artifact_id,
        status="stored",
        format=spec.format,
        url=url,
        qa=qa,
    )


# Serve stored artifacts back out under a stable URL.
from fastapi.staticfiles import StaticFiles  # noqa: E402
from app.storage import DATA_DIR  # noqa: E402

DATA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=DATA_DIR), name="files")
