FROM python:3.13.2-slim

WORKDIR /opt/services/kafka_blob_connector

RUN pip install aiokafka==0.12.0 azure-storage-blob==12.26.0 aiohttp==3.13.0

ENV PYTHONPATH=/opt

CMD ["python", "-m", "services.kafka_blob_connector.kafka_blob_connector.connector"]