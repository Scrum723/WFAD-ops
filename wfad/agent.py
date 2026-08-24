"""ADK root agent. `adk web wfad` and Cloud Run look for root_agent here."""

from google.adk.agents import Agent

from .prompts import ROOT_INSTRUCTION
from .tools.alert import decide_alert
from .tools.disseminate import disseminate_package
from .tools.forecast import write_briefing
from .tools.store import record_run
from .tools.watch import watch_conditions

root_agent = Agent(
    name="wfad",
    model="gemini-3.5-flash",
    description=(
        "Autonomous broadcast-operations agent. An event arrives; WFAD writes a "
        "briefing, decides urgency, and sends the package without a human "
        "driving each step."
    ),
    instruction=ROOT_INSTRUCTION,
    tools=[
        watch_conditions,
        write_briefing,
        decide_alert,
        disseminate_package,
        record_run,
    ],
)
