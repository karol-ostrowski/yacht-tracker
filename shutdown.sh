#!/bin/bash

DESTROY=false

for arg in "$@"; do
  if [ "$arg" == "--destroy" ]; then
    DESTROY=true
    break
  fi
done

echo "Shutting down visualization layer..."
cd webapp
docker compose down
cd ..

echo "Shutting down data generator..."
cd data_generator
docker compose down
cd ..

echo "Shutting down services..."
cd services
docker compose down
cd ..

echo "Shutting down infrastructure..."
cd infra
docker compose down
cd ..

echo "Shutting monitoring..."
cd monitoring
docker compose down
cd ..

if [ "$DESTROY" = true ]; then
  echo "Destroying cloud resources..."
  cd terraform
  terraform destroy -auto-approve
  cd ..
else
  echo "Leaving cloud resources up."
fi

echo "Shutdown complete."