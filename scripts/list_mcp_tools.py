# scripts/list_mcp_tools.py
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_COMMAND = "npx"
MCP_ARGS = ["-y", "@executeautomation/database-server", "db/ventas.db"]  # <-- importante

async def main():
    async with AsyncExitStack() as stack:
        params = StdioServerParameters(command=MCP_COMMAND, args=MCP_ARGS)
        read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()

        resp = await session.list_tools()
        print("🔧 Tools disponibles:")
        for tool in resp.tools:
            print("-", tool.name)

if __name__ == "__main__":
    asyncio.run(main())
