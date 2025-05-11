mkdir -p build/classes
javac -cp "libs/*" -d build/classes src/com/example/producer/RandomNumberProducer.java
docker build -t kafka-producer .