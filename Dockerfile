FROM ghcr.io/astral-sh/uv:python3.13-alpine
WORKDIR /app
COPY . .
RUN uv sync --locked --no-dev
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"
CMD [".venv/bin/python", "main.py", "--ui"]