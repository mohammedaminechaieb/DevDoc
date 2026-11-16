FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --default-timeout=300 --retries 10 --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --default-timeout=300 --retries 10 --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
