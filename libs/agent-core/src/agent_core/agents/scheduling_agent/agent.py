from google.adk.agents import Agent

from .tools import scheduling_tool

root_agent = Agent(
    name="scheduling_agent",
    model="gemini-2.0-flash-exp",
    description="Agent to schedule appointments.",
    instruction="Schedule appointments using the provided tools.",
    tools=[scheduling_tool],
)
