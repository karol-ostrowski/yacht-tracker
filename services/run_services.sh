#!/bin/bash

docker-compose up -d

echo "Waiting for JobManager to be ready..."
until curl -s http://localhost:8081; do
  sleep 2
done

echo "Submitting PyFlink job..."
docker exec jobmanager flink run -py /opt/flink/flink_job.py