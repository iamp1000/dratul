
import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("fastapi-debug-server")

@app.list_tools()
async def list_tools():
    return [
    {
        "name": "get_logs",
        "description": "Get FastAPI server logs",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if _name_ == "_main_":
    asyncio.run(main())

