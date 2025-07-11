import asyncio
import argparse
from src.ui import app
import src.tools.agents as agent

async def main():
    print(
        "Welcome to the S3 Assistant. You can ask me about your S3 buckets or objects."
    )

    while True:
        user_input = await asyncio.to_thread(
            input, "Ask me anything about your S3 storage (or type 'exit' to quit): "
        )

        if user_input.lower() == "exit":
            print("Exiting... Goodbye!")
            break
        response = await agent.invoke_llm(user_input)
        print(response, "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invoke Agentic S3")
    parser.add_argument("--ui", action="store_true", help="Enable ui mode")
    args = parser.parse_args()


    if args.ui:
        gradio_app = app.create_app()
        gradio_app.launch(favicon_path=app.favicon_path)
    else:
        asyncio.run(main())
