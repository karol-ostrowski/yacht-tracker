mkdir -p build/classes
javac -cp "libs/*" -d build/classes src/com/example/consumer/RandomNumberConsumer.java
docker build -t kafka-consumer .