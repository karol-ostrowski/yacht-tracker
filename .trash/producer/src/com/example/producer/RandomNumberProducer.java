package com.example.producer;

import org.apache.kafka.clients.producer.*;
import java.util.Properties;
import java.util.Random;
import java.util.concurrent.ExecutionException;

public class RandomNumberProducer {
    private static final String TOPIC = "random-numbers";
    private static final String BOOTSTRAP_SERVERS = "broker:9092";

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, 
                  "org.apache.kafka.common.serialization.StringSerializer");
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, 
                  "org.apache.kafka.common.serialization.StringSerializer");

        Producer<String, String> producer = new KafkaProducer<>(props);
        Random random = new Random();
        int messageCount = 0;

        try {
            while (true) {
                int randomNumber = random.nextInt(1000);
                String message = "Random number #" + (++messageCount) + ": " + randomNumber;
                
                ProducerRecord<String, String> record = 
                    new ProducerRecord<>(TOPIC, Integer.toString(randomNumber), message);
                
                producer.send(record, (metadata, exception) -> {
                    if (exception != null) {
                        System.err.println("Error sending message: " + exception.getMessage());
                    } else {
                        System.out.println("Sent message: " + message + 
                                          " to partition " + metadata.partition() + 
                                          " with offset " + metadata.offset());
                    }
                });
                
                Thread.sleep(2000); // Wait 2 seconds
            }
        } catch (InterruptedException e) {
            System.out.println("Producer interrupted");
        } finally {
            producer.close();
        }
    }
}