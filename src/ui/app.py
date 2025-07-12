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
        
def setup_api(AWS_ACCESS_KEY, AWS_SECRET_ACCESS, AWS_REGION, GEMINI_API):
    os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY
    os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS
    os.environ["AWS_REGION"] = AWS_REGION
    os.environ["GEMINI_API_KEY"] = GEMINI_API

    # Validate all keys are set and not empty
    required_keys = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "GEMINI_API_KEY"
    ]

    if all(os.environ.get(key) for key in required_keys):
        return "API setup successful"
    else:
        return "API setup failed"
        
    
async def s3_generative_ai(messages, chatbot):
    # Check if 'files' list is not empty
    try:
        if messages.get('files'):
            file_info = str(messages['text']) + " local_path =" + str(messages['files'][0])
            response = await agent.invoke_llm(str(file_info))
        else:
            if messages.get('text'):
                response = await agent.invoke_llm(messages['text'])
            else:
                response = None
        yield response
    except Exception as e:
         yield {"role": "assistant", "content": f"{e}"}

def create_app():
    with gr.Blocks(theme=gr.themes.Default(), fill_height=True) as GenerativeAI:
        with gr.Sidebar(open=False):
            gr.Markdown("⚙️ Setup AWS Credentials and Gemini API key")
            AWS_ACCESS_KEY = gr.Textbox(label="AWS_ACCESS_KEY_ID", type="password")
            AWS_SECRET_ACCESS = gr.Textbox(label="AWS_SECRET_ACCESS_KEY", type="password")
            AWS_REGION = gr.Textbox(label="AWS_REGION", value="us-east-1")
            GEMINI_API = gr.Textbox(label="GEMINI_API_KEY", type="password")
            
            login_btn = gr.Button("Configure API keys")
            login_status = gr.Textbox(label="Status", interactive=False)
            login_btn.click(
                setup_api,
                inputs=[AWS_ACCESS_KEY, AWS_SECRET_ACCESS, AWS_REGION, GEMINI_API],
                outputs=[login_status]
            )
            

        gr.Markdown("# Agentic-S3: AWS S3 with Generative AI")

        # ── CHAT INTERFACE ───────────────────────────────────────────────────────
        gr.ChatInterface(
            fn=s3_generative_ai,
            type="messages",
            description="Interact with your AWS S3 storage using natural language.\n"
                "Collapse the sidebar for setting up AWS Credentials and Gemini API key",
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