# Story desk (first slice)

Human in the loop. Unique IP later (clips, 3–5 min, 3/5/10-day, severe/hurricane/winter). This slice: **hit only**.

## Talk to the agent

```text
Watch Rochester, then draft a story hit.
```

```text
Revise: lead with tonight, drop beach language if none is in Watch.
```

```text
Approve the package for Leesa.
```

## After approve

Folder like:

```
~/Desktop/Doc Weather Content/bundles/2026-08-28-rochester-hit/
  insight.md
  meta.yaml
  CLIP_PROMPT.txt
  story.json
```

No `video.mp4` yet. Clip gen is the next slice. Leesa will not have a video until that file exists; the writing is ready.

## Voice (not wired this slice)

- Voice → text → `revise_story(notes=...)`
- Voice → voice → read `hit.script` back (later)

## Do not

- Auto-approve on a Pub/Sub trigger
- Let Story override Alert severity
- Fetch NWS inside Leesa
- Push these files to `Scrum723/WFAD` contest main
