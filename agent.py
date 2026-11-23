import argparse
import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from groq import AsyncGroq
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client

load_dotenv()


def mcp_tool_to_groq_schema(tool) -> dict:
    schema = getattr(tool, "input_schema", None) or getattr(
        tool, "inputSchema", {}
    )
    if not isinstance(schema, dict):
        schema = {"type": "object", "properties": {}}

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }


def extract_text_from_result(result) -> str:
    texts = []
    if hasattr(result, "content") and result.content:
        for item in result.content:
            if hasattr(item, "text"):
                texts.append(item.text)
            else:
                texts.append(str(item))
    elif hasattr(result, "structured_content") and result.structured_content:
        texts.append(json.dumps(result.structured_content))
    else:
        texts.append(str(result))
    return "\n".join(texts) if texts else "Operation finished with no content."


class GroqMCPAgent:

    def __init__(self, server_urls: list[str], model: str):
        self.server_urls = server_urls
        self.model = model
        self.exit_stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.tools_map: dict[str, tuple[ClientSession, any]] = {}
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant with access to external tools via MCP. "
                    "Use tools whenever required to fetch data or perform operations. "
                    "Do not fabricate answers when tools are available."
                ),
            }
        ]

    async def _connect_single(self, url: str) -> tuple[any, any]:
        if url.rstrip("/").endswith("/sse"):
            streams = await self.exit_stack.enter_async_context(sse_client(url))
        else:
            streams = await self.exit_stack.enter_async_context(
                streamable_http_client(url)
            )
        return streams[0], streams[1]

    async def connect(self):
        print("[*] Connecting to MCP servers...")
        for url in self.server_urls:
            try:
                read_stream, write_stream = await self._connect_single(url)
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()
                self.sessions[url] = session

                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    self.tools_map[tool.name] = (session, tool)
                    print(f"  + Registered tool: {tool.name} (from {url})")

            except Exception as e:
                print(f"[-] Failed to connect to {url}: {e}", file=sys.stderr)

        if not self.sessions:
            raise RuntimeError(
                "Could not establish a connection to any provided MCP server."
            )

        print(
            f"[*] Connected. Total tools available: {len(self.tools_map)}\n"
        )

    async def close(self):
        await self.exit_stack.aclose()

    async def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        tools_schema = [
            mcp_tool_to_groq_schema(tool)
            for _, tool in self.tools_map.values()
        ]

        while True:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=tools_schema if tools_schema else None,
            )

            msg = response.choices[0].message
            assistant_record = {"role": "assistant"}

            if msg.content:
                assistant_record["content"] = msg.content
            if msg.tool_calls:
                assistant_record["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]

            self.messages.append(assistant_record)

            if not msg.tool_calls:
                return msg.content or ""

            for tc in msg.tool_calls:
                func_name = tc.function.name
                call_id = tc.id

                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                print(
                    f"\n[Tool Execution] Calling {func_name} with args: {args}"
                )

                if func_name not in self.tools_map:
                    output = f"Error: Tool '{func_name}' is not recognized."
                else:
                    session, _ = self.tools_map[func_name]
                    try:
                        result = await session.call_tool(
                            func_name, arguments=args
                        )
                        output = extract_text_from_result(result)
                    except Exception as err:
                        output = f"Execution error: {str(err)}"

                print(f"[Tool Result] {output}\n")

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": output,
                    }
                )


async def main():
    parser = argparse.ArgumentParser(description="MCP Universal Client Agent")
    parser.add_argument(
        "--servers",
        nargs="+",
        default=["https://commence-broadside-capitol.ngrok-free.dev/mcp"],
        help="List of MCP server URLs (e.g., http://localhost:8000/mcp)",
    )
    parser.add_argument(
        "--model",
        default="openai/gpt-oss-120b",
        help="Groq model to use",
    )
    args = parser.parse_args()

    agent = GroqMCPAgent(server_urls=args.servers, model=args.model)

    try:
        await agent.connect()
    except Exception as e:
        print(f"Connection aborted: {e}")
        return

    print("Agent ready. Type 'exit' or 'quit' to end.\n" + "=" * 50)

    try:
        while True:
            try:
                user_prompt = input("\nUser: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_prompt:
                continue
            if user_prompt.lower() in ("exit", "quit"):
                break

            reply = await agent.chat(user_prompt)
            print(f"\nAgent: {reply}")
    finally:
        await agent.close()
        print("\nSession closed.")


if __name__ == "__main__":
    asyncio.run(main())