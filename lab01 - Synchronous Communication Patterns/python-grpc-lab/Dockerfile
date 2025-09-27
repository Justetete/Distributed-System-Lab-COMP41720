FROM python:3.9-slim

WORKDIR /app

COPY requirement.txt .

RUN pip install -r requirement.txt

COPY . .

EXPOSE 50051

CMD ["python", "server.py"]