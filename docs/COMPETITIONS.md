# Competitions — same desk, swap the runtime

WFAD's job never changes: get there first, hand a human a briefing they can trust, let them take the story.

What **does** change per contest is the **brain model** and the **media backend**. Tools (Watch, Forecast, Alert, Story, render, Disseminate) stay. Doc and Leesa stay front ends.

| Layer | Stays the same | Swaps per contest |
| --- | --- | --- |
| Facts | NWS Watch | Extra sources only if that contest needs them |
| Loop | One `root_agent`, Story as tools | Host (Cloud Run vs other) |
| Brain | ADK agent shape | `WFAD_AGENT_MODEL` (Gemini 3.5 Flash here) |
| Graphics / video / voice | `render_hit_graphic` / `render_hit_clip` | `MEDIA_PROVIDER=stub\|google` (Grok Imagine later) |
| Post | Leesa bundle folder | — |

## This Google / All Things Agentic path

- Repo for judges: `Scrum723/WFAD` (frozen through judging)
- Ops fork: **this repo**
- Brain: Gemini 3.5 Flash + ADK + Cloud Run + Firestore
- Media: `MEDIA_PROVIDER=google` + AI Studio key or Vertex on `wfad-506515`
- **Google One** is the consumer app (Gemini / Flow). It does **not** fund the API. Use the same Google account, then an AI Studio key or Cloud billing.

## A future Google contest

Keep ADK + Cloud Run. Point media at Veo / Omni / Nano Banana. Same Story desk.

## A future xAI / mixed contest

- Keep Watch (NWS) and the Story tools.
- Swap `WFAD_AGENT_MODEL` / the Agent SDK if ADK is not allowed.
- Add `MEDIA_PROVIDER=grok` (Imagine) without changing `draft_story` / Leesa handoff.
- Do not leave Vertex as a required runtime if the rules forbid Google Cloud.

## Both of us in one week

Grok authors and can still make unique stills in this workspace. Google runs the judged agent and, when `MEDIA_PROVIDER=google`, renders clips. Never submit Grok as the contest LLM when the rules require Gemini.

## Env

```bash
WFAD_AGENT_MODEL=gemini-3.5-flash
MEDIA_PROVIDER=stub          # default until a key exists
# MEDIA_PROVIDER=google
# GOOGLE_API_KEY=             # AI Studio, not Google One credits
# GOOGLE_IMAGE_MODEL=gemini-3.1-flash-image
# GOOGLE_VIDEO_MODEL=veo-3.1-fast-generate-preview
```
