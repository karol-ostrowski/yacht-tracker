FROM python:3.9.22-alpine3.22

RUN pip install kafka-python==2.2.13

COPY ./kafka_producer.py /

COPY ./Sailboat.py /

COPY ./__init__.py /

CMD ["python3.9", "kafka_producer.py", "-S", "6"]