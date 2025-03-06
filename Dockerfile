FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# COPY ./evaluation/ /app
COPY ./executables /app/executables
COPY run.sh /app/run.sh

RUN chmod +x /app/run.sh

#CMD ["python3", "evaluation/main.py"]
CMD ["./run.sh"]
