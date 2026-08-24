"""ADK discovers this package via root_agent in agent.py."""

from . import agent
from .agent import root_agent

__all__ = ["agent", "root_agent"]
