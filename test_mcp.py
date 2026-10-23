"""Quick MCP stdio smoke test. Run after installing mcp[cli]."""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["mcp_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [tool.name for tool in tools.tools])
            result = await session.call_tool("get_study_advice", {"topic":"Java inheritance","minutes_available":30})
            print(result.content[0].text if result.content else "No output")

if __name__ == "__main__":
    asyncio.run(main())
