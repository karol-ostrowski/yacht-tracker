FROM python:3.13.2-slim

WORKDIR /opt/websocket

RUN pip install aiokafka==0.12.0 fastapi==0.118.0 uvicorn==0.37.0 websockets==15.0.1

CMD ["uvicorn", "websocket_server:app", "--host", "0.0.0.0", "--port", "8000"]