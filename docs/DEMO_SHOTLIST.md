# Demo shot list (cap 4:00)

Record after Cloud Run, Vertex or Gemini, and Firestore all exist. Mandatory frames: Cloud Run URL (`.run.app`), Cloud Console, a Firestore document appearing.

| Clock | Shot | What to show |
| --- | --- | --- |
| 0:00–0:20 | Friction | One sentence: an event arrives; WFAD writes a briefing, decides urgency, and sends the package. Cut from a messy human workflow (tabs, copy-paste) to the Cloud Run URL. |
| 0:20–1:00 | Architecture | The four-box mermaid in `ARCHITECTURE.md`. Say the words: Trigger → root_agent (Gemini 3.5 Flash on Cloud Run) → four tools → Firestore + one channel. Do not show Grok or Railway as the runtime. |
| 1:00–3:00 | Live run | Terminal or ADK UI. `POST /trigger` `{"location":"Rochester, NY","reason":"scheduled_briefing"}` **or** type that into `adk web`. Cut to Firestore `wfad_runs` — a new document with watch / briefing / severity. If Wednesday is done, show the one real email or X post. |
| 3:00–3:30 | Cloud Console proof | Cloud Run service page (URL ending in `.run.app`), Vertex or Gemini request logs, Firestore collection. Three screenshots, not a tour. |
| 3:30–4:00 | Buffer / disclosure | “Doc and Leesa are tools this agent can call; they are not this submission.” End. |

## Screenshots to capture (save in `~/Desktop/WFAD-video/`)

1. Firestore first doc — `byXSNEQDZkcBt4LC6JDk` (done if you already saved `01-firestore-first-run.png`).
2. Cloud Run service: https://console.cloud.google.com/run/detail/us-central1/wfad-agent?project=wfad-506515 → `02-cloud-run.png`
3. Live app: https://wfad-agent-kbahexw6ca-uc.a.run.app → `03-run-app-ui.png`
4. Firestore after Cloud Run / Pub/Sub: `jnNGy5TfyBshqERanbQV` or `gzMJdrmUy6vDM75Hfhhn` → `04-firestore-cloudrun-run.png`
5. Logs (Vertex/Gemini on Cloud Run): https://console.cloud.google.com/run/detail/us-central1/wfad-agent/logs?project=wfad-506515 → `05-cloud-run-logs.png`
6. Pub/Sub topic: https://console.cloud.google.com/cloudpubsub/topic/detail/wfad-triggers?project=wfad-506515 → `06-pubsub.png`
7. Gmail inbox: message **WFAD ROUTINE — Rochester, NY** → `07-outbound-email.png`

Do not spend a day on a Next.js skin. The Cloud Run URL plus Firestore console is the UI judges need.
