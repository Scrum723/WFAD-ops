# WFAD desk website

Simple Grok-style chat. **Gemini 3.5 Flash** reads the ask. Tools still own NWS facts.

```bash
cd ~/WFAD-ops
source ~/WFAD/.venv/bin/activate
python -m desk
# http://127.0.0.1:8788
```

| Control | Behavior |
| --- | --- |
| Autopilot on | Watch → Forecast → Alert → draft story + media prompts. Stops. |
| Approve | Writes Leesa bundle. Does not post. |
| Autopilot off | Chat until you ask for a package. |
| LLM | `WFAD_AGENT_MODEL` (Gemini). If Vertex/AI Studio is down, a local parser still drafts. |
| Media | `MEDIA_PROVIDER=stub` or `google` |

Contest `Scrum723/WFAD` is not this site. Do not deploy the desk over the frozen `.run.app` until judging ends.
