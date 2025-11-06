from google.adk.agents import Agent
from google.adk.tools import AgentTool

from agent_core.agents import rag_agent, scheduling_agent

rag_agent_tool = AgentTool(rag_agent)
scheduling_agent_tool = AgentTool(scheduling_agent)

root_agent = Agent(
    name="voice_agent",
    model="gemini-2.0-flash-exp",
    description="I am a voice agent that can answer questions and schedule appointments.",
    instruction="Answer questions and schedule appointments using the provided tools.",
    tools=[rag_agent_tool, scheduling_agent_tool],
)
