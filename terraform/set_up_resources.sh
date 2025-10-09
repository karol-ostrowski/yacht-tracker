#!/bin/bash

terraform apply -auto-approve

echo "AZURE_CONNECTION_STRING=$(terraform output raw_data_connection_string)" > .env_raw_data
echo "AZURE_CONTAINER_NAME=$(terraform output raw_data_container_name)" >> .env_raw_data

echo "AZURE_STORAGE_ACCOUNT_NAME=$(terraform output monitoring_storage_account_name)" > .env_loki
echo "AZURE_STORAGE_ACCOUNT_KEY=$(terraform output monitoring_storage_account_key)" >> .env_loki
echo "AZURE_CONTAINER_NAME=$(terraform output loki_container_name)" >> .env_loki

echo "AZURE_STORAGE_ACCOUNT_NAME=$(terraform output monitoring_storage_account_name)" > .env_mimir
echo "AZURE_STORAGE_ACCOUNT_KEY=$(terraform output monitoring_storage_account_key)" >> .env_mimir
echo "AZURE_CONTAINER_NAME=$(terraform output mimir_container_name)" >> .env_mimir