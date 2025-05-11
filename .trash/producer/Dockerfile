FROM amazoncorretto:21-alpine

WORKDIR /app

# Copy the compiled Java classes and dependencies
COPY ./build/classes/ /app/
COPY ./libs/ /app/libs/

ENTRYPOINT ["java", "-cp", "/app:/app/libs/*", "com.example.producer.RandomNumberProducer"]