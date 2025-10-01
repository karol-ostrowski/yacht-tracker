FROM python:3.13.2-slim

WORKDIR /opt/timescaledb_connector

RUN pip install kafka-python==2.2.13 psycopg==3.2.9

CMD ["python", "connector.py"]