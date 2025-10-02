FROM python:3.13.2-slim

WORKDIR /opt/timescaledb_connector

RUN pip install aiokafka==0.12.0 psycopg==3.2.9

CMD ["python", "connector.py"]