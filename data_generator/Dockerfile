FROM python:3.9.22-alpine3.22

RUN pip install kafka-python==2.2.13

WORKDIR /opt/data_generator

COPY ./kafka_producer.py /opt/data_generator

COPY ./Sailboat.py /opt/data_generator

COPY ./__init__.py /opt/data_generator

ENV PYTHONPATH=/opt

CMD ["python3.9", "-m", "data_generator.kafka_producer", "-S", "6"]