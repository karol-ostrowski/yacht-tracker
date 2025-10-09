#!/bin/bash

echo "Provisioning cloud storage..."
cd terraform
./set_up_resources.sh
cd ..

echo "Setting up infrastructure..."
cd infra
docker compose up -d
cd ..

sleep 10

echo "Setting up monitoring..."
cd monitoring
docker compose up -d
cd ..

echo "Setting up services..."
cd services
./run_services.sh
cd ..

echo "Setting up data generator..."
cd data_generator
docker compose up -d
cd ..

echo "Setting up visualization layer..."
cd webapp
docker compose up -d
cd ..

sleep 2

echo "Set up complete."