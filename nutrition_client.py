import os, sys, json, asyncio
from groq import AsyncGroq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "openai/gpt-oss-20b"
SYSTEM = ("You are a Nutrition AI Agent. Always use the available tools for "
          "calorie or protein questions. Values are per 100g. Reply in one short "
          "sentence like: '100g of chicken breast contains approximately 165 calories.'")


async def ask_agent(session, groq_client, groq_tools, question):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    while True:
        resp = await groq_client.chat.completions.create(
            model=MODEL, messages=messages,
            tools=groq_tools, tool_choice="auto", temperature=0.2,
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [{
                "id": tc.id, "type": "function",
                "function": {"name": tc.function.name,
                             "arguments": tc.function.arguments},
            } for tc in msg.tool_calls],
        })

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"AI Agent: Uses the {tc.function.name} MCP tool.", flush=True)
            result = await session.call_tool(tc.function.name, args)
            text = "".join(c.text for c in result.content if c.type == "text")
            print(f"MCP Server: Returns {text}.", flush=True)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": text})


async def main():
    params = StdioServerParameters(command=sys.executable,
                                   args=["-u", "nutrition_server.py"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("MCP Server Connected Successfully!\n", flush=True)

            listed = await asyncio.wait_for(session.list_tools(), timeout=15)
            print("Available Tools:", flush=True)
            for t in listed.tools:
                print(f"  - {t.name}: {t.description}", flush=True)
            print(f"Total Tools: {len(listed.tools)}\n", flush=True)

            groq_tools = [{
                "type": "function",
                "function": {"name": t.name,
                             "description": t.description or "",
                             "parameters": t.inputSchema},
            } for t in listed.tools]

            groq_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

            questions = [
                "How many calories are in 100g of chicken breast?",
                "How much protein is in 100g of egg?",
                "How many calories are in 100g of oats?",
            ]
            for q in questions:
                print("-" * 60, flush=True)
                print("User:", q, flush=True)
                answer = await ask_agent(session, groq_client, groq_tools, q)
                print("AI Agent:", answer, "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
