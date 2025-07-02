import asyncio
import src.tools.agents as agent

async def main():
    while True:
        user_input = await asyncio.to_thread(
            input, "Enter question (or type 'exit' to quit): "
        )
        if user_input.lower() == "exit":
            print("Exiting...")
            break
        response = await agent.invoke_llm(user_input)
        print(response)

asyncio.run(main())