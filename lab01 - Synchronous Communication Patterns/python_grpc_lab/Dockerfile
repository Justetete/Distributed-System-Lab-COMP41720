FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p generated && \
    if [ -d "proto" ]; then \
        python -m grpc_tools.protoc \
            -I./proto \
            --python_out=./generated \
            --grpc_python_out=./generated \
            proto/user_service.proto; \
    else \
        python -m grpc_tools.protoc \
            -I. \
            --python_out=./generated \
            --grpc_python_out=./generated \
            user_service.proto; \
    fi

EXPOSE 50051

CMD ["python", "server.py"]