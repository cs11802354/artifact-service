# artifact-service

Artifact generation API for agentic workflows: an agent posts a spec, gets
back a validated, QA'd document at a stable URL.

```
Agent -> POST /v1/artifacts -> validate -> compile -> structural QA -> store -> URL
```

## Status

- **Real**: spec validation (Pydantic), HTML + Markdown compilation, structural
  QA (balanced tags, required title/headings present), local-disk storage with
  a stable `/files/{id}.{ext}` URL.
- **Stubbed** (dispatch path is real, adapter body says "not connected" rather
  than fabricating output): PDF, DOCX, PPTX rendering; the QA repair loop;
  semantic/visual QA. Each is a self-contained function to fill in later.

## Run

```
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8090
```

## Test

```
pytest
```

## Deploy

Same shape as `ai-workforce`'s deploy: `docker-compose.yml` builds and runs
one service, `.github/workflows/deploy.yml` runs on a `[self-hosted, linux]`
runner on push to `main` (`docker compose build` -> `docker compose up -d` ->
health check on `/healthz`). Storage is a named volume (`artifact_data`)
mounted at `/data/artifacts`, so artifacts survive a redeploy.

This needs its own self-hosted runner registered against *this* repo (Settings
-> Actions -> Runners) — it does not share ai-workforce's runner registration
even if it ends up on the same host. Also set `ARTIFACT_BASE_URL` in the
deploy environment's `.env` to whatever address callers can actually reach
(a public hostname behind a reverse proxy, same as `ai-workforce`'s
`ai-workforce-api.manishlab.dev`) — the default `localhost` value only works
for local dev.

To point ai-workforce's `artifact_generator` tool at a deployed instance, set
`ARTIFACT_SERVICE_URL` (and `ARTIFACT_API_KEY` if this service has one
configured) in ai-workforce's environment to this service's `ARTIFACT_BASE_URL`.

## Config

| Env var | Default | Purpose |
|---|---|---|
| `ARTIFACT_DATA_DIR` | `/data/artifacts` | Where rendered artifacts are stored |
| `ARTIFACT_BASE_URL` | `http://localhost:8090` | Base URL used to build the returned artifact URL |
| `ARTIFACT_API_KEY` | unset | If set, `/v1/artifacts` requires `Authorization: Bearer <key>` |

## API

`POST /v1/artifacts`

```json
{
  "title": "Q3 Board Update",
  "format": "html",
  "sections": [
    {"heading": "Summary", "content": "Revenue grew 12% quarter over quarter."}
  ],
  "theme": "default"
}
```

Returns `{id, status, format, url, qa, message}`. `status` is one of
`stored`, `qa_failed`, or `stub_not_connected`.
