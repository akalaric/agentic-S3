import os
import sys
import asyncio
import gradio as gr
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tools.agents as agent
dir_path = os.path.dirname(os.path.realpath(__file__))
favicon_path = os.path.join(dir_path, 'Amazon-S3-Logo.png')

async def stream_response(response):
    partial = ""
    if not hasattr(response, "content") or not isinstance(response.content, str):
        return
    for line in response.content.splitlines():
        partial += line + "\n"
        await asyncio.sleep(0.1)
        yield {"role": "assistant", "content": partial}

async def s3_generative_ai(messages, chatbot):
    # Check if 'files' list is not empty
    if messages.get('files'):
        file_info = str(messages['text']) + " local_path =" + str(messages['files'][0])
        response = await agent.invoke_llm(str(file_info))
    else:
        if messages.get('text'):
            response = await agent.invoke_llm(messages['text'])
        else:
            response = None
    yield response

def create_app():
    with gr.Blocks(fill_height=True) as GenerativeAI:

        gr.Markdown("# Agentic-S3: AWS S3 with Generative AI")

        # ── CHAT INTERFACE ───────────────────────────────────────────────────────
        gr.ChatInterface(
            fn=s3_generative_ai,
            type="messages",
            description="Interact with your AWS S3 storage using natural language.",
            autoscroll=True,
            autofocus=True,
            editable=True,
            stop_btn=True,
            multimodal=True,
        )
        
    return GenerativeAI

if __name__ == "__main__":
    gradio_app = create_app()
    gradio_app.launch(favicon_path=favicon_path)