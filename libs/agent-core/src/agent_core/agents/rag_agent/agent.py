from google.adk.agents import Agent


def rag_tool(query: str) -> str:
    return "This is a test response from the RAG tool."


root_agent = Agent(
    # A unique name for the agent.
    name="rag_agent",
    # The Large Language Model (LLM) that agent will use.
    model="gemini-2.0-flash-exp",  # if this model does not work, try below
    # model="gemini-2.0-flash-live-001",
    # A short description of the agent's purpose.
    description="Agent to answer questions using Retrieval Augmented Generation (RAG).",
    # Instructions to set the agent's behavior.
    instruction="Answer the question using the RAG tool.",
    # Add RAG tool to perform RAG.
    tools=[rag_tool],
)
