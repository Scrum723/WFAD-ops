# Stack — three products, one job

Not three WFAD agents. Three **products**. Story desk is an **addition to WFAD**.

```
You
 ├─ Doc     weather front: truth, maps, verify
 ├─ WFAD    middle desk: get there first, briefing, Story desk, handoff
 └─ Leesa   social front: captions, schedule, X / IG / TikTok / YouTube
```

| Product | Repo | Role |
| --- | --- | --- |
| Doc | Live API `weather-agi-production.up.railway.app` | Weather neural net (14 modules). WFAD pulls snapshot products here. |
| **WFAD ops** | **this repo `Scrum723/WFAD-ops`** | Arrive, score, sit with you on the story, emit approved bundle |
| Leesa | `Scrum723/Leesa` / `~/social-media-liaison` | Post the bundle |
| WFAD contest | `Scrum723/WFAD` | Frozen through judging. Do not merge ops here until winners. |

## Story desk (on this agent)

One `root_agent`. Three **tools**, not three agents:

1. `draft_story` — package from Watch / Forecast / Alert
2. `revise_story` — your notes (later: voice-to-text)
3. `approve_package` — writes `~/Desktop/Doc Weather Content/bundles/<slug>/`

Leesa already watches that bundles folder (`insight.md` + `meta.yaml` + optional video).

Graphics/video go through `MEDIA_PROVIDER` (`stub` or `google`). See [`COMPETITIONS.md`](COMPETITIONS.md). Google One is the consumer Gemini/Flow app; WFAD media uses AI Studio or Vertex on the same Google account.
