import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    server_url = "http://localhost:8000/sse"

    async with sse_client(server_url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 1. List tools
            tools = await session.list_tools()
            print("Available Tools:", [tool.name for tool in tools.tools])

            # 2. Query the menu
            menu_response = await session.call_tool(
                "get_menu",
                arguments={"category": "main", "dietary_tag": "vegetarian"}
            )
            print("\nMenu Results:\n", menu_response.content[0].text)

            # 3. Reserve a table
            booking_response = await session.call_tool(
                "book_table",
                arguments={
                    "customer_name": "Sarah Connor",
                    "customer_phone": "+1-555-894-1122",
                    "party_size": 2,
                    "date": "2026-11-15",
                    "time_slot": "19:30",
                    "special_requests": "Window table preferred"
                }
            )
            print("\nBooking Confirmation:\n", booking_response.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())