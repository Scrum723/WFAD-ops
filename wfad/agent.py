"""ADK root agent. `adk web wfad` and Cloud Run look for root_agent here."""

from google.adk.agents import Agent

from .prompts import ROOT_INSTRUCTION
from .tools.alert import decide_alert
from .tools.disseminate import disseminate_package
from .tools.forecast import write_briefing
from .tools.store import record_run
from .tools.story import approve_package, draft_story, revise_story
from .tools.watch import watch_conditions

root_agent = Agent(
    name="wfad",
    model="gemini-3.5-flash",
    description=(
        "Autonomous broadcast-operations agent plus Story desk. Watch, Forecast, "
        "Alert, then draft/revise/approve a unique package. Leesa posts. Doc verifies."
    ),
    instruction=ROOT_INSTRUCTION,
    tools=[
        watch_conditions,
        write_briefing,
        decide_alert,
        draft_story,
        revise_story,
        approve_package,
        disseminate_package,
        record_run,
    ],
)
