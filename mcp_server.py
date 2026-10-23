"""StudyPilot AI MCP server using Streamable HTTP transport.
Run separately from app.py: python mcp_server.py
Default endpoint: http://127.0.0.1:8001/mcp
"""
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("StudyPilot AI", host="127.0.0.1", port=8001)

@mcp.tool()
def get_study_advice(topic: str, minutes_available: int = 30) -> str:
    """Return a practical short study plan for a topic."""
    minutes = max(5, min(int(minutes_available), 240))
    first = max(5, round(minutes * 0.6))
    second = max(0, minutes - first)
    return (f"Study plan for {topic}: spend about {first} minutes reviewing core concepts, "
            f"then {second} minutes on active recall or practice questions. "
            "Finish by writing down one thing you still find difficult.")

@mcp.tool()
def create_quick_quiz(topic: str, number_of_questions: int = 3) -> str:
    """Create quiz prompts; this demo does not claim verified subject answers."""
    n = max(1, min(int(number_of_questions), 10))
    templates = [
        f"Define the key idea in {topic}.",
        f"Give one example of {topic} and explain it.",
        f"What is a common mistake when learning {topic}?"
    ]
    return "\n".join(f"{i+1}. {templates[i % len(templates)]}" for i in range(n))

@mcp.tool()
def get_study_tip() -> str:
    """Return one evidence-informed general study tip."""
    return "Try active recall: close your notes, explain the idea from memory, then check what you missed."

if __name__ == "__main__":
    print("StudyPilot AI MCP server starting at http://127.0.0.1:8001/mcp")
    print("Transport: Streamable HTTP. Press Ctrl+C to stop.")
    mcp.run(transport="streamable-http")
