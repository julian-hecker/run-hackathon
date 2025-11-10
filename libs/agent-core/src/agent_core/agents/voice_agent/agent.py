from google.adk.agents import Agent

from agent_core.agents.faq_agent.agent import root_agent as faq_agent
from agent_core.agents.menu_agent.agent import root_agent as menu_agent

root_agent = Agent(
    name="voice_agent",
    model="gemini-2.0-flash-exp",
    description="Helps callers place food orders by coordinating between FAQ and Menu Agents",
    instruction="Your name is Aita. Answer questions and order food using the provided sub-agents.",
    sub_agents=[faq_agent, menu_agent],
)
