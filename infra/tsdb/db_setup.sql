CREATE TABLE readings (
    reading_id SERIAL PRIMARY KEY,
    yacht_id INT NOT NULL,
    location TEXT NOT NULL -- fix type, should be GEOMETRY(Point, 4326)
);