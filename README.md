# WFAD-ops — Story desk fork

**This is not the contest submission.** Contest code, video, and `.run.app` stay on [`Scrum723/WFAD`](https://github.com/Scrum723/WFAD) through judging. After 31 August 2026, 5:00 p.m. PT, new work lives here.

Story desk is an **addition to WFAD** (same `root_agent`), not a new agent. Doc and Leesa remain the front brains. See [`docs/STACK.md`](docs/STACK.md) and [`docs/STORY_DESK.md`](docs/STORY_DESK.md).

```text
Watch Rochester, then draft a story hit.
Revise: lead with tonight.
Approve the package for Leesa.
```

Approve writes `~/Desktop/Doc Weather Content/bundles/<slug>/` (`insight.md`, `meta.yaml`). Leesa posts. WFAD does not.

## Desk website (testable UI)

Grok-style chat. Gemini 3.5 Flash understands the ask. Autopilot runs Watch → Forecast → Alert → Story and **stops for your approval**.

```bash
cd ~/WFAD-ops
source ~/WFAD/.venv/bin/activate   # or python3 -m venv .venv && pip install -r requirements.txt
python -m desk.app
# open http://127.0.0.1:8788
```

Toggle **Autopilot**. Try: `Rochester 5-day hit for socials`. Click **Approve** to write the Leesa bundle. LLM is Gemini (`WFAD_AGENT_MODEL`). Media stays `MEDIA_PROVIDER=stub` until an AI Studio/Vertex key is set.

# WFAD — Watch, Forecast, Alert, Disseminate

**Track:** Taskmaster (contest parent)

An event arrives; the agent writes a briefing, decides urgency, and sends the package without a human driving each step.

This is a **new** Google ADK agent on Cloud Run. It is not the Doc dashboard and not the Leesa UI. Those products stay where they are. WFAD may call thin copies of their functions; they are disclosed in [`docs/DISCLOSURE.md`](docs/DISCLOSURE.md).

## Friction

Broadcast weather ops still wait on a person to pull NWS, write the hit, pick who gets it, and press send. WFAD is one root agent with four tools that does that loop when a trigger fires — scheduled briefing or a hazard — and writes the run to Firestore so there is a receipt.

## Stack (judged path)

| Requirement | What we use |
| --- | --- |
| Gemini 3.5 or newer | `gemini-3.5-flash` (Vertex in deploy; Google AI Studio key as local fallback) |
| Google agent framework | Agent Development Kit (`wfad/agent.py` exports `root_agent`) |
| Google Cloud service | Cloud Run + Firestore + Pub/Sub |

BYOF: Western New York broadcast ops. Watch is a thin NWS client adapted from Doc. Disseminate may later call one Leesa posting client. The contest app itself is this Cloud Run service, not Railway.

**Not in the architecture:** Grok as the contest LLM, this sandbox as hosting, xAI APIs as a runtime dependency.

## Layout

```
wfad-agent/          (this repo: github.com/Scrum723/WFAD)
  README.md
  ARCHITECTURE.md
  requirements.txt
  main.py            # Cloud Run: ADK FastAPI + /trigger
  Dockerfile
  wfad/
    __init__.py      # from .agent import root_agent
    agent.py         # root_agent, model=gemini-3.5-flash
    prompts.py
    tools/
      watch.py       # NWS
      forecast.py    # briefing formatter
      alert.py       # severity + routing rules
      disseminate.py # Firestore + email stub/SMTP
      store.py       # record_run
  trigger/
    pubsub_handler.py
  docs/
    DISCLOSURE.md
    DEMO_SHOTLIST.md
```

## Local spin-up (today)

```bash
cd WFAD
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
cp .env.example wfad/.env
# set GOOGLE_CLOUD_PROJECT and either Vertex ADC or GOOGLE_API_KEY

gcloud auth application-default login
gcloud config set project wfad-506515

adk web wfad
```

In the ADK UI, ask: `Run WFAD for Rochester, NY, reason scheduled_briefing.` Confirm `watch_conditions` returns NWS data, then `record_run`.

Smoke the Watch tool without a model key:

```bash
python -m wfad.tools.watch "Rochester, NY"
```

Demo trigger (same contract as Pub/Sub, once the API server is up):

```bash
curl -sS -X POST http://127.0.0.1:8080/trigger \
  -H 'Content-Type: application/json' \
  -d '{"location":"Rochester, NY","reason":"scheduled_briefing"}'
```

## Google Cloud (project `wfad-506515`)

Account `cclottin@gmail.com`, billing on, APIs enabled, Firestore Native in `nam5` as named database **`wfad`**. SDK lives at `~/google-cloud-sdk` (sourced from `~/.zshrc`).

Still do if not already done:

1. Register on [allthingsagentichackathon.devpost.com](https://allthingsagentichackathon.devpost.com).
2. Request the $150 Cloud credits before **28 August 12:00 p.m. PT**: https://forms.gle/riGhgDSHkHeMx8Ca6
3. Gemini API key in Google AI Studio as laptop fallback; prefer Vertex in the deployed service.

```bash
export GOOGLE_CLOUD_PROJECT=wfad-506515
export GOOGLE_CLOUD_LOCATION=us-central1
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

### Deploy (official ADK-on-Cloud Run path)

From this parent folder, either:

```bash
# Recommended by ADK docs
adk deploy cloud_run \
  --project=wfad-506515 \
  --region=us-central1 \
  --service_name=wfad-agent \
  --with_ui \
  ./wfad \
  -- \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=wfad-506515,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_GENAI_USE_ENTERPRISE=TRUE,FIRESTORE_DATABASE=wfad,FIRESTORE_COLLECTION=wfad_runs"
```

or source-deploy with the included Dockerfile / `main.py` (URL still ends in `.run.app`):

```bash
gcloud run deploy wfad-agent \
  --source . \
  --region us-central1 \
  --project wfad-506515 \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=wfad-506515,GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_GENAI_USE_ENTERPRISE=TRUE,FIRESTORE_DATABASE=wfad,FIRESTORE_COLLECTION=wfad_runs"
```

**Live service (us-central1):** https://wfad-agent-kbahexw6ca-uc.a.run.app

```bash
curl -sS -X POST https://wfad-agent-kbahexw6ca-uc.a.run.app/trigger \
  -H 'Content-Type: application/json' \
  -d '{"location":"Rochester, NY","reason":"scheduled_briefing"}'
```

Background proof already in this project:

- Pub/Sub topic `wfad-triggers`, push subscription `wfad-triggers-push` → `/trigger` (ack 120s)
- Cloud Scheduler job `wfad-scheduled-briefing` daily 14:30 America/New_York
- Firestore database `wfad`, collection `wfad_runs` (Pub/Sub run example: `gzMJdrmUy6vDM75Hfhhn`)

```bash
gcloud pubsub topics publish wfad-triggers --project=wfad-506515 \
  --message='{"location":"Rochester, NY","reason":"pubsub_push"}'
```

One real email went to `cclottin@gmail.com` (subject `WFAD ROUTINE — Rochester, NY`) with the Cloud Run briefing. Cloud Run `disseminate_package` still labels SMTP as a stub until `SMTP_*` secrets are set on the service.

## What not to do

- Do not deploy the existing Railway apps and call that Google Cloud.
- Do not start Fortified Enterprise pieces until this loop is on Cloud Run.
- Do not spend a day on a Next.js skin.
- Do not rename the project again.

## Schedule

| When | Status |
| --- | --- |
| Skeleton + first Firestore doc | Done (`byXSNEQDZkcBt4LC6JDk`) |
| Cloud Run loop | Done — `.run.app`, Vertex env, four tools |
| Pub/Sub + Scheduler | Done — topic `wfad-triggers`, job `wfad-scheduled-briefing` |
| One real outbound | Done — email to `cclottin@gmail.com` |
| Thursday video | Record from `docs/DEMO_SHOTLIST.md` (cap 4:00) |
| Friday–Saturday | Devpost draft Friday, submit Saturday. Do not wait until Monday 31 August. |

Public repo. If it is ever made private, grant `testing@devpost.com` and `cloudhackathons@google.com`.
