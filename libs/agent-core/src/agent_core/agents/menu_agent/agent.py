from google.adk.agents import Agent
from google.adk.tools import ToolContext, FunctionTool


def add_item_to_order(
    item: str, quantity: int = 1, tool_context: ToolContext | None = None
) -> str:
    """Adds an item to the order state."""
    order = tool_context.state.setdefault("order", [])
    order.append({"item": item, "quantity": quantity})
    tool_context.state["order"] = order
    return f"Added {quantity} '{item}' to the order."


def remove_item_from_order(item: str, tool_context: ToolContext | None = None) -> str:
    """Removes an item from the order state."""
    order = tool_context.state.get("order", [])
    tool_context.state["order"] = [entry for entry in order if entry["item"] != item]
    return f"Removed '{item}' from the order."


MENU_PRICES: dict[str, float] = {
    "Burger": 10.0,
    "Fries": 5.0,
    "Salad": 8.0,
    "Soup": 6.0,
    "Dessert": 4.0,
}


def begin_checkout(tool_context: ToolContext | None = None) -> str:
    """Begins checkout: computes subtotal, updates state, returns an order summary. Payment is handled after checkout at pickup or delivery."""
    order = tool_context.state.get("order", [])
    if not order:
        return "Your order is empty. Add items before starting checkout."

    line_summaries: list[str] = []
    subtotal = 0.0
    for entry in order:
        name = str(entry.get("item", "")).strip()
        qty = int(entry.get("quantity", 1))
        price = float(MENU_PRICES.get(name, 0.0))
        line_total = price * qty
        subtotal += line_total
        line_summaries.append(f"- {name} x{qty} = ${line_total:.2f}")

    order_summary_pretty = "\n".join(line_summaries) + f"\nSubtotal: ${subtotal:.2f}"

    tool_context.state["checkout"] = {
        "started": True,
        "currency": "USD",
        "subtotal": round(subtotal, 2),
        "items": order,
    }
    tool_context.state["order_status"] = "checkout_started"
    tool_context.state["order_summary_pretty"] = order_summary_pretty

    return f"Checkout started.\n{order_summary_pretty}"


menu_prompt = """
You are a helpful assistant that helps with ordering food.
The menu items are as follows:

## Menu Items:
- Burger $10
- Fries $5
- Salad $8
- Soup $6
- Dessert $4

## Current Order:
{order:empty}
"""

add_item_to_order_tool = FunctionTool(add_item_to_order)
remove_item_from_order_tool = FunctionTool(remove_item_from_order)
begin_checkout_tool = FunctionTool(begin_checkout)

root_agent = Agent(
    name="menu_agent",
    model="gemini-2.0-flash-exp",
    description="Agent which helps with ordering food and checkout out.",
    instruction=menu_prompt,
    tools=[add_item_to_order_tool, remove_item_from_order_tool, begin_checkout_tool],
)
