"""Quick check that gpt-6-luna works through Portkey with an MCP tool.

Makes one small agent run and does not change the database.
Run it from the project root: python backend/check_model.py
"""

import asyncio

from pydantic_ai import Agent, NativeOutput
from pydantic_ai.mcp import MCPToolset

import config
from models import AgentReport


async def main() -> None:
    server = MCPToolset(config.MCP_SERVER_PATH)
    agent = Agent(
        config.build_model(),
        instructions="Use your tool to find the shop date, then report it.",
        output_type=NativeOutput(AgentReport),
        toolsets=[server.filtered(lambda ctx, tool: tool.name == "get_shop_date")],
    )
    async with server:
        result = await agent.run("What is today's date for the shop?")

    print(f"Model: {config.MODEL_NAME}")
    print(f"Agent report: {result.output.summary}")
    print(f"Tokens used: {result.usage.total_tokens}")
    print("PASS: Portkey, the model, and the MCP server all worked.")


if __name__ == "__main__":
    asyncio.run(main())
