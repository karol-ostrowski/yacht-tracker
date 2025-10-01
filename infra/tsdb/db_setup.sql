CREATE TABLE readings (
    reading_id SERIAL PRIMARY KEY,
    yacht_id INT NOT NULL,
    location POINT NOT NULL,
    timestamp TIMESTAMP PRECISION NOT NULL,
    inst_speed DOUBLE PRECISION NOT NULL,
    time_taken DOUBLE PRECISION NOT NULL
);