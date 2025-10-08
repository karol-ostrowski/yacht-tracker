docker-compose up -d

echo "Waiting for JobManager to be ready..."
until curl -s http://localhost:8081; do
  sleep 2
done

echo "Submitting PyFlink job..."
docker exec -w /opt/flink/services/flink_stream_processor/flink_stream_processor \
  jobmanager flink run -py flink_job.py