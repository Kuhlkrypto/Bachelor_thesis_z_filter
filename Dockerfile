FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# COPY ./evaluation/ /app
COPY ./bin /app/bin

CMD ["python3", "evaluation/main.py"]