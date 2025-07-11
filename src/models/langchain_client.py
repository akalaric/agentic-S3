import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
load_dotenv()

class GeminiClient():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            # Create and store the instance
            cls._instance = super(GeminiClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=api_key
            )
            self._initialized = True
        except Exception as e:
            raise e
        
    async def interact(self, query:str, history=None):
        messages = [
            SystemMessage(content=("You are a brilliant scientific assistant who explains concepts clearly and concisely. "))]
        if history:
            for msg in history:
                role = msg.get("role")
                content = msg.get("content")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=query))
        response = await self.llm.ainvoke(messages)
        return response
    
# Test the client
if __name__ == "__main__":
    async def main():
        client = GeminiClient()
        while True:
            user_input = await asyncio.to_thread(input, "Enter question (or type 'exit' to quit): ")
            if user_input.lower() == "exit":
                print("Exiting...")
                break
            response = await client.interact(user_input)
            print(response.content)
    asyncio.run(main())