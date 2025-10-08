FROM python:3.13.2-slim

WORKDIR /opt/services/timescaledb_connector

RUN pip install aiokafka==0.12.0 psycopg[binary]==3.2.9

ENV PYTHONPATH=/opt

CMD ["python", "-m", "services.timescaledb_connector.timescaledb_connector.connector"]