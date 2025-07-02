import asyncio
import src.tools.agents as agent

import asyncio
import src.tools.agents as agent  # Assuming agent handles S3 interactions

async def main():
    print("Welcome to the S3 Assistant. You can ask me about your S3 buckets or objects.")
    
    while True:
        user_input = await asyncio.to_thread(
            input, "Ask me anything about your S3 storage (or type 'exit' to quit): "
        )
        
        if user_input.lower() == "exit":
            print("Exiting... Goodbye!")
            break
        response = await agent.invoke_llm(user_input)
        
        print(response)

asyncio.run(main())
