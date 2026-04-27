FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install -U langchain langchain-openai langchain-core fastapi uvicorn pydantic python-dotenv

EXPOSE 8000

CMD ["uvicorn", "10_production.01_fastapi_service:app", "--host", "0.0.0.0", "--port", "8000"]
