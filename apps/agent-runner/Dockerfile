FROM python:3.11-slim

WORKDIR /app

COPY apps/agent-runner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/agent-runner/main.py .
COPY prompts /app/prompts

ENV PROMPTS_DIR=/app/prompts

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
