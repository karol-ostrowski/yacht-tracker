# Yacht tracker
A real time streaming data processing pipeline written with PyFlink.

![webapp-visualisation](https://github.com/user-attachments/assets/5dfa2faf-08f2-497d-a694-7fb295868460)

## Table of contents
- [User manual](#user-manual)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Simulated data generator](#simulated-data-generator)
- [Streaming data processing](#streaming-data-processing)
- [Infrastructure](#infrastructure)
  - [Kafka](#kafka)
  - [Storage](#storage)
    - [Local storage](#local-storage)
    - [Cloud storage](#cloud-storage)
- [Monitoring](#monitoring)
  - [Grafana dashboard](#grafana-dashboard)
  - [Metrics](#metrics)
  - [Logging](#logging)
- [Custom connectors](#custom-connectors)
  - [TimescaleDB connector](#timescaledb-connector)
  - [Azure Storage Blob connector](#azure-storage-blob-connector)
  - [FastAPI WebSocket](#fastapi-websocket)
- [Web application](#web-application)
- [Testing](#testing)
- [What I've learnt](#what-ive-learnt)

## User manual
Prerequisites:  
- Docker v4.47.0+  
- Azure CLI v2.77.0+  
- Logged in to Azure CLI and having a subscription set.  
- Environmental variables set:  
  - TIMESCALEDB_USER=...  
  - TIMESCALEDB_PASSWORD=...  
  - TIMESCALEDB_NAME=...  
    
How to run:  
Clone the repo and execute the `launch.sh` script.  
To shut down the pipeline execute the `shutdown.sh`. To destroy the Azure resources add the `--destroy` flag. 

## Tech stack
- Python
- PyFlink
- Grafana (dashboard, Loki, Mimir, Alloy)
- Docker
- Bash
- Kafka
- Azure (Blob Storage)
- Terraform
- FastAPI (WebSocket)
- Flask
- GitHub Actions
- TimescaleDB 

## Architecture

<img width="920" height="451" alt="yachttracker-architecture-diagram" src="https://github.com/user-attachments/assets/46bbcd2c-49c6-446f-9dc9-cc674af77464" />


The system was designed as decoupled microservices. Data is created by the data generator simulating ingestion of real time data coming from tracked IoT devices. Events go through Kafka for the first time and are sent to Azure Blob Storage for retention in case of a need for replayability and to a Flink job to be processed. The processed data is again sent to Kafka, which forwards it to a database for storage for future analysis and to a WebSocket. From the WebSocket the processed data is read by a web application that displays the location of the IoT devices on a map as well as the instantaneous speed of each of them.  
<br>
Design choices:
- Flink: Chosen for its stream processing capabilities and growing Python ecosystem (PyFlink), which aligns with the project's need for stateful transformations and real-time processing.
- Grafana dashboard: A go-to technology for visualising time-series metrics. Provides easy way for creating useful dashboards and alerts for when set thresholds are crossed.  
- Grafana Loki: Light log database that integrates well with Grafana dashboards. Easier to set up and use than Elasticsearch.
- Grafana Alloy: Needed for Loki to ingest logs from files. Having a containerized Alloy instance running removes the need for running Prometheus.
- Grafana Mimir: Obvious option for metric storage if already using Grafana solutions. One Grafana Alloy file can configure both Mimir and Loki.
- Kafka: Chosen for its position as the standard for event streaming in distributed systems.
- Azure Blob Storage: Already had experience with this public cloud.
- Terraform: Infrastructure as Code for Azure resource provisioning. Enables version-controlled, reproducible deployments.
- TimescaleDB: Can be queried with SQL queries, optimized for timeseries data. Gives possibility of adding more relations and creating relationships in the future.
- GitHub Actions: A natural choice for a project using GitHub as VCS.

## Simulated data generator

The script generates 6 Sailboat objects that move randomly across a set area. In total the script generates around 10 sensor readings per second. 5% are intentionally delayed to simulate late-arriving data. With each move, a sailboat has a chance to change its speed. A sailboat instantly changes direction of movement to the opposite one when the border of the moving area is reached.

## Streaming data processing

The Flink job, written with PyFlink, is divided into couple of transformations. Late events are filtered out and the on-time events are split into multiple streams, each containing only the events from a single sensor. For each sensor instantenous speed and processing time for an event are calculated. The processed events are sent to Kafka topic for other services to use and some custom metrics are exposed at the metrics endpoint for Mimir to scrape.

<img width="1440" height="900" alt="flink-job-overview" src="https://github.com/user-attachments/assets/21658cd4-6ce0-4b30-82bf-986d3a700e21" />

## Infrastructure

### Kafka
Kafka serves as the heart of the system. It fulfills a job of a middleman between different services allowing for decoupling of parts of the pipeline.

### Storage

#### Local storage

Processed data is stored in a containerized TimescaleDB instance running in Docker.

#### Cloud storage

Azure Blob Storage is used as a storage for raw unprocessed data in case a replay is needed and as a storage for Grafana Loki and Grafana Mimir. The Blob Storage is provisioned with a Terraform script during the execution of the `launch.sh` script and can be destroyed with the `shutdown.sh` script with the `--destroy` flag appended.

## Monitoring

### Grafana dashboard

<img width="1440" height="900" alt="grafana-dashboard" src="https://github.com/user-attachments/assets/b298431c-0152-4ca4-8ad2-e4c53edeb190" />

A Grafana dashboard was created to monitor some crucial metrics in real time. The dashboard shows information about the state of the machine the pipeline is running at as well as the average amount of events flowing in and out of the Flink job and the average time taken for a single event to be processed. The logs are integrated into the dashboard and all error logs can be seen at a glance. Alerting was also set up in case an important metric crosses a threshold value.

### Metrics

Metrics are scraped by Grafana Alloy and stored in Grafana Mimir. Several custom metrics were created in the PyFlink script to provide better information for the monitoring dashboard.

### Logging

Each Python script has logging implemented. Logs are collected from a predefined log directory and from Docker containers output. Grafana Loki, backed by Azure Blob Storage, serves as a log database for the pipeline.

## Custom connectors

### TimescaleDB connector

A simple Kafka to TimescaleDB connector was created to forward the enriched data to a long term storage. The connector sends data in batches and works asynchronously.

### Azure Storage Blob connector

A simple Kafka to Azur Storage Blob connector was created to forward raw data to a long term storage. The connector sends data in batches and works asynchronously.

### FastAPI WebSocket

A WebSocket was created for the web application to ingest data as soon as it becomes available. The WebSocket works asynchronously.

## Web application

As a visualisation layer a simple Flask web application was written. The application displays a map of Zegrze lake with markers on it, each marker being a different sensor. On the left side of the website the instantenous speed of sensors can be seen. A GIF displaying working website can be seen at the top of the README.md file.

## Testing

Functions containing custom logic have tests written for them. The tests are executed automatically during merge to main thanks to GitHub Actions workflows.

## What I've learnt

This project let me go though the entire process of creating a software product. From designing the architecture to writing tests for my scripts. In a natural way it made me realise the importance of planning, management of a project and observability. I had an opportunity to explore technologies and deepen my understanding of each of them, which hopefully will translate to better communication between me and other people I will work with in the future.
