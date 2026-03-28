FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY /app .

USER appuser

ENV PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]