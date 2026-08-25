# WFAD — Watch, Forecast, Alert, Disseminate

**Track:** Taskmaster

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
  --set-env-vars="GOOGLE_CLOUD_PROJECT=wfad-506515,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_GENAI_USE_ENTERPRISE=TRUE,FIRESTORE_DATABASE=wfad,FIRESTORE_COLLECTION=wfad_runs"
```

Service URL looks like `https://wfad-agent-xxxxx.us-central1.run.app`.

Wednesday: topic `wfad-triggers` with a push subscription to `https://SERVICE_URL/trigger`, or Cloud Scheduler hitting the same URL. One real email (your inbox or the WHAM list) or one X post — not four platforms.

## What not to do

- Do not deploy the existing Railway apps and call that Google Cloud.
- Do not start Fortified Enterprise pieces until this loop is on Cloud Run.
- Do not spend a day on a Next.js skin.
- Do not rename the project again.

## Schedule

| When | Done when |
| --- | --- |
| Today | Repo, disclosure, `root_agent`, Watch + `record_run`, `adk web`, one Firestore (or local) document |
| Tuesday | Alert + Disseminate on Cloud Run; console screenshots |
| Wednesday | One real outbound; Pub/Sub or Scheduler; four-box diagram |
| Thursday | README + video (shot list in `docs/DEMO_SHOTLIST.md`) |
| Friday–Saturday | Devpost draft Friday, submit Saturday. Do not wait until Monday 31 August. |

Public repo. If it is ever made private, grant `testing@devpost.com` and `cloudhackathons@google.com`.
