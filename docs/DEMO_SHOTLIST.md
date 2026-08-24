# Demo shot list (cap 4:00)

Record after Cloud Run, Vertex or Gemini, and Firestore all exist. Mandatory frames: Cloud Run URL (`.run.app`), Cloud Console, a Firestore document appearing.

| Clock | Shot | What to show |
| --- | --- | --- |
| 0:00–0:20 | Friction | One sentence: an event arrives; WFAD writes a briefing, decides urgency, and sends the package. Cut from a messy human workflow (tabs, copy-paste) to the Cloud Run URL. |
| 0:20–1:00 | Architecture | The four-box mermaid in `ARCHITECTURE.md`. Say the words: Trigger → root_agent (Gemini 3.5 Flash on Cloud Run) → four tools → Firestore + one channel. Do not show Grok or Railway as the runtime. |
| 1:00–3:00 | Live run | Terminal or ADK UI. `POST /trigger` `{"location":"Rochester, NY","reason":"scheduled_briefing"}` **or** type that into `adk web`. Cut to Firestore `wfad_runs` — a new document with watch / briefing / severity. If Wednesday is done, show the one real email or X post. |
| 3:00–3:30 | Cloud Console proof | Cloud Run service page (URL ending in `.run.app`), Vertex or Gemini request logs, Firestore collection. Three screenshots, not a tour. |
| 3:30–4:00 | Buffer / disclosure | “Doc and Leesa are tools this agent can call; they are not this submission.” End. |

## Screenshots to capture as you build (today → Thursday)

1. `adk web wfad` local UI after one successful `watch_conditions` call.
2. Firestore console: first `wfad_runs` document (today’s skeleton).
3. Cloud Run service URL after `gcloud run deploy --source .` or `adk deploy cloud_run`.
4. Vertex AI / Gemini request in the Google Cloud console.
5. Pub/Sub topic `wfad-triggers` or Cloud Scheduler hitting `/trigger`.
6. One real outbound (email in Gmail or one X post) — Wednesday, required for the video.

Do not spend a day on a Next.js skin. The Cloud Run URL plus Firestore console is the UI judges need.
