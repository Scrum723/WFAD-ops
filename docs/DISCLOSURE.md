# Disclosure

Contest rule: disclose pre-existing code you incorporate. WFAD is a new ADK agent. It is not a migration of Doc or Leesa, and those products are not the submission runtime.

## This workspace

Grok (xAI) in this build workspace authored and edited the scaffold. It is an AI coding assistant, not the contest LLM and not production hosting. The judged model is **Gemini 3.5 Flash** via Vertex AI (Google AI Studio key as local fallback only).

## Doc Weather (NWS helpers only)

| Field | Value |
| --- | --- |
| Product | Doc Weather AGI / Decentralized Operations Center |
| Repos | https://github.com/Scrum723/DOC · https://github.com/Scrum723/Decentralized-Weather-AI-Platform-V-2-0 |
| Copied on | 2026-08-24 |
| What moved | The smallest NWS patterns from `backend/api/nws_integration.py`: User-Agent, `/points/{lat},{lon}`, `/alerts/active?point=`, nearest-station `/observations/latest`, forecast periods |
| What did not move | The Doc dashboard, FastAPI backend, Next.js site, Railway service, threat-shield scoring, chat, media pipeline (~180k-line platform) |

The Watch tool is a new sync `requests` client in `wfad/tools/watch.py`. It does not import the Doc backend.

## Leesa (social / email ops)

| Field | Value |
| --- | --- |
| Product | Leesa social-media liaison |
| Repo | https://github.com/Scrum723/Leesa |
| This week | **Not copied.** `disseminate_package` has an explicit skip placeholder. One Leesa posting client may be added only after the Firestore loop is on Cloud Run, and only if it works in about an hour. |
| What is not in this repo | The Leesa UI, Railway app, multi-platform dashboard |

## What judges should score

- New public repo: https://github.com/Scrum723/WFAD
- Framework: Google ADK (`root_agent` in `wfad/agent.py`)
- Model: `gemini-3.5-flash`
- Cloud: Cloud Run + Firestore + Pub/Sub (Vertex preferred in deploy)
- Tools: Watch, Forecast, Alert, Disseminate

Doc and Leesa remain on Railway for real operations. WFAD may call thin copies of their functions. They are not the contest app.
