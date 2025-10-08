FROM python:3.9.22-alpine3.22

RUN pip install kafka-python==2.2.13

WORKDIR /opt/data_generator/data_generator

RUN touch /opt/data_generator/__init__.py

COPY ./data_generator/kafka_producer.py /opt/data_generator/data_generator

COPY ./data_generator/sailboat.py /opt/data_generator/data_generator

COPY ./data_generator/__init__.py /opt/data_generator/data_generator

ENV PYTHONPATH=/opt

CMD ["python3.9", "-m", "data_generator.data_generator.kafka_producer", "-S", "6"]